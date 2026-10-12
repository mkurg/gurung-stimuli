"""Export one BrainVision microphone channel and markers for Praat."""

import argparse
import configparser
import csv
import json
import re
import sys
import wave
from collections import defaultdict
from pathlib import Path

import numpy as np


def read_brainvision_ini(path):
    data = path.read_bytes()
    probe = data.decode("latin1")
    match = re.search(r"(?im)^\s*Codepage\s*=\s*([^\r\n]+)", probe)
    encoding = match.group(1).strip() if match else "utf-8-sig"
    if encoding.upper() == "ANSI":
        encoding = "cp1252"
    if encoding.upper() == "UTF-8":
        encoding = "utf-8-sig"
    try:
        content = data.decode(encoding)
    except UnicodeDecodeError:
        if match:
            raise
        content = data.decode("cp1252")
    lines = content.splitlines()
    # BrainVision adds an identification line and a free-text Comment section.
    lines = lines[1:]
    for index, line in enumerate(lines):
        if line.strip().lower() == "[comment]":
            lines = lines[:index]
            break
    parser = configparser.ConfigParser(interpolation=None, strict=True)
    parser.optionxform = str
    parser.read_string("\n".join(lines))
    return parser


def linked_file(header_path, filename):
    filename = filename.replace("$b", header_path.stem)
    path = header_path.parent / filename
    if not path.is_file():
        raise ValueError(f"Linked file is missing: {path}")
    return path.resolve()


def read_markers(path, sample_count, channel_count, sample_rate):
    parser = read_brainvision_ini(path)
    if "Marker Infos" not in parser:
        raise ValueError("The marker file has no [Marker Infos] section.")
    markers = []
    for key, value in parser["Marker Infos"].items():
        if not re.fullmatch(r"Mk\d+", key):
            continue
        fields = next(csv.reader([value], quoting=csv.QUOTE_NONE))
        if len(fields) not in (5, 6):
            raise ValueError(f"Unexpected marker fields for {key}: {value}")
        position, size, channel = map(int, fields[2:5])
        if not 1 <= position <= sample_count:
            raise ValueError(f"{key} is outside the recorded sample range.")
        if size < 0 or not 0 <= channel <= channel_count:
            raise ValueError(f"Invalid size or channel for {key}.")
        markers.append({
            "marker_id": key,
            "type": fields[0].replace(r"\1", ","),
            "description": fields[1].replace(r"\1", ","),
            "position_1based": position,
            "size_samples": size,
            "channel": channel,
            "date": fields[5] if len(fields) == 6 else "",
            "onset_seconds": (position - 1) / sample_rate,
            "duration_seconds": size / sample_rate,
        })
    return markers


def quote_textgrid(value):
    return '"' + value.replace('"', '""') + '"'


def marker_code_label(marker):
    match = re.fullmatch(r"([SR])\s*(\d+)", marker["description"].strip())
    return f"{match[1]} {int(match[2])}" if match else ""


def textgrid_text(markers, duration):
    # A point tier requires unique times; retain simultaneous marker labels together.
    grouped = defaultdict(list)
    for marker in markers:
        grouped[marker["position_1based"]].append(marker)
    lines = [
        'File type = "ooTextFile"', 'Object class = "TextGrid"', "",
        "xmin = 0", f"xmax = {duration:.17g}", "tiers? <exists>",
        "size = 3", "item []:",
    ]
    for tier_index, name in enumerate(("triggers", "speech_onset"), 1):
        points = sorted(grouped.items()) if name == "triggers" else []
        lines.extend([
            f"    item [{tier_index}]:", '        class = "TextTier"',
            f"        name = {quote_textgrid(name)}", "        xmin = 0",
            f"        xmax = {duration:.17g}", f"        points: size = {len(points)}",
        ])
        for point_index, (_, at_position) in enumerate(points, 1):
            label = " | ".join(filter(None, (marker_code_label(m) for m in at_position)))
            lines.extend([
                f"        points [{point_index}]:",
                f'            number = {at_position[0]["onset_seconds"]:.17g}',
                f"            mark = {quote_textgrid(label)}",
            ])
    lines.extend([
        "    item [3]:", '        class = "IntervalTier"',
        '        name = "transcription"', "        xmin = 0",
        f"        xmax = {duration:.17g}", "        intervals: size = 1",
        "        intervals [1]:", "            xmin = 0",
        f"            xmax = {duration:.17g}", '            text = ""',
    ])
    return "\n".join(lines) + "\n"


def choose_channel(channel_names, requested):
    print("\nRecorded channels:")
    for index, name in enumerate(channel_names, 1):
        print(f"  {index}: {name}")
    answer = requested or input("\nEnter the MICROPHONE channel number or exact name: ").strip()
    if answer in channel_names:
        return answer
    if answer.isdigit() and 1 <= int(answer) <= len(channel_names):
        return channel_names[int(answer) - 1]
    raise ValueError("The channel was not found. Use a listed number or exact name.")


def signal_peak(raw, block_size):
    peak = 0.0
    for start in range(0, raw.n_times, block_size):
        block = raw.get_data(start=start, stop=min(start + block_size, raw.n_times))[0]
        if not np.isfinite(block).all():
            raise ValueError("The selected channel contains non-finite samples.")
        peak = max(peak, float(np.max(np.abs(block))))
    if peak == 0:
        raise ValueError("The selected channel is entirely zero; check the microphone channel.")
    return peak


