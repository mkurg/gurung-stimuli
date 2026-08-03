#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import random
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


RANDOM_SEED = 20260606
EXPECTED_IMAGES = [
    "ic_1",
    "coh_1",
    "coh_2",
    "tr_target",
    "it_target",
    "end_coh_it",
    "end_ic_tr",
    "end_ic_it",
]
TRIAL_PATHS = [
    ("tr_coh", "transitive_cohesive", "cohesive", "transitive", ["coh_1", "coh_2", "tr_target"]),
    (
        "it_coh",
        "intransitive_cohesive",
        "cohesive",
        "intransitive",
        ["coh_1", "coh_2", "it_target", "end_coh_it"],
    ),
    ("tr_ic", "transitive_incohesive", "incohesive", "transitive", ["ic_1", "tr_target", "end_ic_tr"]),
    ("it_ic", "intransitive_incohesive", "incohesive", "intransitive", ["ic_1", "it_target", "end_ic_it"]),
]
TRIAL_PATH_BY_ID = {condition_id: trial_path for condition_id, *trial_path in TRIAL_PATHS}
LIST_RULES = {
    "1": {
        "1": ["it_coh", "tr_ic"],
        "2": ["tr_coh", "it_ic"],
        "3": ["tr_coh", "it_ic"],
        "4": ["it_coh", "tr_ic"],
    },
    "2": {
        "1": ["tr_coh", "it_ic"],
        "2": ["it_coh", "tr_ic"],
        "3": ["it_coh", "tr_ic"],
        "4": ["tr_coh", "it_ic"],
    },
}
CONDITION_TRIGGERS = {
    "tr_coh": 1,
    "tr_ic": 2,
    "it_coh": 3,
    "it_ic": 4,
}
MAIN_FIELDS = [
    "trial_id",
    "random_order",
    "experiment_list",
    "dataset_number",
    "dataset_slug",
    "dataset_label",
    "stimulus_set",
    "condition_id",
    "condition_name",
    "cohesion",
    "transitivity",
    "condition_trigger",
    "item_trigger",
    "n_images",
    "img1",
    "img1_role",
    "img2",
    "img2_role",
    "img3",
    "img3_role",
    "img4",
    "img4_role",
    "between_image",
    "audio_probe",
    "between_audio",
    "between_audio_lock_sec",
    "source_dataset_folder",
]
PRACTICE_FIELDS = [
    "trial_id",
    "n_images",
    "img1",
    "img1_role",
    "img2",
    "img2_role",
    "img3",
    "img3_role",
    "img4",
    "img4_role",
    "between_image",
]

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MAIN_STIMULI_MAX_DIMENSION = 900
JPEG_STIMULI_DIRNAME = "JpegStimuliFullRes"
BETWEEN_TRIALS_SOURCE = Path.home() / "Documents" / "Exp pics"
BETWEEN_TRIALS_MAX_DIMENSION = 1920
PRACTICE_STORIES = [
    ("orange_and_man", 3),
    ("girl_towel_and_old_man", 3),
    ("falling_from_bicycle", 3),
    ("drinking_morning_milk", 4),
    ("butterfly", 3),
    ("badminton_and_wind", 3),
    ("buffalo_blocks_the_way", 3),
    ("pieces_of_broken_jug", 4),
    ("leech_after_rain", 3),
    ("slipper_floats_away", 3),
]
PRACTICE_TRIAL_COUNT = len(PRACTICE_STORIES)
PRACTICE_BETWEEN_TRIAL_COUNT = PRACTICE_TRIAL_COUNT - 1
PRACTICE_SPEAKER_SCREEN_AFTER_TRIALS = {2}
PRACTICE_PHOTO_BETWEEN_COUNT = PRACTICE_BETWEEN_TRIAL_COUNT - len(PRACTICE_SPEAKER_SCREEN_AFTER_TRIALS)
PRACTICE_EXTRA_BETWEEN_COUNT = 1
MAIN_BLOCK_SIZE = 40
MAIN_BLOCK_COUNT = 6
MAIN_BREAK_COUNT = MAIN_BLOCK_COUNT - 1
AUDIO_PROBE_FILES = [
    "Audio/new_disc_q_animal.wav",
    "Audio/new_disc_q_how_many.wav",
    "Audio/new_disc_q_what_happened.wav",
    "Audio/new_disc_q_who.wav",
]
AUDIO_PROBE_RATE = 0.10
AUDIO_PROBE_LOCK_SEC = 10
JPEG_SOF_MARKERS = {
    0xC0,
    0xC1,
    0xC2,
    0xC3,
    0xC5,
    0xC6,
    0xC7,
    0xC9,
    0xCA,
    0xCB,
    0xCD,
    0xCE,
    0xCF,
}


def natural_key(value: str) -> list[object]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", value)]


def slugify(value: str) -> str:
    slug = "".join(
        char.lower() if char.isalnum() or char in {"_", "-", "."} else "_"
        for char in value.strip().replace(" ", "_")
    )
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("._") or "item"


def _read_uint(data: bytes, offset: int, size: int, endian: str) -> int:
    return int.from_bytes(data[offset : offset + size], endian)


def parse_exif_orientation(exif_data: bytes) -> int:
    if len(exif_data) < 8:
        return 1
    if exif_data[:2] == b"II":
        endian = "little"
    elif exif_data[:2] == b"MM":
        endian = "big"
    else:
        return 1
    try:
        if _read_uint(exif_data, 2, 2, endian) != 42:
            return 1
        ifd_offset = _read_uint(exif_data, 4, 4, endian)
        if ifd_offset + 2 > len(exif_data):
            return 1
        entry_count = _read_uint(exif_data, ifd_offset, 2, endian)
        base = ifd_offset + 2
        for index in range(entry_count):
            entry = base + (index * 12)
            if entry + 12 > len(exif_data):
                break
            tag = _read_uint(exif_data, entry, 2, endian)
            if tag != 0x0112:
                continue
            value_type = _read_uint(exif_data, entry + 2, 2, endian)
            if value_type == 3:
                return _read_uint(exif_data, entry + 8, 2, endian)
            return _read_uint(exif_data, entry + 8, 4, endian)
    except Exception:
        return 1
    return 1


def read_jpeg_metadata(path: Path) -> tuple[int, int, int]:
    width = 0
    height = 0
    orientation = 1
    with path.open("rb") as handle:
        if handle.read(2) != b"\xff\xd8":
            raise ValueError(f"Not a JPEG file: {path}")
        while True:
            marker_prefix = handle.read(1)
            if not marker_prefix:
                break
            if marker_prefix != b"\xff":
                continue
            marker_byte = handle.read(1)
            while marker_byte == b"\xff":
                marker_byte = handle.read(1)
            if not marker_byte:
                break
            marker = marker_byte[0]
            if marker == 0xD9:
                break
            if marker == 0xDA:
                break
            if marker in {0x01, *range(0xD0, 0xD8)}:
                continue
            raw_length = handle.read(2)
            if len(raw_length) != 2:
                break
            length = int.from_bytes(raw_length, "big")
            data = handle.read(max(0, length - 2))
            if marker == 0xE1 and data.startswith(b"Exif\x00\x00"):
                orientation = parse_exif_orientation(data[6:])
            if marker in JPEG_SOF_MARKERS and len(data) >= 5:
                height = int.from_bytes(data[1:3], "big")
                width = int.from_bytes(data[3:5], "big")
    if width <= 0 or height <= 0:
        raise ValueError(f"Could not read JPEG dimensions: {path}")
    return width, height, orientation


