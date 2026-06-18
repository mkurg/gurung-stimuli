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
MAIN_FIELDS = [
    "trial_id",
    "random_order",
    "dataset_number",
    "dataset_slug",
    "dataset_label",
    "stimulus_set",
    "condition_id",
    "condition_name",
    "cohesion",
    "transitivity",
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
BETWEEN_TRIALS_SOURCE = Path("between_trials") / "Nepal 2025"
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
PRACTICE_EXTRA_BETWEEN_COUNT = 1
AUDIO_PROBE_FILES = [
    "Audio/tsakyali.wav",
    "Audio/bucketdog_noerg.wav",
    "Audio/chickencorn_erg.wav",
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


def copy_assets(out_dir: Path, old_dir: Path) -> None:
    audio_dir = out_dir / "Audio"
    stim_dir = out_dir / "Stimuli"
    placeholder_dir = out_dir / "Placeholders"
    audio_dir.mkdir(parents=True, exist_ok=True)
    stim_dir.mkdir(parents=True, exist_ok=True)
    placeholder_dir.mkdir(parents=True, exist_ok=True)

    for path in sorted((old_dir / "Audio").iterdir(), key=lambda item: item.name):
        if path.is_file():
            shutil.copy2(path, audio_dir / path.name)

    for audio_value in AUDIO_PROBE_FILES:
        audio_path = audio_dir / Path(audio_value).name
        if not audio_path.is_file():
            print(f"Warning: audio probe file missing from package: {audio_path}")

    for path in sorted((old_dir / "old_stimuli").iterdir(), key=lambda item: item.name):
        if path.is_file():
            shutil.copy2(path, stim_dir / path.name)

    probe_source = audio_dir / "tsakyali.wav"
    if probe_source.is_file():
        shutil.copy2(probe_source, audio_dir / "probe_placeholder.wav")

    placeholder_source = stim_dir / "break.png"
    for index in range(1, 121):
        shutil.copy2(placeholder_source, placeholder_dir / f"between_{index:03d}.png")


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


def copy_main_stimuli(out_dir: Path, datasets: list[dict[str, object]]) -> dict[tuple[int, str], str]:
    main_dir = out_dir / "MainStimuli"
    manifest_rows: list[dict[str, str]] = []
    relative_paths: dict[tuple[int, str], str] = {}
    for dataset in datasets:
        number = int(dataset["number"])
        slug = str(dataset["slug"])
        label = str(dataset["label"])
        set_folder = Path(dataset["set_folder"])
        target_dir = main_dir / slug
        for stem in EXPECTED_IMAGES:
            source = set_folder / f"{stem}.png"
            target = target_dir / f"{stem}.png"
            copy_or_downsample_image(source, target, MAIN_STIMULI_MAX_DIMENSION)
            relative_path = f"MainStimuli/{slug}/{stem}.png"
            relative_paths[(number, stem)] = relative_path
            manifest_rows.append(
                {
                    "dataset_number": str(number),
                    "dataset_slug": slug,
                    "dataset_label": label,
                    "image_role": stem,
                    "package_path": relative_path,
                    "source_path": str(source),
                }
            )

    manifest_path = main_dir / "main_stimuli_manifest.csv"
    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "dataset_number",
                "dataset_slug",
                "dataset_label",
                "image_role",
                "package_path",
                "source_path",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(manifest_rows)
    return relative_paths


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
    between_images: list[str],
    main_stimuli: dict[tuple[int, str], str],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for dataset in datasets:
        number = int(dataset["number"])
        label = str(dataset["label"])
        for condition_id, condition_name, cohesion, transitivity, steps in TRIAL_PATHS:
            row = {
                "trial_id": f"d{number:03d}_set1_{condition_id}",
                "random_order": "",
                "dataset_number": str(number),
                "dataset_slug": str(dataset["slug"]),
                "dataset_label": label.replace(" ", "_"),
                "stimulus_set": "1",
                "condition_id": condition_id,
                "condition_name": condition_name,
                "cohesion": cohesion,
                "transitivity": transitivity,
                "n_images": str(len(steps)),
                "between_image": "",
                "audio_probe": "0",
                "between_audio": "",
                "between_audio_lock_sec": "0",
                "source_dataset_folder": str(dataset["folder"]),
            }
            for index in range(1, 5):
                row[f"img{index}"] = ""
                row[f"img{index}_role"] = ""
            for index, stem in enumerate(steps, start=1):
                row[f"img{index}"] = main_stimuli[(number, stem)]
                row[f"img{index}_role"] = stem
            rows.append(row)

    rng = random.Random(RANDOM_SEED)
    rng.shuffle(rows)
    if len(between_images) < len(rows):
        raise ValueError(f"Need {len(rows)} unique main between-trial images, got {len(between_images)}")
    for index, (row, between_image) in enumerate(zip(rows, between_images), start=1):
        row["random_order"] = str(index)
        row["between_image"] = between_image
    return rows


def build_practice_rows(between_images: list[str]) -> list[dict[str, str]]:
    if len(between_images) < PRACTICE_TRIAL_COUNT:
        raise ValueError(f"Need {PRACTICE_TRIAL_COUNT} unique practice between-trial images, got {len(between_images)}")
    rows: list[dict[str, str]] = []
    for index, (story_slug, image_count) in enumerate(PRACTICE_STORIES, start=1):
        row = {
            "trial_id": f"practice_{index:02d}",
            "n_images": str(image_count),
            "between_image": between_images[index - 1],
        }
        for image_index in range(1, 5):
            if image_index <= image_count:
                row[f"img{image_index}"] = (
                    f"Stimuli/practice_{index:02d}_pic{image_index:02d}_{story_slug}.png"
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
G_SEQUENCE_JITTER_POSITIONS = (
    (-0.035, -0.018),
    (-0.012, -0.018),
    (0.012, -0.018),
    (0.035, -0.018),
    (-0.035, 0.018),
    (-0.012, 0.018),
    (0.012, 0.018),
    (0.035, 0.018),
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
G_AUDIO_PROBE_FILES = (
    "Audio/tsakyali.wav",
    "Audio/bucketdog_noerg.wav",
    "Audio/chickencorn_erg.wav",
)
G_AUDIO_PROBE_RATE = 0.10
G_AUDIO_PROBE_LOCK_SEC = 10
G_MAIN_BLOCK_SIZE = 40
G_PRACTICE_TRIAL_COUNT = 10
G_PRACTICE_PICTURE_AUDIO = {
    1: {
        0: "Audio/tsakyali.wav",
        1: "Audio/bucketdog_noerg.wav",
        2: "Audio/chickencorn_erg.wav",
    },
    2: {
        0: "Audio/tsakyali.wav",
        1: "Audio/bucketdog_noerg.wav",
        2: "Audio/chickencorn_erg.wav",
    },
}
G_PRACTICE_AFTER_TRIAL_AUDIO = {
    4: "Audio/tsakyali.wav",
    7: "Audio/bucketdog_noerg.wav",
    10: "Audio/chickencorn_erg.wav",
}


def g_log(message):
    text = f"{core.getTime():.3f} {message}"
    print(text)
    try:
        with G_DEBUG_LOG.open("a", encoding="utf-8") as handle:
            handle.write(text + "\n")
    except Exception:
        pass

try:
    event.globalKeys.add(key="escape", func=core.quit, name="gurung_escape_quit")
except Exception as _gurung_global_key_error:
    g_log(f"Global escape key was not registered: {_gurung_global_key_error}")


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


def g_practice_picture_audio(trial_index, segment_index):
    trial_audio = G_PRACTICE_PICTURE_AUDIO.get(trial_index, {})
    return trial_audio.get(segment_index, "")


def g_practice_pre_picture_audio(trial_index, segment_index, image_count):
    if trial_index not in G_PRACTICE_PICTURE_AUDIO and segment_index == image_count - 1:
        return "Audio/tsakyali.wav"
    return ""


def g_int(value, default=0):
    if g_is_blank(value):
        return default
    try:
        return int(float(value))
    except Exception:
        return default


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


def g_release_fullscreen_image(stim):
    g_release_stims([stim])
    if G_FULLSCREEN_CACHE.get("stim") is stim:
        G_FULLSCREEN_CACHE["stim"] = None


def g_init_between_images():
    between_dir = G_ROOT / "BetweenTrials"
    practice_images = set()
    try:
        for row in data.importConditions("Conds/practice.csv"):
            image_value = g_text(row.get("between_image", "")).replace("\\", "/")
            if image_value:
                practice_images.add(image_value)
    except Exception as err:
        g_log(f"Could not reserve practice between-trial images: {err}")
    images = []
    try:
        for path in sorted(between_dir.iterdir()):
            if path.is_file() and path.suffix.lower() in G_BETWEEN_IMAGE_EXTS:
                image_value = f"BetweenTrials/{path.name}"
                if image_value not in practice_images:
                    images.append(image_value)
    except Exception as err:
        raise RuntimeError(f"Could not list between-trial images in {between_dir}: {err}")
    if not images:
        raise RuntimeError(f"No between-trial images found in {between_dir}")
    _gurung_random.shuffle(images)
    G_BETWEEN_STATE["images"] = images
    G_BETWEEN_STATE["index"] = 0
    g_log(f"runtime_between_images_shuffled count={len(images)} reserved_practice={len(practice_images)}")


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
    rows = list(data.importConditions("Conds/main_all_120.csv"))
    if not rows:
        raise RuntimeError("No main trials found in Conds/main_all_120.csv")
    _gurung_random.shuffle(rows)
    g_assign_runtime_audio_probes(rows)
    fieldnames = list(rows[0].keys())
    block_files = []
    block_sizes = []
    for block_index in range(3):
        block_rows = rows[block_index * 40 : (block_index + 1) * 40]
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
    g_log(f"runtime_main_sequences_shuffled count={len(rows)} block_sizes={block_sizes}")


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
    if SpeakerDevice is None:
        return None
    try:
        devices = SpeakerDevice.getAvailableDevices()
    except Exception as err:
        g_log(f"Could not list speaker devices: {err}")
        return None
    names = [g_text(device.get("deviceName") or device.get("name")) for device in devices]
    g_log(f"Available speaker devices: {names}")
    virtual_terms = ("blackhole", "soundflower", "loopback", "aggregate", "zoom", "teams")
    preferred = []
    fallback = []
    for device in devices:
        name = g_text(device.get("deviceName") or device.get("name"))
        if not name:
            continue
        if any(term in name.lower() for term in virtual_terms):
            fallback.append(name)
        else:
            preferred.append(name)
    for name in preferred + fallback:
        try:
            speaker = SpeakerDevice(name=name, latencyClass=0)
            g_log(f"Using speaker device: {speaker.name}")
            return speaker
        except Exception as err:
            g_log(f"Could not open speaker {name!r}: {err}")
    g_log("No usable speaker found; PsychoPy will use its default audio device.")
    return None


G_SPEAKER = g_choose_speaker()
g_init_between_images()
g_prepare_runtime_main_blocks()


def g_safe(value):
    text = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in str(value))
    while "__" in text:
        text = text.replace("__", "_")
    return text.strip("._") or "item"


def g_session_recordings_dir():
    participant = g_safe(expInfo.get("participant", "participant"))
    date_value = g_safe(expInfo.get("date") or expInfo.get("date|hid") or data.getDateStr())
    folder = G_RECORDINGS_ROOT / f"{participant}_{date_value}"
    folder.mkdir(parents=True, exist_ok=True)
    expInfo["recordings_dir"] = str(folder)
    g_log(f"recordings_dir {folder}")
    return folder


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
        bag = list(G_SEQUENCE_JITTER_POSITIONS)
        _gurung_random.shuffle(bag)
        G_SEQUENCE_JITTER_STATE["bag"] = bag
    return bag.pop()


def g_sequence_layout(win, roles):
    sequence_count = max(1, len(roles))
    size_count = max(G_SEQUENCE_SIZE_COUNT, sequence_count)
    jitter_x_max = max(abs(pos[0]) for pos in G_SEQUENCE_JITTER_POSITIONS)
    jitter_y_max = max(abs(pos[1]) for pos in G_SEQUENCE_JITTER_POSITIONS)
    horizontal_room = max(0.1, g_window_aspect(win) - (2 * (G_SEQUENCE_X_MARGIN + jitter_x_max)))
    vertical_room = max(0.1, 1.0 - (2 * (G_SEQUENCE_Y_MARGIN + jitter_y_max)))
    width_from_horizontal = horizontal_room / (size_count + ((size_count - 1) * G_SEQUENCE_GAP_RATIO))
    image_height = min(vertical_room, width_from_horizontal / G_IMAGE_ASPECT)
    image_width = image_height * G_IMAGE_ASPECT
    gap = image_width * G_SEQUENCE_GAP_RATIO
    step = image_width + gap
    row_center = (len(roles) - 1) / 2.0
    jitter_x, jitter_y = g_next_sequence_jitter()
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
    if G_SPEAKER is not None:
        audio = sound.Sound(path, speaker=G_SPEAKER)
    else:
        audio = sound.Sound(path)
    audio.play()
    return audio


class GRecorder:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(exist_ok=True)
        self.stream = None
        self.frames = []
        self.path = None
        self.write_queue = queue.Queue()
        self.writer = threading.Thread(target=self._writer_loop, daemon=True)
        self.writer.start()

    def start(self, stem):
        self.stop()
        if not G_RECORDING_AVAILABLE:
            return ""
        self._ensure_stream()
        self.frames = []
        self.path = self.root / f"{g_safe(stem)}.wav"
        g_log(f"rec_segment_start {self.path}")
        return str(self.path)

    def _ensure_stream(self):
        if self.stream is not None:
            return

        def callback(indata, frames, time_info, status):
            if status:
                g_log(f"rec_callback_status {status}")
            if self.path is not None:
                self.frames.append(indata.copy())

        g_log("rec_stream_open_start")
        self.stream = _gurung_sd.InputStream(
            samplerate=48000,
            channels=1,
            dtype="float32",
            callback=callback,
        )
        self.stream.start()
        g_log("rec_stream_open_done")

    def stop(self):
        path = self.path
        frames = self.frames
        self.path = None
        self.frames = []
        if path and frames:
            g_log(f"rec_segment_queue_write {path} frames={len(frames)}")
            self.write_queue.put((str(path), frames))
            return str(path)
        return ""

    def _writer_loop(self):
        while True:
            item = self.write_queue.get()
            if item is None:
                return
            path, frames = item
            try:
                audio = _gurung_np.concatenate(frames, axis=0)
                _gurung_sf.write(path, audio, 48000)
                g_log(f"rec_segment_written {path}")
            except Exception as err:
                g_log(f"rec_segment_write_failed {path}: {err}")

    def abort(self):
        self.stop()
        stream = self.stream
        self.stream = None
        if stream is not None:
            def close_stream():
                try:
                    g_log("rec_stream_abort_start")
                    stream.abort()
                    g_log("rec_stream_abort_done")
                except Exception as err:
                    g_log(f"rec_stream_abort_failed {err}")
                try:
                    stream.close()
                    g_log("rec_stream_close_done")
                except Exception as err:
                    g_log(f"rec_stream_close_failed {err}")

            threading.Thread(target=close_stream, daemon=True).start()


def g_cleanup():
    try:
        G_RECORDER.abort()
    except Exception as err:
        g_log(f"Recorder cleanup failed: {err}")
    try:
        if G_SPEAKER is not None:
            G_SPEAKER.close()
    except Exception as err:
        g_log(f"Speaker cleanup failed: {err}")


G_RECORDINGS_DIR = g_session_recordings_dir()
G_RECORDER = GRecorder(G_RECORDINGS_DIR)
'''


INSTRUCTIONS_BEGIN = r'''
win.color = "white"
instruction_icon = visual.ImageStim(win, image=g_path("Stimuli/sound.png"), pos=(0, 0), size=(0.22, 0.22), interpolate=True)
instruction_audio = g_play_audio("Audio/sequence_instr.wav")
event.clearEvents()
'''

INSTRUCTIONS_EACH = r'''
instruction_icon.draw()
keys = event.getKeys(keyList=["space", "return", "escape"])
if "escape" in keys:
    core.quit()
if "return" in keys:
    if instruction_audio:
        instruction_audio.stop()
    instruction_audio = g_play_audio("Audio/sequence_instr.wav")
if "space" in keys:
    if instruction_audio:
        instruction_audio.stop()
    continueRoutine = False
'''

PRACTICE_BEGIN = r'''
G_PRACTICE_TRIAL_INDEX += 1
win.color = "white"
practice_between_image = g_text(globals().get("between_image", "")) or g_next_between_image()
practice_placeholder = g_fullscreen_image(win, practice_between_image)
practice_roles, practice_paths = g_roles_and_paths()
practice_images = []
practice_arrows = []
practice_segment = 0
practice_phase = "between"
practice_between_clock = core.Clock()
practice_between_audio = None
practice_between_audio_value = g_text(G_PRACTICE_AFTER_TRIAL_AUDIO.get(G_PRACTICE_TRIAL_INDEX - 1, ""))
practice_between_audio_lock = G_AUDIO_PROBE_LOCK_SEC if practice_between_audio_value else 0.0
practice_after_placeholder = None
practice_after_between_image = ""
practice_after_between_clock = core.Clock()
practice_after_between_lock = 0.0
practice_audio = None
practice_audio_value = ""
practice_audio_clock = core.Clock()
practice_audio_duration = 0
practice_segment_audio_value = ""
practice_segment_audio_started = False
practice_segment_audio_lock = 0.0
if practice_between_audio_value:
    practice_between_audio = g_play_audio(practice_between_audio_value)
practice_between_clock.reset()
thisExp.addData("practice_trial_index", G_PRACTICE_TRIAL_INDEX)
thisExp.addData("practice_between_image", g_path(practice_between_image))
thisExp.addData("practice_between_audio", g_path(practice_between_audio_value) if practice_between_audio_value else "")
event.clearEvents()
'''

PRACTICE_EACH = r'''
if practice_phase == "between":
    practice_placeholder.draw()
    keys = event.getKeys(keyList=["space", "escape"])
    if "escape" in keys:
        G_RECORDER.abort()
        core.quit()
    if "space" in keys and practice_between_clock.getTime() >= practice_between_audio_lock:
        if practice_between_audio:
            practice_between_audio.stop()
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
            practice_stem = f"{expInfo['participant']}_practice_{G_PRACTICE_TRIAL_INDEX:02d}_pic{practice_segment + 1:02d}_{practice_roles[practice_segment]}"
            G_RECORDER.start(practice_stem)
        event.clearEvents()
elif practice_phase == "segment":
    g_draw_sequence(practice_images, practice_arrows, practice_segment + 1)
    if practice_segment_audio_value and not practice_segment_audio_started:
        practice_audio_value = practice_segment_audio_value
        practice_audio = g_play_audio(practice_audio_value)
        practice_audio_clock.reset()
        practice_segment_audio_lock = g_float(practice_audio.getDuration(), 0) if practice_audio else 0
        practice_segment_audio_started = True
        thisExp.addData(f"practice_seg{practice_segment + 1}_onset_audio", g_path(practice_audio_value))
    keys = event.getKeys(keyList=["space", "escape"])
    if "escape" in keys:
        G_RECORDER.abort()
        core.quit()
    if "space" in keys and practice_audio_clock.getTime() >= practice_segment_audio_lock:
        if practice_audio:
            practice_audio.stop()
        practice_audio = None
        audio_file = G_RECORDER.stop()
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
                practice_after_between_clock.reset()
                practice_after_between_lock = G_AUDIO_PROBE_LOCK_SEC
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
                practice_stem = f"{expInfo['participant']}_practice_{G_PRACTICE_TRIAL_INDEX:02d}_pic{practice_segment + 1:02d}_{practice_roles[practice_segment]}"
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
        practice_stem = f"{expInfo['participant']}_practice_{G_PRACTICE_TRIAL_INDEX:02d}_pic{practice_segment + 1:02d}_{practice_roles[practice_segment]}"
        G_RECORDER.start(practice_stem)
        event.clearEvents()
elif practice_phase == "practice_after_between":
    practice_after_placeholder.draw()
    keys = event.getKeys(keyList=["space", "escape"])
    if "escape" in keys:
        G_RECORDER.abort()
        core.quit()
    if "space" in keys and practice_after_between_clock.getTime() >= practice_after_between_lock:
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
practice_done_audio = g_play_audio("Audio/practice_end.wav")
practice_done_clock = core.Clock()
practice_done_duration = g_float(practice_done_audio.getDuration() if practice_done_audio else 0, 0.0)
event.clearEvents()
'''

PRACTICE_DONE_EACH = r'''
practice_done_icon.draw()
keys = event.getKeys(keyList=["space", "escape"])
if "escape" in keys:
    core.quit()
if "space" in keys and practice_done_clock.getTime() >= practice_done_duration:
    if practice_done_audio:
        practice_done_audio.stop()
    continueRoutine = False
'''

MAIN_BEGIN = r'''
G_MAIN_TRIAL_INDEX += 1
win.color = "white"
main_between_image = g_next_between_image()
main_placeholder = g_fullscreen_image(win, main_between_image)
main_roles, main_paths = g_roles_and_paths()
main_images = []
main_arrows = []
main_segment = 0
main_phase = "between"
main_between_clock = core.Clock()
main_between_audio = None
main_between_audio_value = g_text(globals().get("between_audio", ""))
main_audio_lock = g_float(globals().get("between_audio_lock_sec", 0), 0.0)
main_dataset_number = g_int(globals().get("dataset_number", 0), 0)
main_condition_id = g_text(globals().get("condition_id", "unknown_condition"))
if main_between_audio_value:
    main_between_audio = g_play_audio(main_between_audio_value)
main_between_clock.reset()
thisExp.addData("main_trial_index", G_MAIN_TRIAL_INDEX)
thisExp.addData("between_image", g_path(main_between_image))
thisExp.addData("audio_probe", audio_probe)
thisExp.addData("between_audio", g_path(main_between_audio_value) if main_between_audio_value else "")
event.clearEvents()
'''

MAIN_EACH = r'''
if main_phase == "between":
    main_placeholder.draw()
    keys = event.getKeys(keyList=["space", "escape"])
    if "escape" in keys:
        G_RECORDER.abort()
        core.quit()
    if "space" in keys and main_between_clock.getTime() >= main_audio_lock:
        if main_between_audio:
            main_between_audio.stop()
        thisExp.addData("between_rt", main_between_clock.getTime())
        g_release_fullscreen_image(main_placeholder)
        main_placeholder = None
        main_images, main_arrows = g_make_sequence(win, main_roles, main_paths)
        main_phase = "segment"
        main_stem = f"{expInfo['participant']}_main_imageset{main_dataset_number:02d}_condition_{main_condition_id}_pic{main_segment + 1:02d}_{main_roles[main_segment]}"
        G_RECORDER.start(main_stem)
        event.clearEvents()
elif main_phase == "segment":
    g_draw_sequence(main_images, main_arrows, main_segment + 1)
    keys = event.getKeys(keyList=["space", "escape"])
    if "escape" in keys:
        G_RECORDER.abort()
        core.quit()
    if "space" in keys:
        audio_file = G_RECORDER.stop()
        seg = main_segment + 1
        thisExp.addData(f"seg{seg}_role", main_roles[main_segment])
        thisExp.addData(f"seg{seg}_audio", audio_file)
        if main_segment >= len(main_images) - 1:
            continueRoutine = False
        else:
            main_segment += 1
            main_stem = f"{expInfo['participant']}_main_imageset{main_dataset_number:02d}_condition_{main_condition_id}_pic{main_segment + 1:02d}_{main_roles[main_segment]}"
            G_RECORDER.start(main_stem)
        event.clearEvents()
'''

MAIN_END = r'''
G_RECORDER.stop()
if main_between_audio:
    main_between_audio.stop()
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
    core.quit()
if "space" in keys and break_clock.getTime() >= 30:
    continueRoutine = False
'''

END_BEGIN = r'''
win.color = "white"
finish_image = visual.ImageStim(win, image=g_path("Stimuli/finish.png"), pos=(0, 0), size=(0.55, 0.55), interpolate=True)
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
            param.set("val", "gurung_120_v1")
        elif name == "Experiment info":
            param.set("val", "{'participant': 'f\"{randint(0, 999999):06.0f}\"', 'session': '001'}")
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
    loop_initiator(flow, "MainBlock1", "$g_runtime_main_block_file(1)", loop_type="sequential")
    ET.SubElement(flow, "Routine", name="MainTrial")
    ET.SubElement(flow, "LoopTerminator", name="MainBlock1")
    ET.SubElement(flow, "Routine", name="Break")
    loop_initiator(flow, "MainBlock2", "$g_runtime_main_block_file(2)", loop_type="sequential")
    ET.SubElement(flow, "Routine", name="MainTrial")
    ET.SubElement(flow, "LoopTerminator", name="MainBlock2")
    ET.SubElement(flow, "Routine", name="Break")
    loop_initiator(flow, "MainBlock3", "$g_runtime_main_block_file(3)", loop_type="sequential")
    ET.SubElement(flow, "Routine", name="MainTrial")
    ET.SubElement(flow, "LoopTerminator", name="MainBlock3")
    ET.SubElement(flow, "Routine", name="EndExperiment")

    ET.indent(root, space="  ")
    path = out_dir / "gurung_120_v1.psyexp"
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
    return path


def write_readme(out_dir: Path, source_root: Path) -> None:
    text = f"""# Gurung PsychoPy 120-Trial First Draft

This is a first Builder-compatible draft based on the design described on 2026-06-06.

- Stimulus source: set/folder `1` from the Gurung trial viewer data.
- Main trials: 30 datasets x 4 conditions = 120 trials.
- Trial order: practice runs in CSV order; main picture sequences are shuffled as one 120-trial list at runtime, then split into 40/40/40 for the breaks.
- Breaks: after trials 40 and 80.
- Between-trial images: unique landscape photos sampled from `{BETWEEN_TRIALS_SOURCE}` and copied into `BetweenTrials/`; practice uses its assigned CSV images, the extra practice-end probe uses one more Nepal image, and main images are shuffled at runtime without reusing practice images.
- Between-trial audio probes: 10% of main trials are selected at runtime; `Audio/tsakyali.wav`, `Audio/bucketdog_noerg.wav`, and `Audio/chickencorn_erg.wav` each occur on one third of those trials; lockout is 10 seconds; the first main Nepal screen after practice or any break can never be an audio-probe screen.
- Practice fixed audio probes: after practice sequences 4, 7, and 10, the experiment plays `Audio/tsakyali.wav`, `Audio/bucketdog_noerg.wav`, and `Audio/chickencorn_erg.wav`, respectively, on Nepal-image screens with the same 10-second lock as main probes.
- Practice uses the numbered practice-story images in CSV order. Stories 1 and 2 start `Audio/tsakyali.wav`, `Audio/bucketdog_noerg.wav`, and `Audio/chickencorn_erg.wav` simultaneously with pictures 1, 2, and 3; stories 3-10 play `Audio/tsakyali.wav` before the last picture.
- Breaks show `Stimuli/break.png`; space is locked for 30 seconds.
- Main recordings are named with image set, condition, and picture identifier.
- Practice recordings are named with practice trial number and picture number.
- Microphone recordings are stored in `recordings/<participant>_<date-time>/` for each run.
- Main PNGs are local packaged copies in `MainStimuli/`, downsampled to max `{MAIN_STIMULI_MAX_DIMENSION}px on the long edge. This avoids loading trial textures from the Google Drive cloud-storage mount during the run.
- All sequence pictures use the same on-screen size across 3- and 4-picture trials; each sequence row is group-centered with a small randomized horizontal and vertical jitter.

Open `gurung_120_v1.psyexp` in PsychoPy Builder.

Source root used:

```text
{source_root}
```

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
        for dirname in ("Audio", "data", "recordings"):
            source = out_dir / dirname
            if source.exists():
                target = preserve_root / dirname
                shutil.move(str(source), str(target))
                preserved_dirs[dirname] = target
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for dirname, source in preserved_dirs.items():
        shutil.move(str(source), str(out_dir / dirname))
    datasets = scan_dataset_set1(source_root)
    copy_assets(out_dir, old_dir)
    main_stimuli = copy_main_stimuli(out_dir, datasets)

    required_between_count = PRACTICE_TRIAL_COUNT + PRACTICE_EXTRA_BETWEEN_COUNT + (len(datasets) * len(TRIAL_PATHS))
    between_images = prepare_between_images(out_dir, required_between_count)
    practice_between_images = between_images[:PRACTICE_TRIAL_COUNT]
    main_between_images = between_images[PRACTICE_TRIAL_COUNT:]
    main_rows = build_main_rows(datasets, main_between_images, main_stimuli)
    practice_rows = build_practice_rows(practice_between_images)
    conds = out_dir / "Conds"
    write_csv(conds / "main_all_120.csv", main_rows, MAIN_FIELDS)
    for block_index in range(3):
        block_rows = main_rows[block_index * 40 : (block_index + 1) * 40]
        write_csv(conds / f"main_block{block_index + 1}.csv", block_rows, MAIN_FIELDS)
    write_csv(conds / "practice.csv", practice_rows, PRACTICE_FIELDS)
    psyexp = build_psyexp(out_dir, template)
    write_readme(out_dir, source_root)

    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "out_dir": str(out_dir),
        "psyexp": str(psyexp),
        "source_root": str(source_root),
        "random_seed": RANDOM_SEED,
        "main_trials": len(main_rows),
        "practice_trials": len(practice_rows),
        "runtime_audio_probe_trials": int(round(len(main_rows) * AUDIO_PROBE_RATE)),
        "runtime_audio_probe_files": AUDIO_PROBE_FILES,
        "between_trial_images": len(between_images),
        "between_trial_source": str(BETWEEN_TRIALS_SOURCE),
        "between_trial_max_dimension": BETWEEN_TRIALS_MAX_DIMENSION,
        "main_stimuli_images": len(main_stimuli),
        "main_stimuli_max_dimension": MAIN_STIMULI_MAX_DIMENSION,
        "blocks": [40, 40, 40],
    }
    (out_dir / "package_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="psychopy_gurung_v1")
    parser.add_argument("--source-root", default=str(default_source_root()))
    parser.add_argument("--old-dir", default="old")
    parser.add_argument("--template", default="gurungfixed.psyexp")
    parser.add_argument("--clean", action="store_true")
    return parser.parse_args()


def main() -> None:
    print(json.dumps(build(parse_args()), indent=2))


if __name__ == "__main__":
    main()