def write_wav(path, raw, sample_rate, peak, block_size):
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        for start in range(0, raw.n_times, block_size):
            block = raw.get_data(start=start, stop=min(start + block_size, raw.n_times))[0]
            scaled = np.rint((block / peak) * (0.95 * 32767)).astype("<i2")
            output.writeframesraw(scaled.tobytes())


def export_recording(vhdr, requested_channel=None, output_parent=None):
    try:
        import mne
    except ImportError as error:
        raise ValueError("MNE is missing. Run this script from the installed MNE-Python Prompt.") from error

    vhdr = vhdr.resolve()
    if vhdr.suffix.lower() != ".vhdr" or not vhdr.is_file():
        raise ValueError("Choose an existing .vhdr file.")
    header = read_brainvision_ini(vhdr)
    common = header["Common Infos"]
    if common.get("Averaged", "NO").upper() != "NO" or common.get("SegmentationType", "NOTSEGMENTED").upper() != "NOTSEGMENTED":
        raise ValueError("Use the original continuous, unaveraged BrainVision recording.")
    data_path = linked_file(vhdr, common["DataFile"])
    if not common.get("MarkerFile"):
        raise ValueError("The header does not link a .vmrk file; locate the original marker file first.")
    marker_path = linked_file(vhdr, common["MarkerFile"])
    marker_data_path = linked_file(marker_path, read_brainvision_ini(marker_path)["Common Infos"]["DataFile"])
    if marker_data_path != data_path:
        raise ValueError("The header and marker file refer to different data files.")

    raw = mne.io.read_raw_brainvision(vhdr, preload=False, verbose="ERROR")
    sample_count = int(raw.n_times)
    frequency = float(raw.info["sfreq"])
    sample_rate = round(frequency)
    if sample_rate <= 0 or abs(frequency - sample_rate) > 1e-8:
        raise ValueError(f"Sampling rate {frequency:g} Hz is not an exact integer; WAV cannot store it without a timing change.")
    if sample_count == 0 or sample_count * 2 > 4_000_000_000:
        raise ValueError("This recording is empty or too large for a single ordinary WAV.")
    markers = read_markers(marker_path, sample_count, len(raw.ch_names), frequency)
    channel = choose_channel(raw.ch_names, requested_channel)
    raw.pick([channel])
    duration = sample_count / sample_rate
    block_size = sample_rate * 60
    print(f"\nSelected: {channel}; {sample_rate} Hz; {duration:.3f} seconds")
    print("Reading microphone samples to set a constant playback gain...")
    peak = signal_peak(raw, block_size)

    parent = Path(output_parent).resolve() if output_parent else vhdr.parent / "praat_export"
    parent.mkdir(parents=True, exist_ok=True)
    folder_name = re.sub(r'[^\w.-]+', "_", f"{vhdr.stem}_{channel}").strip("._") or "recording"
    output = parent / folder_name
    suffix = 2
    while output.exists():
        output = parent / f"{folder_name}_{suffix}"
        suffix += 1
    output.mkdir()
    stem = vhdr.stem
    wav_path = output / f"{stem}.wav"
    grid_path = output / f"{stem}.TextGrid"
    table_path = output / f"{stem}_markers.tsv"
    write_wav(wav_path, raw, sample_rate, peak, block_size)
    grid_path.write_text(textgrid_text(markers, duration), encoding="utf-8")
    columns = ["marker_id", "type", "description", "position_1based", "size_samples", "channel", "date", "onset_seconds", "duration_seconds"]
    with table_path.open("w", newline="", encoding="utf-8-sig") as table:
        writer = csv.DictWriter(table, fieldnames=columns, delimiter="\t")
        writer.writeheader()
        writer.writerows(markers)
    metadata = {
        "source_header": str(vhdr), "source_data": str(data_path),
        "source_markers": str(marker_path), "channel": channel,
        "sampling_rate_hz": frequency, "sample_count": sample_count,
        "duration_seconds": duration, "marker_count": len(markers),
        "wav_format": "mono 16-bit PCM", "peak_before_scaling": peak,
        "normalization": "one constant gain; peak set to 95% of 32767",
        "time_origin": "first recorded sample; no cropping, filtering, or resampling",
        "marker_time_formula": "(position_1based - 1) / sampling_rate_hz",
        "textgrid_markers": "all marker onsets retained; compact S/R codes; full marker metadata in TSV",
        "marker_duration_and_channel": "preserved in the TSV, not represented by point-tier duration",
        "mne_version": mne.__version__,
        "numpy_version": np.__version__, "python_version": sys.version,
    }
    (output / f"{stem}_export.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nExport complete: {len(markers)} original markers copied.")
    if not markers:
        print("NOTE: the marker file contains no markers; the triggers tier is empty.")
    print(f"Output folder: {output}")
    print(f"Open these together in Praat:\n  {wav_path}\n  {grid_path}")
    print("Original BrainVision files were read only. Existing exports were not overwritten.")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vhdr", nargs="?", help="Path to the original .vhdr file")
    parser.add_argument("--channel", help="Microphone channel name or listed channel number")
    parser.add_argument("--output-dir", type=Path, help="Parent directory for a new export folder")
    parser.add_argument("--result-json", type=Path, help="Write the new export-folder path for the workflow importer")
    args = parser.parse_args()
    path = args.vhdr or input("Enter the full path to your .vhdr file: ").strip().strip('"')
    output = export_recording(Path(path), args.channel, args.output_dir)
    if args.result_json:
        args.result_json.write_text(json.dumps({"output_folder": str(output)}) + "\n", encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, configparser.Error, EOFError, KeyboardInterrupt) as error:
        print(f"\nStopped: {error}", file=sys.stderr)
        sys.exit(1)