def read_png_metadata(path: Path) -> tuple[int, int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if not header.startswith(b"\x89PNG\r\n\x1a\n") or header[12:16] != b"IHDR":
        raise ValueError(f"Could not read PNG dimensions: {path}")
    return int.from_bytes(header[16:20], "big"), int.from_bytes(header[20:24], "big"), 1


def displayed_image_size(path: Path) -> tuple[int, int]:
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        width, height, orientation = read_jpeg_metadata(path)
    elif suffix == ".png":
        width, height, orientation = read_png_metadata(path)
    else:
        raise ValueError(f"Unsupported image extension: {path}")
    if orientation in {5, 6, 7, 8}:
        width, height = height, width
    return width, height


def parse_dataset_folder(path: Path) -> tuple[int, str] | None:
    match = re.match(r"^(\d+)_(.+)$", path.name)
    if not match:
        return None
    return int(match.group(1)), match.group(2)


def default_source_root() -> Path:
    return (
        Path.home()
        / "Library"
        / "CloudStorage"
        / "GoogleDrive-apazent@gmail.com"
        / ".shortcut-targets-by-id"
        / "1exBA-7XrpLfZc6s8oGNYTbmjGsu5dT6p"
        / "Gurung stimuli"
    )


def scan_dataset_set1(source_root: Path) -> list[dict[str, object]]:
    datasets: list[dict[str, object]] = []
    missing: list[str] = []
    for folder in sorted(source_root.iterdir(), key=lambda path: natural_key(path.name)):
        if not folder.is_dir():
            continue
        parsed = parse_dataset_folder(folder)
        if not parsed:
            continue
        number, label = parsed
        set_folder = folder / "1"
        if not set_folder.is_dir():
            missing.append(str(set_folder))
            continue
        for stem in EXPECTED_IMAGES:
            image = set_folder / f"{stem}.png"
            if not image.is_file():
                missing.append(str(image))
        datasets.append(
            {
                "number": number,
                "label": label,
                "slug": f"{number:03d}_{slugify(label)}",
                "folder": folder,
                "set_folder": set_folder,
            }
        )
    if missing:
        raise FileNotFoundError("Missing expected set-1 stimuli:\n" + "\n".join(missing[:80]))
    if len(datasets) != 30:
        raise ValueError(f"Expected 30 datasets, found {len(datasets)}")
    return datasets


def scan_jpeg_stimuli(jpeg_root: Path) -> list[dict[str, object]]:
    datasets: list[dict[str, object]] = []
    missing: list[str] = []
    if not jpeg_root.is_dir():
        raise FileNotFoundError(f"JPEG stimulus folder not found: {jpeg_root}")
    for folder in sorted(jpeg_root.iterdir(), key=lambda path: natural_key(path.name)):
        if not folder.is_dir():
            continue
        parsed = parse_dataset_folder(folder)
        if not parsed:
            continue
        number, label = parsed
        image_paths: dict[tuple[int, str], str] = {}
        for set_number in range(1, 5):
            set_folder = folder / str(set_number)
            if not set_folder.is_dir():
                missing.append(str(set_folder))
                continue
            for stem in EXPECTED_IMAGES:
                image = set_folder / f"{stem}.jpg"
                if not image.is_file():
                    missing.append(str(image))
                image_paths[(set_number, stem)] = (
                    f"{JPEG_STIMULI_DIRNAME}/{folder.name}/{set_number}/{stem}.jpg"
                )
        datasets.append(
            {
                "number": number,
                "label": label,
                "slug": f"{number:03d}_{slugify(label)}",
                "folder": folder,
                "image_paths": image_paths,
            }
        )
    if missing:
        raise FileNotFoundError("Missing expected JPEG stimuli:\n" + "\n".join(missing[:80]))
    if len(datasets) != 30:
        raise ValueError(f"Expected 30 JPEG stimulus datasets, found {len(datasets)}")
    return datasets


def copy_assets(out_dir: Path, old_dir: Path) -> None:
    audio_dir = out_dir / "Audio"
    stim_dir = out_dir / "Stimuli"
    audio_dir.mkdir(parents=True, exist_ok=True)
    stim_dir.mkdir(parents=True, exist_ok=True)

    old_audio_dir = old_dir / "Audio"
    if old_audio_dir.is_dir():
        for path in sorted(old_audio_dir.iterdir(), key=lambda item: item.name):
            if path.is_file():
                shutil.copy2(path, audio_dir / path.name)
    else:
        print(f"Legacy audio folder not found; keeping existing package audio: {old_audio_dir}")

    for audio_value in AUDIO_PROBE_FILES:
        audio_path = audio_dir / Path(audio_value).name
        if not audio_path.is_file():
            print(f"Warning: audio probe file missing from package: {audio_path}")

    legacy_stimuli = {"arrow.png", "break.png", "finish.png", "sound.png", "sound.jpg"}
    old_stimuli_dir = old_dir / "old_stimuli"
    if old_stimuli_dir.is_dir():
        for path in sorted(old_stimuli_dir.iterdir(), key=lambda item: item.name):
            if path.is_file() and path.name in legacy_stimuli:
                shutil.copy2(path, stim_dir / path.name)
    else:
        print(f"Legacy stimuli folder not found; keeping existing package stimuli: {old_stimuli_dir}")

    probe_source = audio_dir / "new_disc_tsakyali.wav"
    if probe_source.is_file():
        shutil.copy2(probe_source, audio_dir / "probe_placeholder.wav")


def resize_image_with_powershell(source: Path, target: Path, max_dimension: int) -> None:
    script = r'''
Add-Type -AssemblyName System.Drawing
$source = __SOURCE__
$target = __TARGET__
$maxDimension = __MAX_DIMENSION__
$image = [System.Drawing.Image]::FromFile($source)
try {
    $scale = [Math]::Min(1.0, $maxDimension / [double]([Math]::Max($image.Width, $image.Height)))
    $width = [Math]::Max(1, [int][Math]::Round($image.Width * $scale))
    $height = [Math]::Max(1, [int][Math]::Round($image.Height * $scale))
    $bitmap = New-Object System.Drawing.Bitmap($width, $height)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    try {
        $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $graphics.DrawImage($image, 0, 0, $width, $height)
    } finally {
        $graphics.Dispose()
    }
    $lowerTarget = $target.ToLowerInvariant()
    if ($lowerTarget.EndsWith(".jpg") -or $lowerTarget.EndsWith(".jpeg")) {
        $codec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq "image/jpeg" }
        $encoderParams = New-Object System.Drawing.Imaging.EncoderParameters(1)
        $encoderParams.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, [int64]90)
        $bitmap.Save($target, $codec, $encoderParams)
        $encoderParams.Dispose()
    } else {
        $bitmap.Save($target)
    }
    $bitmap.Dispose()
} finally {
    $image.Dispose()
}
'''.replace("__SOURCE__", json.dumps(str(source))).replace("__TARGET__", json.dumps(str(target))).replace(
        "__MAX_DIMENSION__", str(int(max_dimension))
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def copy_or_downsample_image(source: Path, target: Path, max_dimension: int) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_mtime >= source.stat().st_mtime:
        return
    try:
        subprocess.run(
            ["sips", "-Z", str(max_dimension), str(source), "--out", str(target)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        try:
            resize_image_with_powershell(source, target, max_dimension)
        except Exception:
            shutil.copy2(source, target)


def list_landscape_between_sources(source_dir: Path) -> list[Path]:
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Between-trial source folder not found: {source_dir}")
    images: list[Path] = []
    for path in sorted(source_dir.rglob("*"), key=lambda item: natural_key(str(item.relative_to(source_dir)))):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        try:
            width, height = displayed_image_size(path)
        except Exception as err:
            print(f"Skipping unreadable between-trial image {path}: {err}")
            continue
        if width > height:
            images.append(path)
    return images


def prepare_between_images(out_dir: Path, required_count: int) -> list[str]:
    between_dir = out_dir / "BetweenTrials"
    candidates = list_landscape_between_sources(BETWEEN_TRIALS_SOURCE)
    if len(candidates) < required_count:
        raise ValueError(
            f"Need {required_count} unique landscape between-trial images, "
            f"but found {len(candidates)} in {BETWEEN_TRIALS_SOURCE}"
        )
    if between_dir.exists():
        shutil.rmtree(between_dir)
    between_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(RANDOM_SEED + 2)
    rng.shuffle(candidates)
    selected = candidates[:required_count]
    images: list[str] = []
    for index, source in enumerate(selected, start=1):
        target = between_dir / f"nepal_2025_{index:03d}_{slugify(source.stem)}{source.suffix.lower()}"
        copy_or_downsample_image(source, target, BETWEEN_TRIALS_MAX_DIMENSION)
        images.append(f"BetweenTrials/{target.name}")
    return images


def build_main_rows(
    datasets: list[dict[str, object]],
    list_id: str,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if list_id not in LIST_RULES:
        raise ValueError(f"Unknown experimental list: {list_id}")
    for dataset in datasets:
        number = int(dataset["number"])
        label = str(dataset["label"])
        image_paths = dataset["image_paths"]
        for set_number in range(1, 5):
            set_key = str(set_number)
            for condition_id in LIST_RULES[list_id][set_key]:
                condition_name, cohesion, transitivity, steps = TRIAL_PATH_BY_ID[condition_id]
                item_trigger = ((number - 1) * 4) + set_number
                row = {
                    "trial_id": f"d{number:03d}_set{set_number}_{condition_id}_list{list_id}",
                    "random_order": "",
                    "experiment_list": list_id,
                    "dataset_number": str(number),
                    "dataset_slug": str(dataset["slug"]),
                    "dataset_label": label.replace(" ", "_"),
                    "stimulus_set": str(set_number),
                    "condition_id": condition_id,
                    "condition_name": condition_name,
                    "cohesion": cohesion,
                    "transitivity": transitivity,
                    "condition_trigger": str(CONDITION_TRIGGERS[condition_id]),
                    "item_trigger": str(item_trigger),
                    "n_images": str(len(steps)),
                    "between_image": "",
                    "audio_probe": "0",
                    "between_audio": "",
                    "between_audio_lock_sec": "0",
                    "source_dataset_folder": f"{JPEG_STIMULI_DIRNAME}/{dataset['folder'].name}",
                }
                for index in range(1, 5):
                    row[f"img{index}"] = ""
                    row[f"img{index}_role"] = ""
                for index, stem in enumerate(steps, start=1):
                    row[f"img{index}"] = image_paths[(set_number, stem)]
                    row[f"img{index}_role"] = stem
                rows.append(row)

    for index, row in enumerate(rows, start=1):
        row["random_order"] = str(index)
        row["between_image"] = ""
    return rows


def build_practice_rows(between_images: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index, (story_slug, image_count) in enumerate(PRACTICE_STORIES, start=1):
        row = {
            "trial_id": f"practice_{index:02d}",
            "n_images": str(image_count),
            "between_image": "",
        }
        for image_index in range(1, 5):
            if image_index <= image_count:
                row[f"img{image_index}"] = (
                    f"Stimuli/practice_{index:02d}_pic{image_index:02d}_{story_slug}.jpg"
                )
                row[f"img{image_index}_role"] = f"practice_{image_index}"
            else:
                row[f"img{image_index}"] = ""
                row[f"img{image_index}_role"] = ""
        rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


SHARED_CODE = r'''
from pathlib import Path
import atexit
import csv
import gc
import queue
import random as _gurung_random
import threading

try:
    from psychopy.hardware.speaker import SpeakerDevice
except Exception as _gurung_speaker_import_error:
    SpeakerDevice = None
    print("SpeakerDevice import failed:", _gurung_speaker_import_error)

try:
    import numpy as _gurung_np
    import sounddevice as _gurung_sd
    import soundfile as _gurung_sf
    G_RECORDING_AVAILABLE = True
except Exception as _gurung_recording_error:
    G_RECORDING_AVAILABLE = False
    print("Audio recording is unavailable:", _gurung_recording_error)

try:
    import serial as _gurung_serial
except Exception as _gurung_serial_error:
    _gurung_serial = None
    print("Serial trigger backend is unavailable:", _gurung_serial_error)

try:
    from PIL import Image as _gurung_Image
    from PIL import ImageOps as _gurung_ImageOps
except Exception as _gurung_image_import_error:
    _gurung_Image = None
    _gurung_ImageOps = None
    print("Image metadata reading is unavailable:", _gurung_image_import_error)

G_ROOT = Path(_thisDir)
G_DATA_DIR = G_ROOT / "data"
G_RECORDINGS_ROOT = G_ROOT / "recordings"
G_RECORDINGS_DIR = None
G_DEBUG_LOG = G_ROOT / "debug_gurung_runtime.log"
G_DATA_DIR.mkdir(exist_ok=True)
G_RECORDINGS_ROOT.mkdir(exist_ok=True)
G_IMAGE_ASPECT = 2.0 / 3.0
G_SEQUENCE_SIDE_STEPS = 2
G_SEQUENCE_X_MARGIN = 0.02
G_SEQUENCE_Y_MARGIN = 0.05
G_SEQUENCE_GAP_RATIO = 0.12
G_SEQUENCE_SIZE_COUNT = 5
G_SEQUENCE_JITTER_SLOTS = (
    (-0.30, -0.018),
    (-0.22, 0.018),
    (-0.18, -0.018),
    (-0.06, 0.018),
    (0.06, -0.018),
    (0.18, 0.018),
    (0.22, -0.018),
    (0.30, 0.018),
)
G_SEQUENCE_JITTER_STATE = {"bag": []}
G_ARROW_MAX_SIZE = 0.045
G_MAIN_TRIAL_INDEX = 0
G_PRACTICE_TRIAL_INDEX = 0
G_SPEAKER = None
G_FULLSCREEN_CACHE = {"stim": None}
G_BETWEEN_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}
G_BETWEEN_STATE = {"images": [], "index": 0}
G_MAIN_RUNTIME_STATE = {"prepared": False, "files": []}
G_TRIGGER_STATE = {
    "serial": None,
    "log_path": None,
    "header_written": False,
    "pulse_ms": 5.0,
    "port": "",
    "serial_status": "not_initialized",
    "trigger_index": 0,
}
G_AUDIO_PROBE_FILES = (
    "Audio/new_disc_q_animal.wav",
    "Audio/new_disc_q_how_many.wav",
    "Audio/new_disc_q_what_happened.wav",
    "Audio/new_disc_q_who.wav",
)
G_AUDIO_PROBE_RATE = 0.10
G_AUDIO_PROBE_LOCK_SEC = 10
G_AUDIO_SPEAKER_IMAGE = "Stimuli/sound.png"
G_AUDIO_SPEAKER_SIZE = (0.22, 0.22)
G_RECORDING_STOP_GRACE_SEC = 0.5
G_LISTENER_RESPONSE_MIN_SEC = 10.0
G_LISTENER_RESPONSE_DIRNAME = "listener responses"
G_MAIN_BLOCK_SIZE = 40
G_MAIN_BLOCK_COUNT = 6
G_PRACTICE_TRIAL_COUNT = 10
G_PRACTICE_PICTURE_AUDIO = {
    1: {
        0: "Audio/new_disc_orange_1.wav",
        1: "Audio/new_disc_orange_2.wav",
        2: "Audio/new_disc_orange_3.wav",
    },
    2: {
        0: "Audio/new_disc_towel_1.wav",
        1: "Audio/new_disc_towel_2.wav",
        2: "Audio/new_disc_towel_3.wav",
    },
}
G_PRACTICE_AFTER_TRIAL_AUDIO = {
    2: "Audio/new_disc_instr2.wav",
    4: "Audio/new_disc_q_what_happened.wav",
    7: "Audio/new_disc_q_who.wav",
    10: "Audio/new_disc_q_how_many.wav",
}
G_PRACTICE_SPEAKER_SCREEN_AFTER_TRIALS = {2}
G_LAST_MAIN_TRIAL_INFO = {}


def g_log(message):
    text = f"{core.getTime():.3f} {message}"
    print(text)
    try:
        with G_DEBUG_LOG.open("a", encoding="utf-8") as handle:
            handle.write(text + "\n")
    except Exception:
        pass

def g_is_blank(value):
    if value is None:
        return True
    text = str(value).strip()
    return text == "" or text.lower() in {"none", "nan", "null"}


def g_text(value):
    if g_is_blank(value):
        return ""
    return str(value).strip()


def g_float(value, default=0.0):
    if g_is_blank(value):
        return default
    try:
        return float(value)
    except Exception:
        return default


def g_key_names(keys):
    names = []
    for key in keys:
        try:
            names.append(key[0])
        except Exception:
            names.append(key)
    return names


def g_key_time(keys, key_name, default=None):
    if default is None:
        default = core.getTime()
    for key in keys:
        try:
            if key[0] == key_name:
                return g_float(key[-1], default)
        except Exception:
            if key == key_name:
                return default
    return default


def g_practice_picture_audio(trial_index, segment_index):
    trial_audio = G_PRACTICE_PICTURE_AUDIO.get(trial_index, {})
    return trial_audio.get(segment_index, "")


def g_practice_pre_picture_audio(trial_index, segment_index, image_count):
    if trial_index not in G_PRACTICE_PICTURE_AUDIO and segment_index == image_count - 1:
        return "Audio/new_disc_tsakyali.wav"
    return ""


def g_int(value, default=0):
    if g_is_blank(value):
        return default
    try:
        return int(float(value))
    except Exception:
        return default


def g_bool(value, default=False):
    if g_is_blank(value):
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return default


def g_selected_list():
    value = g_text(expInfo.get("list", "1")).lower().replace("list", "").strip()
    if value not in {"1", "2"}:
        g_log(f"invalid_experiment_list {value!r}; using list 1")
        value = "1"
    expInfo["list"] = value
    return value


def g_path(value):
    value = g_text(value)
    if not value:
        return ""
    path = Path(value)
    if path.is_absolute():
        return str(path)
    return str(G_ROOT / path)


def g_window_aspect(win):
    try:
        return max(float(win.size[0]) / float(win.size[1]), 1.0)
    except Exception:
        return 1.5


def g_image_aspect(path):
    if _gurung_Image is None:
        return None
    try:
        with _gurung_Image.open(path) as image:
            if _gurung_ImageOps is not None:
                image = _gurung_ImageOps.exif_transpose(image)
            width, height = image.size
        if width > 0 and height > 0:
            return float(width) / float(height)
    except Exception as err:
        g_log(f"image_aspect_warning {path}: {err}")
    return None


def g_fullscreen_size(win, image_path):
    screen_aspect = g_window_aspect(win)
    image_aspect = g_image_aspect(image_path)
    if not image_aspect:
        return (screen_aspect, 1.0)
    if image_aspect >= screen_aspect:
        return (screen_aspect, screen_aspect / image_aspect)
    return (image_aspect, 1.0)


def g_fullscreen_image(win, image_value):
    path = g_path(image_value)
    old_stim = G_FULLSCREEN_CACHE.get("stim")
    if old_stim is not None:
        try:
            old_stim.clearTextures()
        except Exception:
            pass
    g_log(f"load_fullscreen_image {path}")
    stim = visual.ImageStim(
        win,
        image=path,
        pos=(0, 0),
        size=g_fullscreen_size(win, path),
        interpolate=True,
    )
    G_FULLSCREEN_CACHE["stim"] = stim
    return stim


def g_audio_speaker_image(win):
    return visual.ImageStim(
        win,
        image=g_path(G_AUDIO_SPEAKER_IMAGE),
        pos=(0, 0),
        size=G_AUDIO_SPEAKER_SIZE,
        interpolate=True,
    )


def g_release_fullscreen_image(stim):
    g_release_stims([stim])
    if G_FULLSCREEN_CACHE.get("stim") is stim:
        G_FULLSCREEN_CACHE["stim"] = None


def g_init_between_images():
    between_dir = G_ROOT / "BetweenTrials"
    images = []
    try:
        for path in sorted(between_dir.iterdir()):
            if path.is_file() and path.suffix.lower() in G_BETWEEN_IMAGE_EXTS:
                image_value = f"BetweenTrials/{path.name}"
                images.append(image_value)
    except Exception as err:
        raise RuntimeError(f"Could not list between-trial images in {between_dir}: {err}")
    if not images:
        raise RuntimeError(f"No between-trial images found in {between_dir}")
    _gurung_random.shuffle(images)
    G_BETWEEN_STATE["images"] = images
    G_BETWEEN_STATE["index"] = 0
    g_log(f"runtime_between_images_shuffled count={len(images)}")


def g_next_between_image():
    images = G_BETWEEN_STATE.get("images") or []
    index = int(G_BETWEEN_STATE.get("index") or 0)
    if index >= len(images):
        raise RuntimeError(f"No unused between-trial images remain: used {index}, available {len(images)}")
    image_value = images[index]
    G_BETWEEN_STATE["index"] = index + 1
    g_log(f"runtime_between_image {index + 1}/{len(images)} {image_value}")
    return image_value


def g_prepare_runtime_main_blocks():
    if G_MAIN_RUNTIME_STATE.get("prepared"):
        return
    list_id = g_selected_list()
    conditions_path = f"Conds/main_list{list_id}_all_240.csv"
    rows = list(data.importConditions(conditions_path))
    if not rows:
        raise RuntimeError(f"No main trials found in {conditions_path}")
    if len(rows) != G_MAIN_BLOCK_SIZE * G_MAIN_BLOCK_COUNT:
        raise RuntimeError(
            f"Expected {G_MAIN_BLOCK_SIZE * G_MAIN_BLOCK_COUNT} main trials in {conditions_path}, found {len(rows)}"
        )
    _gurung_random.shuffle(rows)
    g_assign_runtime_audio_probes(rows)
    fieldnames = list(rows[0].keys())
    block_files = []
    block_sizes = []
    for block_index in range(G_MAIN_BLOCK_COUNT):
        block_rows = rows[
            block_index * G_MAIN_BLOCK_SIZE : (block_index + 1) * G_MAIN_BLOCK_SIZE
        ]
        block_sizes.append(len(block_rows))
        block_path = G_DATA_DIR / f"runtime_main_block{block_index + 1}.csv"
        with block_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
            writer.writeheader()
            for row in block_rows:
                writer.writerow({field: "" if g_is_blank(row.get(field, "")) else row.get(field, "") for field in fieldnames})
        block_files.append(str(block_path))
    G_MAIN_RUNTIME_STATE["files"] = block_files
    G_MAIN_RUNTIME_STATE["prepared"] = True
    g_log(f"runtime_main_sequences_shuffled list={list_id} count={len(rows)} block_sizes={block_sizes}")


def g_assign_runtime_audio_probes(rows):
    for row in rows:
        row["audio_probe"] = "0"
        row["between_audio"] = ""
        row["between_audio_lock_sec"] = "0"
    probe_count = int(round(len(rows) * G_AUDIO_PROBE_RATE))
    if probe_count <= 0:
        return
    if probe_count % len(G_AUDIO_PROBE_FILES):
        raise RuntimeError(
            f"Audio probe count {probe_count} cannot be split equally across {len(G_AUDIO_PROBE_FILES)} files"
        )
    block_start_indices = set(range(0, len(rows), G_MAIN_BLOCK_SIZE))
    candidate_indices = [index for index in range(len(rows)) if index not in block_start_indices]
    if probe_count > len(candidate_indices):
        raise RuntimeError(f"Need {probe_count} audio probe slots, only {len(candidate_indices)} are available")
    for audio_value in G_AUDIO_PROBE_FILES:
        audio_path = Path(g_path(audio_value))
        if not audio_path.is_file():
            raise RuntimeError(f"Missing audio probe file: {audio_path}")
    per_audio_count = probe_count // len(G_AUDIO_PROBE_FILES)
    audio_bag = []
    for audio_value in G_AUDIO_PROBE_FILES:
        audio_bag.extend([audio_value] * per_audio_count)
    _gurung_random.shuffle(audio_bag)
    probe_indices = _gurung_random.sample(candidate_indices, probe_count)
    for row_index, audio_value in zip(probe_indices, audio_bag):
        rows[row_index]["audio_probe"] = "1"
        rows[row_index]["between_audio"] = audio_value
        rows[row_index]["between_audio_lock_sec"] = str(G_AUDIO_PROBE_LOCK_SEC)
    counts = {audio_value: audio_bag.count(audio_value) for audio_value in G_AUDIO_PROBE_FILES}
    g_log(f"runtime_main_audio_probes count={probe_count} counts={counts} block_start_audio=0")


def g_runtime_main_block_file(block_index):
    if not G_MAIN_RUNTIME_STATE.get("prepared"):
        g_prepare_runtime_main_blocks()
    files = G_MAIN_RUNTIME_STATE.get("files") or []
    index = int(block_index) - 1
    if index < 0 or index >= len(files):
        raise RuntimeError(f"Invalid main block index: {block_index}")
    return files[index]


def g_choose_speaker():
    g_log("Using PsychoPy default speaker device.")
    return None


G_SPEAKER = g_choose_speaker()
g_init_between_images()
g_prepare_runtime_main_blocks()


def g_safe(value):
    text = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in str(value))
    while "__" in text:
        text = text.replace("__", "_")
    return text.strip("._") or "item"


def g_participant_tag():
    return g_safe(expInfo.get("participant", "participant"))


def g_list_tag():
    return f"l{g_selected_list()}"


def g_transitivity_tag(value):
    text = g_text(value).lower()
    if text.startswith("tr") or text == "transitive":
        return "tr"
    if text.startswith("it") or text.startswith("itr") or text == "intransitive":
        return "it"
    return g_safe(text or "unknown")


def g_practice_stem(trial_index, picture_index):
    return f"{g_participant_tag()}_practice_{int(trial_index):02d}_pic{int(picture_index):02d}"


def g_discourse_main_stem(trial_index, dataset_number, condition_id, picture_index, role):
    return (
        f"{g_participant_tag()}_main_{g_list_tag()}_trial{int(trial_index):03d}_"
        f"imageset{int(dataset_number):02d}_cond_{g_safe(condition_id)}_"
        f"pic{int(picture_index):02d}_{g_safe(role)}"
    )


def g_session_recordings_dir():
    participant = g_participant_tag()
    list_tag = g_list_tag()
    date_value = g_safe(expInfo.get("date") or expInfo.get("date|hid") or data.getDateStr())
    folder = G_RECORDINGS_ROOT / f"{participant}_{list_tag}_{date_value}"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / G_LISTENER_RESPONSE_DIRNAME).mkdir(parents=True, exist_ok=True)
    expInfo["recordings_dir"] = str(folder)
    g_log(f"recordings_dir {folder}")
    return folder


def g_question_filename_tag(question_audio):
    value = g_text(question_audio)
    if not value:
        return "unknown_question"
    try:
        name = Path(value.replace("\\", "/")).name
        stem = Path(name).stem or name
    except Exception:
        stem = value
    for prefix in ("new_disc_q_", "disc_q_", "q_"):
        if stem.startswith(prefix):
            stem = stem[len(prefix):]
            break
    return g_safe(stem or "unknown_question")


def g_listener_practice_stem(trial_index, question_audio=""):
    participant = g_participant_tag()
    question_tag = g_question_filename_tag(question_audio)
    return f"{participant}_listener_practice_trial{int(trial_index):02d}_{question_tag}"


def g_listener_main_stem(trial_info, question_audio=""):
    participant = g_participant_tag()
    trial_index = g_int((trial_info or {}).get("trial_index", 0), 0)
    dataset_number = g_int((trial_info or {}).get("dataset_number", 0), 0)
    condition_id = g_safe(g_text((trial_info or {}).get("condition_id", "unknown_condition")))
    question_tag = g_question_filename_tag(question_audio)
    return (
        f"{participant}_listener_main_{g_list_tag()}_trial{trial_index:03d}_"
        f"imageset{dataset_number:02d}_cond_{condition_id}_{question_tag}"
    )


def g_roles_and_paths():
    roles = []
    paths = []
    for idx in range(1, 5):
        image_value = globals().get(f"img{idx}", "")
        role_value = globals().get(f"img{idx}_role", f"img{idx}")
        if not g_is_blank(image_value):
            paths.append(g_path(image_value))
            roles.append(g_text(role_value) or f"img{idx}")
    return roles, paths


def g_target_index(roles):
    for target_role in ("tr_target", "it_target"):
        if target_role in roles:
            return roles.index(target_role)
    return (len(roles) - 1) / 2


def g_next_sequence_jitter():
    bag = G_SEQUENCE_JITTER_STATE.get("bag")
    if not bag:
        bag = list(G_SEQUENCE_JITTER_SLOTS)
        _gurung_random.shuffle(bag)
        G_SEQUENCE_JITTER_STATE["bag"] = bag
    return bag.pop()


def g_sequence_layout(win, roles):
    sequence_count = max(1, len(roles))
    size_count = max(G_SEQUENCE_SIZE_COUNT, sequence_count)
    jitter_x_width_max = max(abs(pos[0]) for pos in G_SEQUENCE_JITTER_SLOTS)
    jitter_y_max = max(abs(pos[1]) for pos in G_SEQUENCE_JITTER_SLOTS)
    horizontal_room = max(0.1, g_window_aspect(win) - (2 * G_SEQUENCE_X_MARGIN))
    vertical_room = max(0.1, 1.0 - (2 * (G_SEQUENCE_Y_MARGIN + jitter_y_max)))
    width_from_horizontal = horizontal_room / (
        size_count
        + ((size_count - 1) * G_SEQUENCE_GAP_RATIO)
        + (2 * jitter_x_width_max)
    )
    image_height = min(vertical_room, width_from_horizontal / G_IMAGE_ASPECT)
    image_width = image_height * G_IMAGE_ASPECT
    gap = image_width * G_SEQUENCE_GAP_RATIO
    step = image_width + gap
    row_center = (len(roles) - 1) / 2.0
    jitter_x_factor, jitter_y = g_next_sequence_jitter()
    jitter_x = jitter_x_factor * image_width
    positions = [((idx - row_center) * step + jitter_x, jitter_y) for idx in range(len(roles))]
    arrow_size = min(G_ARROW_MAX_SIZE, max(0.02, gap * 0.9))
    return (image_width, image_height), positions, (arrow_size, arrow_size), (jitter_x, jitter_y)


def g_make_sequence(win, roles, paths):
    image_size, positions, arrow_size, jitter = g_sequence_layout(win, roles)
    g_log(f"make_sequence roles={roles} jitter={jitter} paths={paths}")
    images = []
    for path, pos in zip(paths, positions):
        images.append(visual.ImageStim(win, image=path, pos=pos, size=image_size, interpolate=True))
    arrows = []
    for left, right in zip(positions, positions[1:]):
        arrows.append(g_make_arrow(win, ((left[0] + right[0]) / 2, (left[1] + right[1]) / 2), arrow_size))
    return images, arrows


def g_make_arrow(win, pos, size):
    arrow_width = float(size[0])
    arrow_height = float(size[1])
    shaft_half_height = arrow_height * 0.16
    head_back_x = arrow_width * 0.08
    left_x = -arrow_width / 2.0
    right_x = arrow_width / 2.0
    arrow_color = (-0.25, -0.25, -0.25)
    vertices = [
        (left_x, -shaft_half_height),
        (head_back_x, -shaft_half_height),
        (head_back_x, -arrow_height / 2.0),
        (right_x, 0),
        (head_back_x, arrow_height / 2.0),
        (head_back_x, shaft_half_height),
        (left_x, shaft_half_height),
    ]
    return visual.ShapeStim(
        win,
        vertices=vertices,
        pos=pos,
        fillColor=arrow_color,
        lineColor=arrow_color,
        closeShape=True,
    )


def g_release_stims(*groups):
    for group in groups:
        if not group:
            continue
        for stim in group:
            try:
                clear_textures = getattr(stim, "clearTextures", None)
                if clear_textures is not None:
                    clear_textures()
            except Exception as err:
                g_log(f"stim_release_warning {err}")
    gc.collect()


def g_draw_sequence(images, arrows, reveal_count):
    win.color = "white"
    for idx in range(reveal_count):
        images[idx].draw()
    for idx in range(max(0, reveal_count - 1)):
        arrows[idx].draw()


def g_play_audio(path_value):
    path = g_path(path_value)
    if not path:
        return None
    g_log(f"play_audio {path}")
    audio = sound.Sound(path)
    audio.play()
    return audio


def g_init_trigger_log(recordings_dir):
    log_path = Path(recordings_dir) / "eeg_triggers.csv"
    G_TRIGGER_STATE["log_path"] = log_path
    G_TRIGGER_STATE["header_written"] = False
    g_write_trigger_log_header()
    g_init_serial_trigger()


def g_write_trigger_log_header():
    log_path = G_TRIGGER_STATE.get("log_path")
    if not log_path or G_TRIGGER_STATE.get("header_written"):
        return
    try:
        with Path(log_path).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "trigger_index",
                    "core_time",
                    "trigger_code",
                    "label",
                    "send_mode",
                    "serial_port",
                    "serial_status",
                    "serial_sent",
                    "pulse_ms",
                    "details",
                ],
                lineterminator="\n",
            )
            writer.writeheader()
        G_TRIGGER_STATE["header_written"] = True
    except Exception as err:
        g_log(f"trigger_log_header_failed {err}")


def g_init_serial_trigger():
    port = g_text(expInfo.get("eeg_port", ""))
    pulse_ms = g_float(expInfo.get("trigger_pulse_ms", 5), 5.0)
    G_TRIGGER_STATE["pulse_ms"] = max(0.0, pulse_ms)
    G_TRIGGER_STATE["port"] = port
    G_TRIGGER_STATE["trigger_index"] = 0
    if not port:
        G_TRIGGER_STATE["serial_status"] = "disabled_blank_port"
        g_log("trigger_serial_disabled blank_eeg_port")
        return
    if _gurung_serial is None:
        G_TRIGGER_STATE["serial_status"] = "unavailable_missing_pyserial"
        g_log("trigger_serial_unavailable missing_pyserial")
        return
    try:
        serial_port = _gurung_serial.Serial(port=port, baudrate=115200, timeout=0)
        G_TRIGGER_STATE["serial"] = serial_port
        G_TRIGGER_STATE["serial_status"] = "open"
        g_log(f"trigger_serial_opened port={port} pulse_ms={G_TRIGGER_STATE['pulse_ms']}")
    except Exception as err:
        G_TRIGGER_STATE["serial"] = None
        G_TRIGGER_STATE["serial_status"] = "open_failed"
        g_log(f"trigger_serial_open_failed port={port} err={err}")


def g_close_serial_trigger():
    serial_port = G_TRIGGER_STATE.get("serial")
    G_TRIGGER_STATE["serial"] = None
    if serial_port is None:
        return
    try:
        serial_port.write(bytes([0]))
    except Exception:
        pass
    try:
        serial_port.close()
        G_TRIGGER_STATE["serial_status"] = "closed"
        g_log("trigger_serial_closed")
    except Exception as err:
        G_TRIGGER_STATE["serial_status"] = "close_failed"
        g_log(f"trigger_serial_close_failed {err}")


def g_log_trigger(code, label="", send_mode="immediate", serial_sent=False, details=""):
    log_path = G_TRIGGER_STATE.get("log_path")
    if not log_path:
        return
    try:
        g_write_trigger_log_header()
        G_TRIGGER_STATE["trigger_index"] = int(G_TRIGGER_STATE.get("trigger_index", 0)) + 1
        with Path(log_path).open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "trigger_index",
                    "core_time",
                    "trigger_code",
                    "label",
                    "send_mode",
                    "serial_port",
                    "serial_status",
                    "serial_sent",
                    "pulse_ms",
                    "details",
                ],
                lineterminator="\n",
            )
            writer.writerow(
                {
                    "trigger_index": G_TRIGGER_STATE["trigger_index"],
                    "core_time": f"{core.getTime():.6f}",
                    "trigger_code": int(code),
                    "label": g_text(label),
                    "send_mode": g_text(send_mode),
                    "serial_port": g_text(G_TRIGGER_STATE.get("port", "")),
                    "serial_status": g_text(G_TRIGGER_STATE.get("serial_status", "")),
                    "serial_sent": "1" if serial_sent else "0",
                    "pulse_ms": f"{g_float(G_TRIGGER_STATE.get('pulse_ms', 0), 0.0):.3f}",
                    "details": details,
                }
            )
    except Exception as err:
        g_log(f"trigger_log_write_failed {err}")


def g_send_trigger(code, label="", send_mode="immediate"):
    code = g_int(code, 0)
    if code <= 0 or code > 255:
        g_log(f"trigger_invalid code={code} label={label}")
        g_log_trigger(code, label, send_mode=send_mode, serial_sent=False, details="invalid_code")
        return
    serial_port = G_TRIGGER_STATE.get("serial")
    serial_sent = False
    details = g_text(G_TRIGGER_STATE.get("serial_status", ""))
    if serial_port is not None:
        try:
            serial_port.write(bytes([code]))
            serial_port.flush()
            pulse_sec = max(0.0, g_float(G_TRIGGER_STATE.get("pulse_ms", 5.0), 5.0) / 1000.0)
            if pulse_sec:
                core.wait(pulse_sec)
            serial_port.write(bytes([0]))
            serial_port.flush()
            serial_sent = True
            details = "serial_sent"
        except Exception as err:
            details = f"serial_error={err}"
            G_TRIGGER_STATE["serial_status"] = "send_failed"
            g_log(f"trigger_serial_send_failed code={code} label={label} err={err}")
    g_log_trigger(code, label, send_mode=send_mode, serial_sent=serial_sent, details=details)
    g_log(f"trigger code={code} label={label} mode={send_mode} serial_sent={serial_sent} details={details}")


def g_trigger_on_flip(code, label=""):
    try:
        win.callOnFlip(g_send_trigger, code, label, "on_flip")
    except Exception as err:
        g_log(f"trigger_call_on_flip_failed code={code} label={label} err={err}")
        g_send_trigger(code, label, "on_flip_fallback")


def g_mark_clock_started(state):
    state["started"] = True
    state["core_time"] = core.getTime()


def g_discourse_segment_trigger(roles, segment_index):
    target_index = int(g_target_index(roles))
    if segment_index < target_index - 1:
        return 198
    if segment_index == target_index - 1:
        return 199
    if segment_index == target_index:
        return 200
    if segment_index > target_index:
        return 201
    return 0


class GRecorder:
    sample_rate = 48000

    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(exist_ok=True)
        self.full_path = self.root / "full_session.wav"
        self.events_path = self.root / "recording_events.csv"
        self.segments_path = self.root / "recording_segments.csv"
        self.stream = None
        self.full_writer = None
        self.segments = []
        self.current_segment = None
        self.lock = threading.Lock()
        self.log_lock = threading.Lock()
        self.write_queue = queue.Queue()
        self.close_event = threading.Event()
        self.event_index = 0
        self.segment_index = 0
        self.total_frames = 0
        self.last_callback_core_time = None
        self.last_callback_end_sample = 0
        self.finalized = False
        self.full_blocks_since_flush = 0
        self.event_handle = None
        self.event_writer = None
        self.writer_error = None
        self._open_event_log()
        self.writer = threading.Thread(target=self._writer_loop, daemon=True)
        self.writer.start()
        self.closer = threading.Thread(target=self._closer_loop, daemon=True)
        self.closer.start()
        if G_RECORDING_AVAILABLE:
            self._ensure_stream()
        else:
            self._log_event("recording_unavailable", details="sounddevice/soundfile import failed")

    def start(self, stem, subdir=None):
        self.stop()
        if not G_RECORDING_AVAILABLE:
            return ""
        self._ensure_stream()
        if self.stream is None:
            return ""
        now = core.getTime()
        sample = self._sample_index_now(event_core_time=now)
        target_dir = self.root
        if subdir:
            target_dir = self.root / str(subdir)
            target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / f"{g_safe(stem)}.wav"
        with self.lock:
            self.segment_index += 1
            segment = {
                "id": self.segment_index,
                "stem": g_safe(stem),
                "path": path,
                "full_session_path": self.full_path,
                "requested_core_time": now,
                "requested_stream_time": self._stream_time_unlocked(),
                "requested_sample": sample,
                "onset_scheduled": False,
                "onset_core_time": None,
                "onset_stream_time": None,
                "onset_sample": None,
                "stop_core_time": None,
                "stop_stream_time": None,
                "stop_sample": None,
                "post_pad_sec": None,
                "end_sample": None,
                "clip_start_sample": None,
                "clip_end_sample": None,
                "written": False,
                "written_core_time": None,
                "n_frames": 0,
                "status": "waiting_for_picture_onset",
                "notes": "",
            }
            self.segments.append(segment)
            self.current_segment = segment
        self._log_event("segment_start_requested", segment, sample, details=str(path))
        self._write_segments_log()
        return str(path)

    def mark_onset_on_flip(self):
        with self.lock:
            segment = self.current_segment
            if segment is None:
                return
            if segment.get("onset_scheduled") or segment.get("onset_sample") is not None:
                return
            segment["onset_scheduled"] = True
            segment_id = segment["id"]
        try:
            win.callOnFlip(self._mark_segment_onset, segment_id)
        except Exception as err:
            self._mark_segment_onset(segment_id, note=f"callOnFlip_failed:{err}")

    def _mark_segment_onset(self, segment_id, note=""):
        now = core.getTime()
        stream_time = self._stream_time()
        sample = self._sample_index_now(stream_time=stream_time, event_core_time=now)
        with self.lock:
            segment = self._find_segment_unlocked(segment_id)
            if segment is None or segment.get("onset_sample") is not None:
                return
            segment["onset_core_time"] = now
            segment["onset_stream_time"] = stream_time
            segment["onset_sample"] = sample
            segment["status"] = "recording"
            if note:
                segment["notes"] = note
        self._log_event("picture_onset", segment, sample, stream_time=stream_time, details=note)
        self._write_segments_log()

    def _ensure_stream(self):
        if self.stream is not None:
            return
        if not G_RECORDING_AVAILABLE:
            return

        def callback(indata, frames, time_info, status):
            if status:
                g_log(f"rec_callback_status {status}")
            block = indata.copy()
            callback_core_time = core.getTime()
            with self.lock:
                block_start = self.total_frames
                block_end = block_start + int(frames)
                self.total_frames = block_end
                self.last_callback_core_time = callback_core_time
                self.last_callback_end_sample = block_end
            self.write_queue.put(("full", block))

        g_log("rec_stream_open_start")
        try:
            self.full_writer = _gurung_sf.SoundFile(
                str(self.full_path),
                mode="w",
                samplerate=self.sample_rate,
                channels=1,
            )
            self.stream = _gurung_sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
                callback=callback,
            )
            self.stream.start()
            self._log_event("full_session_start", sample_index=0, details=str(self.full_path))
            g_log("rec_stream_open_done")
        except Exception as err:
            g_log(f"rec_stream_open_failed {err}")
            self._log_event("recording_open_failed", details=str(err))
            self.stream = None
            try:
                if self.full_writer is not None:
                    self.full_writer.close()
            except Exception:
                pass
            self.full_writer = None

    def stop(self, grace_sec=None, event_core_time=None):
        if grace_sec is None:
            grace_sec = G_RECORDING_STOP_GRACE_SEC
        now = core.getTime()
        if event_core_time is None:
            event_core_time = now
        stream_time = self._stream_time()
        sample = self._sample_index_now(stream_time=stream_time, event_core_time=event_core_time)
        end_sample = sample + int(round(max(0.0, grace_sec) * self.sample_rate))
        with self.lock:
            segment = self.current_segment
            self.current_segment = None
            if segment is not None:
                if segment.get("onset_sample") is None:
                    segment["onset_sample"] = segment.get("requested_sample", sample)
                    segment["onset_core_time"] = segment.get("requested_core_time", event_core_time)
                    segment["onset_stream_time"] = segment.get("requested_stream_time", stream_time)
                    segment["notes"] = "forced_onset_from_start_request"
                segment["stop_core_time"] = event_core_time
                segment["stop_stream_time"] = stream_time
                segment["stop_sample"] = sample
                segment["post_pad_sec"] = max(0.0, grace_sec)
                segment["end_sample"] = max(int(segment["onset_sample"]), int(end_sample))
                segment["status"] = "stopped_waiting_for_tail"
        if segment is None:
            return ""
        path = segment["path"]
        self._log_event(
            "segment_stop_requested",
            segment,
            sample,
            stream_time=stream_time,
            details=f"grace={grace_sec:.3f};event_core_time={event_core_time:.6f}",
        )
        self._write_segments_log()
        return str(path)

    def _closer_loop(self):
        while True:
            self.close_event.wait(0.02)
            self.close_event.clear()
            self._flush_ready_segments()

    def _flush_ready_segments(self, force=False):
        return

    def _writer_loop(self):
        while True:
            item = self.write_queue.get()
            try:
                if item is None:
                    self._close_full_writer()
                    return
                kind = item[0]
                if kind == "full":
                    self._write_full_block(item[1])
            except Exception as err:
                self.writer_error = err
                g_log(f"rec_writer_loop_error {err}")
            finally:
                self.write_queue.task_done()

    def _write_full_block(self, block):
        if self.full_writer is None:
            return
        self.full_writer.write(block)
        self.full_blocks_since_flush += 1
        if self.full_blocks_since_flush >= 10:
            self.full_writer.flush()
            self.full_blocks_since_flush = 0

    def _write_segment_clips(self):
        if not G_RECORDING_AVAILABLE:
            return
        if not self.full_path.exists():
            self._log_event("segment_clip_failed", details=f"missing_full_session={self.full_path}")
            return
        try:
            with _gurung_sf.SoundFile(str(self.full_path), mode="r") as full_audio:
                available_frames = len(full_audio)
                for segment in list(self.segments):
                    if segment.get("onset_sample") is None:
                        continue
                    start_sample = max(0, int(segment.get("onset_sample") or 0))
                    requested_end_sample = int(segment.get("end_sample") or available_frames)
                    requested_end_sample = max(start_sample, requested_end_sample)
                    clip_start = min(start_sample, available_frames)
                    clip_end = min(requested_end_sample, available_frames)
                    full_audio.seek(clip_start)
                    audio = full_audio.read(clip_end - clip_start, dtype="float32", always_2d=True)
                    _gurung_sf.write(str(segment["path"]), audio, full_audio.samplerate)
                    status = "written"
                    notes = g_text(segment.get("notes", ""))
                    if requested_end_sample > available_frames:
                        status = "written_truncated_at_experiment_stop"
                        suffix = f"truncated_end_sample={requested_end_sample};available_frames={available_frames}"
                        notes = f"{notes} {suffix}".strip()
                    with self.lock:
                        segment["clip_start_sample"] = clip_start
                        segment["clip_end_sample"] = clip_end
                        segment["written"] = True
                        segment["written_core_time"] = core.getTime()
                        segment["n_frames"] = int(audio.shape[0])
                        segment["status"] = status
                        segment["notes"] = notes
                    self._log_event(
                        "segment_written",
                        segment,
                        sample_index=clip_start,
                        details=f"frames={int(audio.shape[0])} clip={clip_start}:{clip_end}",
                    )
        except Exception as err:
            with self.lock:
                for segment in self.segments:
                    if not segment.get("written"):
                        segment["status"] = "clip_failed"
                        segment["notes"] = f"{segment.get('notes', '')} clip_failed:{err}".strip()
            self._log_event("segment_clip_failed", details=str(err))
        self._write_segments_log()

    def _close_full_writer(self):
        writer = self.full_writer
        self.full_writer = None
        if writer is None:
            return
        try:
            writer.flush()
        except Exception:
            pass
        try:
            writer.close()
            self._log_event("full_session_closed", sample_index=self._total_frames(), details=str(self.full_path))
        except Exception as err:
            g_log(f"rec_full_writer_close_failed {err}")

    def _time_field(self, time_info, name):
        try:
            value = getattr(time_info, name)
        except Exception:
            try:
                value = time_info[name]
            except Exception:
                return None
        try:
            return float(value)
        except Exception:
            return None

    def _stream_time(self):
        with self.lock:
            return self._stream_time_unlocked()

    def _stream_time_unlocked(self):
        try:
            if self.stream is not None:
                return float(self.stream.time)
        except Exception:
            pass
        return None

    def _sample_index_now(self, stream_time=None, event_core_time=None):
        with self.lock:
            total_frames = self.total_frames
            last_callback_core_time = self.last_callback_core_time
            last_callback_end_sample = self.last_callback_end_sample
            can_estimate = self.stream is not None and not self.finalized
        if can_estimate and last_callback_core_time is not None:
            if event_core_time is None:
                event_core_time = core.getTime()
            estimate = int(round(last_callback_end_sample + ((event_core_time - last_callback_core_time) * self.sample_rate)))
            return max(0, estimate)
        return int(total_frames)

    def _total_frames(self):
        with self.lock:
            return int(self.total_frames)

    def _find_segment_unlocked(self, segment_id):
        for segment in self.segments:
            if segment.get("id") == segment_id:
                return segment
        return None

    def _open_event_log(self):
        self.event_fields = (
            "event_index",
            "event_type",
            "segment_id",
            "stem",
            "path",
            "core_time",
            "stream_time",
            "sample_index",
            "details",
        )
        self.segment_fields = (
            "segment_id",
            "stem",
            "path",
            "full_session_path",
            "status",
            "requested_core_time",
            "requested_stream_time",
            "requested_sample",
            "onset_core_time",
            "onset_stream_time",
            "onset_sample",
            "stop_core_time",
            "stop_stream_time",
            "stop_sample",
            "post_pad_sec",
            "end_sample",
            "clip_start_sample",
            "clip_end_sample",
            "written_core_time",
            "n_frames",
            "notes",
        )
        try:
            self.event_handle = self.events_path.open("w", encoding="utf-8", newline="")
            self.event_writer = csv.DictWriter(self.event_handle, fieldnames=self.event_fields, lineterminator="\n")
            self.event_writer.writeheader()
            self.event_handle.flush()
        except Exception as err:
            g_log(f"recording_event_log_open_failed {err}")
            self.event_handle = None
            self.event_writer = None
        self._write_segments_log()

    def _format_value(self, value):
        if value is None:
            return ""
        if isinstance(value, float):
            return f"{value:.6f}"
        return str(value)

    def _log_event(self, event_type, segment=None, sample_index=None, stream_time=None, details=""):
        core_time = core.getTime()
        if stream_time is None:
            stream_time = self._stream_time()
        if sample_index is None:
            sample_index = self._sample_index_now(stream_time=stream_time, event_core_time=core_time)
        segment_id = ""
        stem = ""
        path = ""
        if segment is not None:
            segment_id = segment.get("id", "")
            stem = segment.get("stem", "")
            path = segment.get("path", "")
        with self.log_lock:
            self.event_index += 1
            row = {
                "event_index": self.event_index,
                "event_type": event_type,
                "segment_id": segment_id,
                "stem": stem,
                "path": path,
                "core_time": self._format_value(core_time),
                "stream_time": self._format_value(stream_time),
                "sample_index": self._format_value(sample_index),
                "details": details,
            }
            try:
                if self.event_writer is not None:
                    self.event_writer.writerow(row)
                    self.event_handle.flush()
            except Exception as err:
                g_log(f"recording_event_log_write_failed {err}")
        g_log(f"recording_event {event_type} segment={segment_id} sample={row['sample_index']} {details}")

    def _segment_row(self, segment):
        row = {}
        for field in self.segment_fields:
            if field == "segment_id":
                value = segment.get("id")
            else:
                value = segment.get(field)
            row[field] = self._format_value(value)
        return row

    def _write_segments_log(self):
        try:
            with self.log_lock:
                with self.segments_path.open("w", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=self.segment_fields, lineterminator="\n")
                    writer.writeheader()
                    with self.lock:
                        rows = [self._segment_row(segment) for segment in self.segments]
                    writer.writerows(rows)
        except Exception as err:
            g_log(f"recording_segments_log_write_failed {err}")

    def _wait_for_pending_tail(self):
        deadline = core.getTime() + G_RECORDING_STOP_GRACE_SEC + 0.2
        while core.getTime() < deadline:
            with self.lock:
                pending = [
                    int(segment["end_sample"])
                    for segment in self.segments
                    if segment.get("end_sample") is not None and not segment.get("written")
                ]
                total_frames = self.total_frames
            if not pending or max(pending) <= total_frames:
                return
            core.wait(0.02)

    def _force_close_open_segments(self):
        now = core.getTime()
        sample = self._sample_index_now(event_core_time=now)
        with self.lock:
            for segment in self.segments:
                if segment.get("written"):
                    continue
                if segment.get("onset_sample") is None:
                    segment["onset_sample"] = segment.get("requested_sample", sample)
                    segment["onset_core_time"] = segment.get("requested_core_time", now)
                    segment["onset_stream_time"] = segment.get("requested_stream_time")
                    segment["notes"] = "forced_onset_during_cleanup"
                if segment.get("end_sample") is None:
                    segment["stop_core_time"] = now
                    segment["stop_stream_time"] = self._stream_time_unlocked()
                    segment["stop_sample"] = sample
                    segment["post_pad_sec"] = 0.0
                    segment["end_sample"] = max(int(segment["onset_sample"]), int(sample))
                    segment["status"] = "forced_stop_during_cleanup"

    def finalize(self, wait_for_post_pad=True):
        with self.lock:
            if self.finalized:
                return
            self.finalized = True
        self._log_event("recording_finalize_start", details=f"wait_for_post_pad={wait_for_post_pad}")
        if self.current_segment is not None:
            self.stop(grace_sec=0.0)
        if wait_for_post_pad:
            self._wait_for_pending_tail()
        stream = self.stream
        self.stream = None
        if stream is not None:
            try:
                g_log("rec_stream_stop_start")
                stream.stop()
                g_log("rec_stream_stop_done")
            except Exception as err:
                g_log(f"rec_stream_stop_failed {err}")
            try:
                stream.close()
                g_log("rec_stream_close_done")
            except Exception as err:
                g_log(f"rec_stream_close_failed {err}")
        self._force_close_open_segments()
        try:
            self.write_queue.join()
        except Exception as err:
            g_log(f"rec_write_queue_join_failed {err}")
        self.write_queue.put(None)
        try:
            self.write_queue.join()
        except Exception:
            pass
        try:
            self.writer.join(timeout=2.0)
        except Exception:
            pass
        self._write_segment_clips()
        self._write_segments_log()
        self._log_event("recording_finalize_done", details=f"writer_error={self.writer_error}")
        try:
            if self.event_handle is not None:
                self.event_handle.flush()
                self.event_handle.close()
        except Exception:
            pass

    def abort(self):
        self.finalize(wait_for_post_pad=False)


def g_cleanup(wait_for_post_pad=True):
    try:
        G_RECORDER.finalize(wait_for_post_pad=wait_for_post_pad)
    except Exception as err:
        g_log(f"Recorder cleanup failed: {err}")
    try:
        g_close_serial_trigger()
    except Exception as err:
        g_log(f"Trigger cleanup failed: {err}")


G_RECORDINGS_DIR = g_session_recordings_dir()
g_init_trigger_log(G_RECORDINGS_DIR)
G_RECORDER = GRecorder(G_RECORDINGS_DIR)


def g_abort_and_quit():
    g_cleanup(wait_for_post_pad=True)
    core.quit()


try:
    event.globalKeys.add(key="escape", func=g_abort_and_quit, name="gurung_escape_quit")
except Exception as _gurung_global_key_error:
    g_log(f"Global escape key was not registered: {_gurung_global_key_error}")


try:
    runAtExit.append(g_cleanup)
except Exception as _gurung_run_at_exit_error:
    g_log(f"Could not register recorder runAtExit cleanup: {_gurung_run_at_exit_error}")


try:
    atexit.register(g_cleanup)
except Exception as _gurung_atexit_error:
    g_log(f"Could not register recorder atexit cleanup: {_gurung_atexit_error}")
'''


INSTRUCTIONS_BEGIN = r'''
win.color = "white"
instruction_icon = visual.ImageStim(win, image=g_path("Stimuli/sound.png"), pos=(0, 0), size=(0.22, 0.22), interpolate=True)
instruction_audio = None
instruction_started = False
instruction_clock = core.Clock()
instruction_duration = 0.0
instruction_first_play_complete = False
instruction_replay_unlocked = False
event.clearEvents()
'''

INSTRUCTIONS_EACH = r'''
instruction_icon.draw()
if instruction_started and not instruction_first_play_complete and instruction_clock.getTime() >= instruction_duration:
    instruction_first_play_complete = True
keys = event.getKeys(keyList=["space", "return", "escape"])
if "escape" in keys:
    g_abort_and_quit()
if "return" in keys:
    if instruction_audio:
        instruction_audio.stop()
    instruction_replay_unlocked = instruction_started or instruction_first_play_complete
    instruction_audio = g_play_audio("Audio/new_disc_instr1.wav")
    instruction_started = True
    instruction_clock.reset()
    instruction_duration = g_float(instruction_audio.getDuration() if instruction_audio else 0, 0.0)
    event.clearEvents()
elif "space" in keys:
    if not instruction_started:
        instruction_audio = g_play_audio("Audio/new_disc_instr1.wav")
        instruction_started = True
        instruction_clock.reset()
        instruction_duration = g_float(instruction_audio.getDuration() if instruction_audio else 0, 0.0)
        event.clearEvents()
    else:
        if instruction_first_play_complete or instruction_replay_unlocked:
            if instruction_audio:
                instruction_audio.stop()
            continueRoutine = False
'''

PRACTICE_BEGIN = r'''
G_PRACTICE_TRIAL_INDEX += 1
win.color = "white"
practice_skip_between = G_PRACTICE_TRIAL_INDEX == 1
practice_previous_trial_index = G_PRACTICE_TRIAL_INDEX - 1
practice_between_audio_value = "" if practice_skip_between else g_text(G_PRACTICE_AFTER_TRIAL_AUDIO.get(practice_previous_trial_index, ""))
practice_between_uses_speaker = False if practice_skip_between else practice_previous_trial_index in G_PRACTICE_SPEAKER_SCREEN_AFTER_TRIALS
practice_between_image = "" if (practice_skip_between or practice_between_uses_speaker) else g_next_between_image()
practice_between_display_image = "" if practice_skip_between else (G_AUDIO_SPEAKER_IMAGE if practice_between_uses_speaker else practice_between_image)
practice_placeholder = None
if not practice_skip_between:
    practice_placeholder = (
        g_audio_speaker_image(win) if practice_between_uses_speaker else g_fullscreen_image(win, practice_between_image)
    )
practice_roles, practice_paths = g_roles_and_paths()
practice_images = []
practice_arrows = []
practice_segment = 0
practice_phase = "segment" if practice_skip_between else "between"
practice_between_clock = core.Clock()
practice_between_audio = None
practice_between_audio_lock = G_AUDIO_PROBE_LOCK_SEC if practice_between_audio_value else 0.0
practice_between_audio_duration = 0.0
practice_between_is_question = bool(practice_between_audio_value and not practice_between_uses_speaker)
practice_between_audio_done = not practice_between_is_question
practice_between_instruction_first_play_complete = not practice_between_uses_speaker
practice_between_instruction_replay_unlocked = False
practice_listener_clock = core.Clock()
practice_listener_audio_file = ""
practice_listener_stem = ""
practice_after_placeholder = None
practice_after_between_image = ""
practice_after_between_clock = core.Clock()
practice_after_between_lock = 0.0
practice_after_between_audio_duration = 0.0
practice_after_question_audio_done = True
practice_after_listener_clock = core.Clock()
practice_after_listener_audio_file = ""
practice_audio = None
practice_audio_value = ""
practice_audio_clock = core.Clock()
practice_audio_duration = 0
practice_segment_audio_value = ""
practice_segment_audio_started = False
practice_segment_audio_lock = 0.0
if practice_between_audio_value and not practice_skip_between:
    practice_between_audio = g_play_audio(practice_between_audio_value)
    practice_between_audio_duration = g_float(practice_between_audio.getDuration() if practice_between_audio else 0, 0.0)
    if practice_between_uses_speaker and practice_between_audio_duration <= 0:
        practice_between_instruction_first_play_complete = True
practice_between_clock.reset()
thisExp.addData("practice_trial_index", G_PRACTICE_TRIAL_INDEX)
thisExp.addData("practice_between_image", g_path(practice_between_display_image))
thisExp.addData("practice_between_audio", g_path(practice_between_audio_value) if practice_between_audio_value else "")
thisExp.addData("practice_between_skipped", int(practice_skip_between))
if practice_skip_between:
    practice_images, practice_arrows = g_make_sequence(win, practice_roles, practice_paths)
    practice_segment_audio_value = g_practice_picture_audio(G_PRACTICE_TRIAL_INDEX, practice_segment)
    practice_segment_audio_started = False
    practice_segment_audio_lock = 0.0
    practice_stem = g_practice_stem(G_PRACTICE_TRIAL_INDEX, practice_segment + 1)
    G_RECORDER.start(practice_stem)
event.clearEvents()
'''

PRACTICE_EACH = r'''
if practice_phase == "between":
    practice_placeholder.draw()
    if practice_between_is_question and not practice_between_audio_done and practice_between_clock.getTime() >= practice_between_audio_duration:
        if practice_between_audio:
            practice_between_audio.stop()
        practice_between_audio = None
        practice_listener_stem = g_listener_practice_stem(practice_previous_trial_index, practice_between_audio_value)
        practice_listener_audio_file = G_RECORDER.start(practice_listener_stem, subdir=G_LISTENER_RESPONSE_DIRNAME)
        practice_listener_clock.reset()
        practice_between_audio_done = True
        event.clearEvents()
    if practice_between_uses_speaker and not practice_between_instruction_first_play_complete and practice_between_clock.getTime() >= practice_between_audio_duration:
        practice_between_instruction_first_play_complete = True
    keys = event.getKeys(keyList=["space", "return", "escape"], timeStamped=core.monotonicClock)
    key_names = g_key_names(keys)
    if "escape" in key_names:
        g_abort_and_quit()
    if practice_between_uses_speaker and "return" in key_names:
        if practice_between_audio:
            practice_between_audio.stop()
        practice_between_instruction_replay_unlocked = True
        practice_between_audio = g_play_audio(practice_between_audio_value)
        practice_between_audio_duration = g_float(practice_between_audio.getDuration() if practice_between_audio else 0, 0.0)
        practice_between_clock.reset()
        event.clearEvents()
    if practice_between_uses_speaker:
        practice_between_can_continue = (
            "space" in key_names
            and (
                practice_between_instruction_first_play_complete
                or practice_between_instruction_replay_unlocked
            )
        )
    elif practice_between_is_question:
        practice_between_can_continue = (
            practice_between_audio_done
            and "space" in key_names
            and practice_listener_clock.getTime() >= G_LISTENER_RESPONSE_MIN_SEC
        )
    else:
        practice_between_can_continue = "space" in key_names
    if practice_between_can_continue:
        if practice_between_is_question:
            stopped_listener_file = G_RECORDER.stop(event_core_time=g_key_time(keys, "space"))
            if stopped_listener_file:
                practice_listener_audio_file = stopped_listener_file
            thisExp.addData("practice_listener_reference_trial", practice_previous_trial_index)
            thisExp.addData("practice_listener_response_audio", practice_listener_audio_file)
            thisExp.addData("practice_listener_response_rt", practice_listener_clock.getTime())
        if practice_between_audio:
            practice_between_audio.stop()
        practice_between_audio = None
        thisExp.addData("practice_between_rt", practice_between_clock.getTime())
        g_release_fullscreen_image(practice_placeholder)
        practice_placeholder = None
        practice_images, practice_arrows = g_make_sequence(win, practice_roles, practice_paths)
        practice_pre_audio_value = g_practice_pre_picture_audio(G_PRACTICE_TRIAL_INDEX, practice_segment, len(practice_images))
        if practice_pre_audio_value:
            practice_phase = "practice_audio"
            practice_audio_value = practice_pre_audio_value
            practice_audio = g_play_audio(practice_audio_value)
            practice_audio_clock.reset()
            practice_audio_duration = g_float(practice_audio.getDuration(), 0) if practice_audio else 0
            thisExp.addData(f"practice_seg{practice_segment + 1}_pre_audio", g_path(practice_audio_value))
        else:
            practice_phase = "segment"
            practice_segment_audio_value = g_practice_picture_audio(G_PRACTICE_TRIAL_INDEX, practice_segment)
            practice_segment_audio_started = False
            practice_segment_audio_lock = 0.0
            practice_stem = g_practice_stem(G_PRACTICE_TRIAL_INDEX, practice_segment + 1)
            G_RECORDER.start(practice_stem)
        event.clearEvents()
elif practice_phase == "segment":
    g_draw_sequence(practice_images, practice_arrows, practice_segment + 1)
    G_RECORDER.mark_onset_on_flip()
    if practice_segment_audio_value and not practice_segment_audio_started:
        practice_audio_value = practice_segment_audio_value
        practice_audio = g_play_audio(practice_audio_value)
        practice_audio_clock.reset()
        practice_segment_audio_lock = g_float(practice_audio.getDuration(), 0) if practice_audio else 0
        practice_segment_audio_started = True
        thisExp.addData(f"practice_seg{practice_segment + 1}_onset_audio", g_path(practice_audio_value))
    keys = event.getKeys(keyList=["space", "escape"], timeStamped=core.monotonicClock)
    key_names = g_key_names(keys)
    if "escape" in key_names:
        g_abort_and_quit()
    if "space" in key_names and practice_audio_clock.getTime() >= practice_segment_audio_lock:
        if practice_audio:
            practice_audio.stop()
        practice_audio = None
        audio_file = G_RECORDER.stop(event_core_time=g_key_time(keys, "space"))
        seg = practice_segment + 1
        thisExp.addData(f"practice_seg{seg}_role", practice_roles[practice_segment])
        thisExp.addData(f"practice_seg{seg}_audio", audio_file)
        if practice_segment >= len(practice_images) - 1:
            practice_audio_value = g_text(G_PRACTICE_AFTER_TRIAL_AUDIO.get(G_PRACTICE_TRIAL_INDEX, ""))
            if practice_audio_value and G_PRACTICE_TRIAL_INDEX >= G_PRACTICE_TRIAL_COUNT:
                practice_phase = "practice_after_between"
                practice_after_between_image = g_next_between_image()
                practice_after_placeholder = g_fullscreen_image(win, practice_after_between_image)
                practice_audio = g_play_audio(practice_audio_value)
                practice_audio_clock.reset()
                practice_after_between_audio_duration = g_float(practice_audio.getDuration() if practice_audio else 0, 0.0)
                practice_after_between_clock.reset()
                practice_after_question_audio_done = False
                practice_after_listener_audio_file = ""
                thisExp.addData("practice_after_trial_audio", g_path(practice_audio_value))
                thisExp.addData("practice_after_trial_between_image", g_path(practice_after_between_image))
            else:
                continueRoutine = False
        else:
            practice_segment += 1
            practice_pre_audio_value = g_practice_pre_picture_audio(G_PRACTICE_TRIAL_INDEX, practice_segment, len(practice_images))
            if practice_pre_audio_value:
                practice_phase = "practice_audio"
                practice_audio_value = practice_pre_audio_value
                practice_audio = g_play_audio(practice_audio_value)
                practice_audio_clock.reset()
                practice_audio_duration = g_float(practice_audio.getDuration(), 0) if practice_audio else 0
                thisExp.addData(f"practice_seg{practice_segment + 1}_pre_audio", g_path(practice_audio_value))
            else:
                practice_segment_audio_value = g_practice_picture_audio(G_PRACTICE_TRIAL_INDEX, practice_segment)
                practice_segment_audio_started = False
                practice_segment_audio_lock = 0.0
                practice_stem = g_practice_stem(G_PRACTICE_TRIAL_INDEX, practice_segment + 1)
                G_RECORDER.start(practice_stem)
        event.clearEvents()
elif practice_phase == "practice_audio":
    g_draw_sequence(practice_images, practice_arrows, practice_segment)
    if practice_audio_clock.getTime() >= practice_audio_duration:
        if practice_audio:
            practice_audio.stop()
        practice_audio = None
        practice_phase = "segment"
        practice_segment_audio_value = g_practice_picture_audio(G_PRACTICE_TRIAL_INDEX, practice_segment)
        practice_segment_audio_started = False
        practice_segment_audio_lock = 0.0
        practice_stem = g_practice_stem(G_PRACTICE_TRIAL_INDEX, practice_segment + 1)
        G_RECORDER.start(practice_stem)
        event.clearEvents()
elif practice_phase == "practice_after_between":
    practice_after_placeholder.draw()
    if not practice_after_question_audio_done and practice_audio_clock.getTime() >= practice_after_between_audio_duration:
        if practice_audio:
            practice_audio.stop()
        practice_audio = None
        practice_after_listener_audio_file = G_RECORDER.start(
            g_listener_practice_stem(G_PRACTICE_TRIAL_INDEX, practice_audio_value),
            subdir=G_LISTENER_RESPONSE_DIRNAME,
        )
        practice_after_listener_clock.reset()
        practice_after_question_audio_done = True
        event.clearEvents()
    keys = event.getKeys(keyList=["space", "escape"], timeStamped=core.monotonicClock)
    key_names = g_key_names(keys)
    if "escape" in key_names:
        g_abort_and_quit()
    if (
        "space" in key_names
        and practice_after_question_audio_done
        and practice_after_listener_clock.getTime() >= G_LISTENER_RESPONSE_MIN_SEC
    ):
        stopped_listener_file = G_RECORDER.stop(event_core_time=g_key_time(keys, "space"))
        if stopped_listener_file:
            practice_after_listener_audio_file = stopped_listener_file
        thisExp.addData("practice_listener_reference_trial", G_PRACTICE_TRIAL_INDEX)
        thisExp.addData("practice_listener_response_audio", practice_after_listener_audio_file)
        thisExp.addData("practice_listener_response_rt", practice_after_listener_clock.getTime())
        if practice_audio:
            practice_audio.stop()
        practice_audio = None
        g_release_fullscreen_image(practice_after_placeholder)
        practice_after_placeholder = None
        continueRoutine = False
        event.clearEvents()
'''

PRACTICE_END = r'''
G_RECORDER.stop()
if practice_between_audio:
    practice_between_audio.stop()
if practice_audio:
    practice_audio.stop()
g_release_stims(practice_images, practice_arrows)
g_release_fullscreen_image(practice_placeholder)
g_release_fullscreen_image(practice_after_placeholder)
practice_images = []
practice_arrows = []
practice_placeholder = None
practice_after_placeholder = None
'''

PRACTICE_DONE_BEGIN = r'''
win.color = "white"
practice_done_icon = visual.ImageStim(win, image=g_path("Stimuli/sound.png"), pos=(0, 0), size=(0.22, 0.22), interpolate=True)
practice_done_audio = g_play_audio("Audio/new_disc_instr3.wav")
practice_done_clock = core.Clock()
practice_done_duration = g_float(practice_done_audio.getDuration() if practice_done_audio else 0, 0.0)
practice_done_first_play_complete = False
practice_done_replay_unlocked = False
event.clearEvents()
'''

PRACTICE_DONE_EACH = r'''
practice_done_icon.draw()
if not practice_done_first_play_complete and practice_done_clock.getTime() >= practice_done_duration:
    practice_done_first_play_complete = True
keys = event.getKeys(keyList=["space", "return", "escape"])
if "escape" in keys:
    g_abort_and_quit()
if "return" in keys:
    if practice_done_audio:
        practice_done_audio.stop()
    practice_done_replay_unlocked = True
    practice_done_audio = g_play_audio("Audio/new_disc_instr3.wav")
    practice_done_clock.reset()
    practice_done_duration = g_float(practice_done_audio.getDuration() if practice_done_audio else 0, 0.0)
    event.clearEvents()
if "space" in keys:
    if practice_done_first_play_complete or practice_done_replay_unlocked:
        if practice_done_audio:
            practice_done_audio.stop()
        continueRoutine = False
'''

MAIN_BEGIN = r'''
G_MAIN_TRIAL_INDEX += 1
win.color = "white"
main_skip_between_after_break = G_MAIN_TRIAL_INDEX > 1 and (G_MAIN_TRIAL_INDEX - 1) % G_MAIN_BLOCK_SIZE == 0
main_between_image = "" if main_skip_between_after_break else g_next_between_image()
main_placeholder = None if main_skip_between_after_break else g_fullscreen_image(win, main_between_image)
main_roles, main_paths = g_roles_and_paths()
main_images = []
main_arrows = []
main_segment = 0
main_phase = "segment" if main_skip_between_after_break else "between"
main_between_clock = core.Clock()
main_between_audio = None
main_between_audio_value = "" if main_skip_between_after_break else g_text(globals().get("between_audio", ""))
main_audio_lock = 0.0 if main_skip_between_after_break else g_float(globals().get("between_audio_lock_sec", 0), 0.0)
main_dataset_number = g_int(globals().get("dataset_number", 0), 0)
main_condition_id = g_text(globals().get("condition_id", "unknown_condition"))
main_stimulus_set = g_int(globals().get("stimulus_set", 0), 0)
main_condition_trigger = g_int(globals().get("condition_trigger", 0), 0)
main_item_trigger = g_int(globals().get("item_trigger", 0), 0)
main_listener_reference = dict(G_LAST_MAIN_TRIAL_INFO) if G_LAST_MAIN_TRIAL_INFO else {}
main_between_audio_duration = 0.0
main_between_audio_done = not bool(main_between_audio_value)
main_listener_clock = core.Clock()
main_listener_audio_file = ""
main_target_index = int(g_target_index(main_roles))
main_target_clock = core.Clock()
main_target_state = {"started": False, "condition_sent": False, "item_sent": False}
main_segment_trigger_scheduled = False
if main_between_audio_value:
    main_between_audio = g_play_audio(main_between_audio_value)
    main_between_audio_duration = g_float(main_between_audio.getDuration() if main_between_audio else 0, 0.0)
main_between_clock.reset()
thisExp.addData("main_trial_index", G_MAIN_TRIAL_INDEX)
thisExp.addData("experiment_list", g_selected_list())
thisExp.addData("between_image", g_path(main_between_image))
thisExp.addData("between_skipped_after_break", int(main_skip_between_after_break))
thisExp.addData("audio_probe", audio_probe)
thisExp.addData("between_audio", g_path(main_between_audio_value) if main_between_audio_value else "")
thisExp.addData("stimulus_set", main_stimulus_set)
thisExp.addData("condition_trigger", main_condition_trigger)
thisExp.addData("item_trigger", main_item_trigger)
if main_skip_between_after_break:
    main_images, main_arrows = g_make_sequence(win, main_roles, main_paths)
    main_stem = g_discourse_main_stem(
        G_MAIN_TRIAL_INDEX,
        main_dataset_number,
        main_condition_id,
        main_segment + 1,
        main_roles[main_segment],
    )
    G_RECORDER.start(main_stem)
event.clearEvents()
'''

MAIN_EACH = r'''
if main_phase == "between":
    main_placeholder.draw()
    if main_between_audio_value and not main_between_audio_done and main_between_clock.getTime() >= main_between_audio_duration:
        if main_between_audio:
            main_between_audio.stop()
        main_between_audio = None
        main_listener_audio_file = G_RECORDER.start(
            g_listener_main_stem(main_listener_reference, main_between_audio_value),
            subdir=G_LISTENER_RESPONSE_DIRNAME,
        )
        main_listener_clock.reset()
        main_between_audio_done = True
        event.clearEvents()
    keys = event.getKeys(keyList=["space", "escape"], timeStamped=core.monotonicClock)
    key_names = g_key_names(keys)
    if "escape" in key_names:
        g_abort_and_quit()
    if main_between_audio_value:
        main_between_can_continue = (
            main_between_audio_done
            and "space" in key_names
            and main_listener_clock.getTime() >= G_LISTENER_RESPONSE_MIN_SEC
        )
    else:
        main_between_can_continue = "space" in key_names and main_between_clock.getTime() >= main_audio_lock
    if main_between_can_continue:
        if main_between_audio_value:
            stopped_listener_file = G_RECORDER.stop(event_core_time=g_key_time(keys, "space"))
            if stopped_listener_file:
                main_listener_audio_file = stopped_listener_file
            thisExp.addData("listener_reference_main_trial_index", g_int(main_listener_reference.get("trial_index", 0), 0))
            thisExp.addData("listener_reference_dataset_number", g_int(main_listener_reference.get("dataset_number", 0), 0))
            thisExp.addData("listener_reference_condition_id", g_text(main_listener_reference.get("condition_id", "")))
            thisExp.addData("listener_response_audio", main_listener_audio_file)
            thisExp.addData("listener_response_rt", main_listener_clock.getTime())
        if main_between_audio:
            main_between_audio.stop()
        main_between_audio = None
        thisExp.addData("between_rt", main_between_clock.getTime())
        g_release_fullscreen_image(main_placeholder)
        main_placeholder = None
        main_images, main_arrows = g_make_sequence(win, main_roles, main_paths)
        main_phase = "segment"
        main_stem = g_discourse_main_stem(
            G_MAIN_TRIAL_INDEX,
            main_dataset_number,
            main_condition_id,
            main_segment + 1,
            main_roles[main_segment],
        )
        G_RECORDER.start(main_stem)
        main_segment_trigger_scheduled = False
        event.clearEvents()
elif main_phase == "segment":
    g_draw_sequence(main_images, main_arrows, main_segment + 1)
    if not main_segment_trigger_scheduled:
        G_RECORDER.mark_onset_on_flip()
        main_segment_trigger = g_discourse_segment_trigger(main_roles, main_segment)
        if main_segment_trigger:
            g_trigger_on_flip(
                main_segment_trigger,
                f"discourse_trial{G_MAIN_TRIAL_INDEX:03d}_set{main_stimulus_set}_seg{main_segment + 1}_{main_roles[main_segment]}",
            )
        if main_segment == main_target_index:
            win.callOnFlip(main_target_clock.reset)
            win.callOnFlip(g_mark_clock_started, main_target_state)
        main_segment_trigger_scheduled = True
    if main_target_state.get("started"):
        if (not main_target_state.get("condition_sent")) and main_target_clock.getTime() >= 0.200:
            g_send_trigger(
                main_condition_trigger,
                f"discourse_trial{G_MAIN_TRIAL_INDEX:03d}_condition_{main_condition_id}",
            )
            main_target_state["condition_sent"] = True
        if (not main_target_state.get("item_sent")) and main_target_clock.getTime() >= 0.400:
            g_send_trigger(
                main_item_trigger,
                f"discourse_trial{G_MAIN_TRIAL_INDEX:03d}_item{main_item_trigger:03d}",
            )
            main_target_state["item_sent"] = True
    keys = event.getKeys(keyList=["space", "escape"], timeStamped=core.monotonicClock)
    key_names = g_key_names(keys)
    if "escape" in key_names:
        g_abort_and_quit()
    main_can_advance_segment = main_segment != main_target_index or main_target_state.get("item_sent")
    if "space" in key_names and main_can_advance_segment:
        audio_file = G_RECORDER.stop(event_core_time=g_key_time(keys, "space"))
        seg = main_segment + 1
        thisExp.addData(f"seg{seg}_role", main_roles[main_segment])
        thisExp.addData(f"seg{seg}_audio", audio_file)
        if main_segment >= len(main_images) - 1:
            g_send_trigger(202, f"discourse_trial{G_MAIN_TRIAL_INDEX:03d}_end")
            continueRoutine = False
        else:
            main_segment += 1
            main_stem = g_discourse_main_stem(
                G_MAIN_TRIAL_INDEX,
                main_dataset_number,
                main_condition_id,
                main_segment + 1,
                main_roles[main_segment],
            )
            G_RECORDER.start(main_stem)
            main_segment_trigger_scheduled = False
        event.clearEvents()
'''

MAIN_END = r'''
G_RECORDER.stop()
if main_between_audio:
    main_between_audio.stop()
G_LAST_MAIN_TRIAL_INFO = {
    "trial_index": G_MAIN_TRIAL_INDEX,
    "dataset_number": main_dataset_number,
    "condition_id": main_condition_id,
}
g_release_stims(main_images, main_arrows)
g_release_fullscreen_image(main_placeholder)
main_images = []
main_arrows = []
main_placeholder = None
'''

BREAK_BEGIN = r'''
win.color = "white"
break_image = visual.ImageStim(win, image=g_path("Stimuli/break.png"), pos=(0, 0), size=(0.55, 0.55), interpolate=True)
break_clock = core.Clock()
event.clearEvents()
'''

BREAK_EACH = r'''
break_image.draw()
keys = event.getKeys(keyList=["space", "escape"])
if "escape" in keys:
    g_abort_and_quit()
if "space" in keys and break_clock.getTime() >= 30:
    continueRoutine = False
'''

END_BEGIN = r'''
win.color = "white"
finish_image = visual.ImageStim(win, image=g_path("Stimuli/finish.png"), pos=(0, 0), size=(0.55, 0.275), interpolate=True)
finish_clock = core.Clock()
event.clearEvents()
'''

END_EACH = r'''
finish_image.draw()
keys = event.getKeys(keyList=["space", "escape"])
if "escape" in keys or "space" in keys or finish_clock.getTime() >= 10:
    g_cleanup()
    continueRoutine = False
'''


def add_param(parent: ET.Element, name: str, val: str, val_type: str = "str", updates: str = "None") -> None:
    ET.SubElement(parent, "Param", name=name, val=val, valType=val_type, updates=updates)


def routine_settings(routine: ET.Element, name: str) -> None:
    component = ET.SubElement(routine, "RoutineSettingsComponent", name=name, plugin="None")
    add_param(component, "backgroundFit", "none")
    add_param(component, "backgroundImg", "")
    add_param(component, "color", "$[1,1,1]", "color")
    add_param(component, "colorSpace", "rgb")
    add_param(component, "desc", "", updates="constant")
    add_param(component, "disabled", "False", "bool")
    add_param(component, "durationEstim", "", "code")
    add_param(component, "forceNonSlip", "False", "code")
    add_param(component, "name", name, "code")
    add_param(component, "saveStartStop", "True", "bool")
    add_param(component, "skipIf", "", "code", "constant")
    add_param(component, "stopType", "duration (s)")
    add_param(component, "stopVal", "", "code", "constant")
    add_param(component, "useWindowParams", "False", "bool")


def code_component(
    routine: ET.Element,
    name: str,
    begin_experiment: str = "",
    begin_routine: str = "",
    each_frame: str = "",
    end_routine: str = "",
) -> None:
    component = ET.SubElement(routine, "CodeComponent", name=name, plugin="None")
    add_param(component, "Before Experiment", "", "extendedCode", "constant")
    add_param(component, "Before JS Experiment", "", "extendedCode", "constant")
    add_param(component, "Begin Experiment", begin_experiment, "extendedCode", "constant")
    add_param(component, "Begin JS Experiment", "", "extendedCode", "constant")
    add_param(component, "Begin Routine", begin_routine, "extendedCode", "constant")
    add_param(component, "Code Type", "Py")
    add_param(component, "Each Frame", each_frame, "extendedCode", "constant")
    add_param(component, "Each JS Frame", "", "extendedCode", "constant")
    add_param(component, "End Experiment", "", "extendedCode", "constant")
    add_param(component, "End JS Experiment", "", "extendedCode", "constant")
    add_param(component, "End JS Routine", "", "extendedCode", "constant")
    add_param(component, "End Routine", end_routine, "extendedCode", "constant")
    add_param(component, "disabled", "False", "bool")
    add_param(component, "name", name, "code")


def keep_alive_image_component(routine: ET.Element, name: str) -> None:
    component = ET.SubElement(routine, "ImageComponent", name=name, plugin="None")
    add_param(component, "anchor", "center")
    add_param(component, "color", "$[1,1,1]", "color", "constant")
    add_param(component, "colorSpace", "rgb")
    add_param(component, "contrast", "1", "num", "constant")
    add_param(component, "disabled", "False", "bool")
    add_param(component, "draggable", "False", "code", "constant")
    add_param(component, "durationEstim", "", "code")
    add_param(component, "flipHoriz", "False", "bool", "constant")
    add_param(component, "flipVert", "False", "bool", "constant")
    add_param(component, "image", "Stimuli/sound.png", "file", "constant")
    add_param(component, "interpolate", "linear", "str", "constant")
    add_param(component, "mask", "", "str", "constant")
    add_param(component, "name", name, "code")
    add_param(component, "opacity", "0", "num", "constant")
    add_param(component, "ori", "0", "num", "constant")
    add_param(component, "pos", "(0, 0)", "list", "constant")
    add_param(component, "saveStartStop", "True", "bool")
    add_param(component, "size", "(0.01, 0.01)", "list", "constant")
    add_param(component, "startEstim", "", "code")
    add_param(component, "startType", "time (s)", "str")
    add_param(component, "startVal", "0.0", "code")
    add_param(component, "stopType", "duration (s)", "str")
    add_param(component, "stopVal", "", "code", "constant")
    add_param(component, "syncScreenRefresh", "True", "bool")
    add_param(component, "texture resolution", "128", "num", "constant")
    add_param(component, "units", "from exp settings", "str")
    add_param(component, "validator", "", "code")


def add_routine(routines: ET.Element, name: str, code_name: str, **code_parts: str) -> None:
    routine = ET.SubElement(routines, "Routine", name=name)
    routine_settings(routine, name)
    keep_alive_image_component(routine, f"{name}_keep_alive")
    code_component(routine, code_name, **code_parts)


def loop_initiator(flow: ET.Element, name: str, conditions_file: str, loop_type: str = "random") -> None:
    loop = ET.SubElement(flow, "LoopInitiator", loopType="TrialHandler", name=name)
    add_param(loop, "Selected rows", "")
    add_param(loop, "conditions", "None")
    add_param(loop, "conditionsFile", conditions_file, "file")
    add_param(loop, "endPoints", "[0, 1]", "num")
    add_param(loop, "isTrials", "True", "bool")
    add_param(loop, "loopType", loop_type)
    add_param(loop, "nReps", "1", "num")
    add_param(loop, "name", name, "code")
    add_param(loop, "random seed", "", "code")


def patch_settings(settings: ET.Element) -> None:
    legacy_eye_tracker_params = {
        "ecSampleRate",
        "elAddress",
        "elDataFiltering",
        "elLiveFiltering",
        "elModel",
        "elPupilAlgorithm",
        "elPupilMeasure",
        "elSampleRate",
        "elSimMode",
        "elTrackEyes",
        "elTrackingMode",
        "gpAddress",
        "gpPort",
        "plCompanionAddress",
        "plCompanionPort",
        "plConfidenceThreshold",
        "plPupilCaptureRecordingLocation",
        "plPupilRemoteAddress",
        "plPupilRemotePort",
        "plPupilRemoteTimeoutMs",
        "plPupillometryOnly",
        "plSurfaceName",
        "tbLicenseFile",
        "tbModel",
        "tbSampleRate",
        "tbSerialNo",
    }
    for param in list(settings.findall("Param")):
        if param.attrib.get("name") in legacy_eye_tracker_params:
            settings.remove(param)

    for param in settings.findall("Param"):
        name = param.attrib.get("name")
        if name == "expName":
            param.set("val", "discourse_part")
        elif name == "Experiment info":
            param.set(
                "val",
                "{'participant': 'f\"{randint(0, 999999):06.0f}\"', 'session': '001', 'list': '1', 'eeg_port': '', 'trigger_pulse_ms': '5'}",
            )
            param.set("valType", "code")
        elif name == "color":
            param.set("val", "$(1.0000, 1.0000, 1.0000)")
        elif name == "Data filename":
            param.set("val", "u'data/%s_%s_%s' % (expInfo['participant'], expName, expInfo['date'])")
        elif name == "Full-screen window":
            param.set("val", "True")
            param.set("valType", "bool")
        elif name == "Screen":
            param.set("val", "0")
            param.set("valType", "num")
        elif name == "Window size (pixels)":
            param.set("val", "(1200, 800)")
            param.set("valType", "list")


def build_psyexp(out_dir: Path, template: Path) -> Path:
    template_root = ET.parse(template).getroot()
    settings = template_root.find("Settings")
    if settings is None:
        raise ValueError(f"Template has no Settings: {template}")
    patch_settings(settings)

    root = ET.Element("PsychoPy2experiment", encoding="utf-8", version="2026.1.3")
    root.append(settings)
    routines = ET.SubElement(root, "Routines")
    add_routine(
        routines,
        "Instructions",
        "instructions_code",
        begin_experiment=SHARED_CODE,
        begin_routine=INSTRUCTIONS_BEGIN,
        each_frame=INSTRUCTIONS_EACH,
    )
    add_routine(
        routines,
        "PracticeTrial",
        "practice_trial_code",
        begin_routine=PRACTICE_BEGIN,
        each_frame=PRACTICE_EACH,
        end_routine=PRACTICE_END,
    )
    add_routine(
        routines,
        "PracticeEnd",
        "practice_end_code",
        begin_routine=PRACTICE_DONE_BEGIN,
        each_frame=PRACTICE_DONE_EACH,
    )
    add_routine(
        routines,
        "MainTrial",
        "main_trial_code",
        begin_routine=MAIN_BEGIN,
        each_frame=MAIN_EACH,
        end_routine=MAIN_END,
    )
    add_routine(routines, "Break", "break_code", begin_routine=BREAK_BEGIN, each_frame=BREAK_EACH)
    add_routine(routines, "EndExperiment", "end_code", begin_routine=END_BEGIN, each_frame=END_EACH)

    flow = ET.SubElement(root, "Flow")
    ET.SubElement(flow, "Routine", name="Instructions")
    loop_initiator(flow, "PracticeLoop", "Conds/practice.csv", loop_type="sequential")
    ET.SubElement(flow, "Routine", name="PracticeTrial")
    ET.SubElement(flow, "LoopTerminator", name="PracticeLoop")
    ET.SubElement(flow, "Routine", name="PracticeEnd")
    for block_index in range(1, 7):
        loop_initiator(flow, f"MainBlock{block_index}", f"$g_runtime_main_block_file({block_index})", loop_type="sequential")
        ET.SubElement(flow, "Routine", name="MainTrial")
        ET.SubElement(flow, "LoopTerminator", name=f"MainBlock{block_index}")
        if block_index < 6:
            ET.SubElement(flow, "Routine", name="Break")
    ET.SubElement(flow, "Routine", name="EndExperiment")

    ET.indent(root, space="  ")
    path = out_dir / "discourse_part.psyexp"
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
    return path


def write_readme(out_dir: Path, source_root: Path) -> None:
    text = f"""# Gurung PsychoPy Discourse Experiment

This is the Builder-compatible discourse experiment.

- Main picture stimuli are the committed JPEGs under `{JPEG_STIMULI_DIRNAME}/`.
- At the start dialog, choose experimental `list` 1 or 2. Each list has 240 picture-sequence trials.
- Trial order: practice runs in CSV order; the selected main list is shuffled at runtime on every run, then split into 40/40/40/40/40/40 for the breaks.
- Breaks: after trials 40, 80, 120, 160, and 200.
- Between-trial images: unique landscape photos sampled from `{BETWEEN_TRIALS_SOURCE}` and copied into `BetweenTrials/`; every actual Nepal-photo screen in practice and main draws from one shuffled no-repeat runtime pool. Speaker-icon instruction screens and the first main trial after each break do not consume a Nepal photo.
- Between-trial audio probes: 10% of main trials are selected at runtime; the four `Audio/new_disc_q_*.wav` questions each occur 6 times per 240-trial list; the first main Nepal screen after practice or any break can never be an audio-probe screen.
- EEG triggers are logged to `recordings/<participant>_l<list>_<date-time>/eeg_triggers.csv`. If `eeg_port` is filled in, the same trigger codes are also sent as single-byte serial pulses using `trigger_pulse_ms` as pulse duration.
- Discourse trigger codes: optional early pre-target picture 198, picture before target 199, target picture 200, condition 1-4 at 200 ms after target onset, item 1-120 at 400 ms after target onset, optional post-target picture 201, trial-end button press 202.
- Practice fixed audio probes: after practice sequence 2, the experiment plays `Audio/new_disc_instr2.wav` on the centered speaker-icon screen; after practice sequences 4, 7, and 10, it plays three of the `Audio/new_disc_q_*.wav` questions on Nepal-image screens.
- Speaker-icon audio screens can be replayed with Enter. On the first playback, Space advances only after the audio finishes; after an Enter replay, Space can advance immediately. The first instruction audio starts only after Space is pressed.
- Nepal-image audio probes are treated as listener questions: the audio plays first, then listener-response recording starts automatically; Space ends the response and advances only after at least 10 seconds of recording.
- Practice uses the numbered practice-story images in CSV order. Stories 1 and 2 start the matching `Audio/new_disc_orange_*.wav` and `Audio/new_disc_towel_*.wav` files simultaneously with pictures 1, 2, and 3; stories 3-10 play `Audio/new_disc_tsakyali.wav` before the last picture.
- Breaks show `Stimuli/break.png`; space is locked for 30 seconds.
- Main recordings are named with runtime main-trial number, list tag, image set, `cond`, and picture identifier.
- Practice recordings are named with participant, practice trial number, and picture number, for example `arrate_practice_08_pic02.wav`.
- Listener-response recordings are stored in `recordings/<participant>_l<list>_<date-time>/listener responses/`; filenames include the short question audio stem, for example `who`.
- Microphone recordings are stored in `recordings/<participant>_l<list>_<date-time>/` for each run.
- Each recordings folder now also contains a continuous raw `full_session.wav`, `recording_events.csv`, and `recording_segments.csv`. The old per-picture response WAV files are still written with the same names, but they are clipped from the continuous recording using logged picture-onset and space-press sample indices, with a 0.5-second post-space tail.
- All sequence pictures use the same on-screen size across 3- and 4-picture trials; each sequence row is group-centered with horizontal jitter capped at 30% of the picture width.

Open `discourse_part.psyexp` in PsychoPy Builder.

The main trial routine uses a Code Component because trials may contain either 3 or 4 images.
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


def build(args: argparse.Namespace) -> dict[str, object]:
    out_dir = Path(args.out).expanduser().resolve()
    source_root = Path(args.source_root).expanduser().resolve()
    old_dir = Path(args.old_dir).expanduser().resolve()
    template = Path(args.template).expanduser().resolve()

    preserved_dirs: dict[str, Path] = {}
    if out_dir.exists() and args.clean:
        preserve_root = Path(tempfile.mkdtemp(prefix="gurung_psychopy_preserve_"))
        for dirname in ("Audio", "data", "recordings", "Stimuli", JPEG_STIMULI_DIRNAME):
            source = out_dir / dirname
            if source.exists():
                target = preserve_root / dirname
                shutil.move(str(source), str(target))
                preserved_dirs[dirname] = target
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for dirname, source in preserved_dirs.items():
        shutil.move(str(source), str(out_dir / dirname))
    copy_assets(out_dir, old_dir)
    datasets = scan_jpeg_stimuli(out_dir / JPEG_STIMULI_DIRNAME)

    main_trials_per_list = len(datasets) * 4 * 2
    main_between_count = main_trials_per_list - MAIN_BREAK_COUNT
    required_between_count = PRACTICE_PHOTO_BETWEEN_COUNT + PRACTICE_EXTRA_BETWEEN_COUNT + main_between_count
    between_images = prepare_between_images(out_dir, required_between_count)
    main_rows_by_list = {
        list_id: build_main_rows(datasets, list_id)
        for list_id in sorted(LIST_RULES)
    }
    practice_rows = build_practice_rows([])
    conds = out_dir / "Conds"
    for list_id, main_rows in main_rows_by_list.items():
        write_csv(conds / f"main_list{list_id}_all_240.csv", main_rows, MAIN_FIELDS)
        for block_index in range(6):
            block_rows = main_rows[block_index * 40 : (block_index + 1) * 40]
            write_csv(conds / f"main_list{list_id}_block{block_index + 1}.csv", block_rows, MAIN_FIELDS)
    write_csv(conds / "practice.csv", practice_rows, PRACTICE_FIELDS)
    psyexp = build_psyexp(out_dir, template)
    write_readme(out_dir, source_root)

    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "out_dir": str(out_dir),
        "psyexp": str(psyexp),
        "jpeg_stimuli_root": str(out_dir / JPEG_STIMULI_DIRNAME),
        "random_seed": RANDOM_SEED,
        "main_trials_per_list": main_trials_per_list,
        "experimental_lists": sorted(LIST_RULES),
        "practice_trials": len(practice_rows),
        "runtime_audio_probe_trials_per_list": int(round(main_trials_per_list * AUDIO_PROBE_RATE)),
        "runtime_audio_probe_files": AUDIO_PROBE_FILES,
        "between_trial_images": len(between_images),
        "between_trial_source": str(BETWEEN_TRIALS_SOURCE),
        "between_trial_max_dimension": BETWEEN_TRIALS_MAX_DIMENSION,
        "jpeg_stimuli_images": len(datasets) * 4 * len(EXPECTED_IMAGES),
        "blocks_per_list": [40, 40, 40, 40, 40, 40],
    }
    (out_dir / "package_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="discourse part")
    parser.add_argument("--source-root", default=str(default_source_root()))
    parser.add_argument("--old-dir", default="old")
    parser.add_argument("--template", default="gurungfixed.psyexp")
    parser.add_argument("--clean", action="store_true")
    return parser.parse_args()


def main() -> None:
    print(json.dumps(build(parse_args()), indent=2))


if __name__ == "__main__":
    main()
