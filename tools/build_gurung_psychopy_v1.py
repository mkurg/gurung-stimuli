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
    between_dir = out_dir / "BetweenTrials"
    audio_dir.mkdir(parents=True, exist_ok=True)
    stim_dir.mkdir(parents=True, exist_ok=True)
    placeholder_dir.mkdir(parents=True, exist_ok=True)
    between_dir.mkdir(parents=True, exist_ok=True)

    for path in sorted((old_dir / "Audio").iterdir(), key=lambda item: item.name):
        if path.is_file():
            shutil.copy2(path, audio_dir / path.name)

    for path in sorted((old_dir / "old_stimuli").iterdir(), key=lambda item: item.name):
        if path.is_file():
            shutil.copy2(path, stim_dir / path.name)

    probe_source = audio_dir / "tsakyali.wav"
    if probe_source.is_file():
        shutil.copy2(probe_source, audio_dir / "probe_placeholder.wav")

    placeholder_source = stim_dir / "break.png"
    for index in range(1, 121):
        shutil.copy2(placeholder_source, placeholder_dir / f"between_{index:03d}.png")

    source_between = Path("between_trials")
    if source_between.is_dir():
        for path in sorted(source_between.iterdir(), key=lambda item: natural_key(item.name)):
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
                target = between_dir / f"{slugify(path.stem)}{path.suffix.lower()}"
                try:
                    subprocess.run(
                        ["sips", "-Z", "1920", str(path), "--out", str(target)],
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                except Exception:
                    shutil.copy2(path, target)


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
        )
        writer.writeheader()
        writer.writerows(manifest_rows)
    return relative_paths


def list_between_images(out_dir: Path) -> list[str]:
    between_dir = out_dir / "BetweenTrials"
    images = [
        f"BetweenTrials/{path.name}"
        for path in sorted(between_dir.iterdir(), key=lambda item: natural_key(item.name))
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    ]
    if not images:
        return [f"Placeholders/between_{index:03d}.png" for index in range(1, 121)]
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
    probe_indices = set(rng.sample(range(len(rows)), 12))
    for index, row in enumerate(rows, start=1):
        row["random_order"] = str(index)
        row["between_image"] = rng.choice(between_images)
        if index - 1 in probe_indices:
            row["audio_probe"] = "1"
            row["between_audio"] = "Audio/tsakyali.wav"
            row["between_audio_lock_sec"] = "10"
    return rows


def build_practice_rows(between_images: list[str]) -> list[dict[str, str]]:
    rng = random.Random(RANDOM_SEED + 1)
    rows: list[dict[str, str]] = []
    for index in range(1, 9):
        row = {
            "trial_id": f"practice_{index:02d}",
            "n_images": "3",
            "img1": f"Stimuli/pr{index}_1.png",
            "img1_role": "practice_1",
            "img2": f"Stimuli/pr{index}_2.png",
            "img2_role": "practice_2",
            "img3": f"Stimuli/pr{index}_3.png",
            "img3_role": "practice_3",
            "img4": "",
            "img4_role": "",
            "between_image": rng.choice(between_images),
        }
        rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


SHARED_CODE = r'''
from pathlib import Path
import gc
import queue
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

G_ROOT = Path(_thisDir)
G_DATA_DIR = G_ROOT / "data"
G_RECORDINGS_DIR = G_ROOT / "recordings"
G_DEBUG_LOG = G_ROOT / "debug_gurung_runtime.log"
G_DATA_DIR.mkdir(exist_ok=True)
G_RECORDINGS_DIR.mkdir(exist_ok=True)
G_IMAGE_SIZE = (0.22, 0.35)
G_ARROW_SIZE = (0.035, 0.035)
G_STEP = 0.27
G_MAIN_TRIAL_INDEX = 0
G_PRACTICE_TRIAL_INDEX = 0
G_SPEAKER = None
G_FULLSCREEN_CACHE = {}


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


def g_fullscreen_size(win):
    try:
        return (float(win.size[0]) / float(win.size[1]), 1.0)
    except Exception:
        return (1.5, 1.0)


def g_fullscreen_image(win, image_value):
    path = g_path(image_value)
    stim = G_FULLSCREEN_CACHE.get(path)
    if stim is None:
        g_log(f"load_fullscreen_image {path}")
        stim = visual.ImageStim(
            win,
            image=path,
            pos=(0, 0),
            size=g_fullscreen_size(win),
            interpolate=True,
        )
        G_FULLSCREEN_CACHE[path] = stim
    return stim


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


def g_safe(value):
    text = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in str(value))
    while "__" in text:
        text = text.replace("__", "_")
    return text.strip("._") or "item"


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


def g_positions_for_roles(roles):
    target_index = None
    for target_role in ("tr_target", "it_target"):
        if target_role in roles:
            target_index = roles.index(target_role)
            break
    if target_index is None:
        target_index = (len(roles) - 1) / 2
    return [((idx - target_index) * G_STEP, 0) for idx in range(len(roles))]


def g_make_sequence(win, roles, paths):
    g_log(f"make_sequence roles={roles} paths={paths}")
    positions = g_positions_for_roles(roles)
    images = []
    for path, pos in zip(paths, positions):
        images.append(visual.ImageStim(win, image=path, pos=pos, size=G_IMAGE_SIZE, interpolate=True))
    arrows = []
    arrow_path = g_path("Stimuli/arrow.png")
    for left, right in zip(positions, positions[1:]):
        arrows.append(
            visual.ImageStim(
                win,
                image=arrow_path,
                pos=((left[0] + right[0]) / 2, 0),
                size=G_ARROW_SIZE,
                interpolate=True,
            )
        )
    return images, arrows


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
practice_roles, practice_paths = g_roles_and_paths()
practice_images, practice_arrows = g_make_sequence(win, practice_roles, practice_paths)
practice_segment = 0
practice_phase = "between"
practice_placeholder = g_fullscreen_image(win, between_image)
practice_between_clock = core.Clock()
practice_audio = None
practice_audio_clock = core.Clock()
practice_audio_duration = 0
thisExp.addData("practice_trial_index", G_PRACTICE_TRIAL_INDEX)
thisExp.addData("practice_between_image", g_path(between_image))
event.clearEvents()
'''

PRACTICE_EACH = r'''
if practice_phase == "between":
    practice_placeholder.draw()
    keys = event.getKeys(keyList=["space", "escape"])
    if "escape" in keys:
        G_RECORDER.abort()
        core.quit()
    if "space" in keys:
        thisExp.addData("practice_between_rt", practice_between_clock.getTime())
        practice_phase = "segment"
        practice_stem = f"{expInfo['participant']}_practice_{G_PRACTICE_TRIAL_INDEX:02d}_pic{practice_segment + 1:02d}_{practice_roles[practice_segment]}"
        G_RECORDER.start(practice_stem)
        event.clearEvents()
elif practice_phase == "segment":
    g_draw_sequence(practice_images, practice_arrows, practice_segment + 1)
    keys = event.getKeys(keyList=["space", "escape"])
    if "escape" in keys:
        G_RECORDER.abort()
        core.quit()
    if "space" in keys:
        audio_file = G_RECORDER.stop()
        seg = practice_segment + 1
        thisExp.addData(f"practice_seg{seg}_role", practice_roles[practice_segment])
        thisExp.addData(f"practice_seg{seg}_audio", audio_file)
        if practice_segment >= len(practice_images) - 1:
            continueRoutine = False
        else:
            practice_segment += 1
            if practice_segment == 2:
                practice_phase = "practice_audio"
                practice_audio = g_play_audio("Audio/tsakyali.wav")
                practice_audio_clock.reset()
                practice_audio_duration = practice_audio.getDuration() if practice_audio else 0
            else:
                practice_stem = f"{expInfo['participant']}_practice_{G_PRACTICE_TRIAL_INDEX:02d}_pic{practice_segment + 1:02d}_{practice_roles[practice_segment]}"
                G_RECORDER.start(practice_stem)
        event.clearEvents()
elif practice_phase == "practice_audio":
    g_draw_sequence(practice_images, practice_arrows, 2)
    if practice_audio_clock.getTime() >= practice_audio_duration:
        practice_phase = "segment"
        practice_stem = f"{expInfo['participant']}_practice_{G_PRACTICE_TRIAL_INDEX:02d}_pic{practice_segment + 1:02d}_{practice_roles[practice_segment]}"
        G_RECORDER.start(practice_stem)
        event.clearEvents()
'''

PRACTICE_END = r'''
G_RECORDER.stop()
if practice_audio:
    practice_audio.stop()
g_release_stims(practice_images, practice_arrows)
practice_images = []
practice_arrows = []
'''

PRACTICE_DONE_BEGIN = r'''
win.color = "white"
practice_done_icon = visual.ImageStim(win, image=g_path("Stimuli/sound.png"), pos=(0, 0), size=(0.22, 0.22), interpolate=True)
practice_done_audio = g_play_audio("Audio/practice_end.wav")
event.clearEvents()
'''

PRACTICE_DONE_EACH = r'''
practice_done_icon.draw()
keys = event.getKeys(keyList=["space", "escape"])
if "escape" in keys:
    core.quit()
if "space" in keys:
    if practice_done_audio:
        practice_done_audio.stop()
    continueRoutine = False
'''

MAIN_BEGIN = r'''
G_MAIN_TRIAL_INDEX += 1
win.color = "white"
main_roles, main_paths = g_roles_and_paths()
main_images, main_arrows = g_make_sequence(win, main_roles, main_paths)
main_segment = 0
main_phase = "between"
main_between_clock = core.Clock()
main_between_audio = None
main_between_audio_value = g_text(globals().get("between_audio", ""))
main_audio_lock = g_float(globals().get("between_audio_lock_sec", 0), 0.0)
main_placeholder = g_fullscreen_image(win, between_image)
main_dataset_number = g_int(globals().get("dataset_number", 0), 0)
main_condition_id = g_text(globals().get("condition_id", "unknown_condition"))
if main_between_audio_value:
    main_between_audio = g_play_audio(main_between_audio_value)
main_between_clock.reset()
thisExp.addData("main_trial_index", G_MAIN_TRIAL_INDEX)
thisExp.addData("between_image", g_path(between_image))
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
main_images = []
main_arrows = []
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


def loop_initiator(flow: ET.Element, name: str, conditions_file: str) -> None:
    loop = ET.SubElement(flow, "LoopInitiator", loopType="TrialHandler", name=name)
    add_param(loop, "Selected rows", "")
    add_param(loop, "conditions", "None")
    add_param(loop, "conditionsFile", conditions_file, "file")
    add_param(loop, "endPoints", "[0, 1]", "num")
    add_param(loop, "isTrials", "True", "bool")
    add_param(loop, "loopType", "sequential")
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
            param.set("val", "False")
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
    loop_initiator(flow, "PracticeLoop", "Conds/practice.csv")
    ET.SubElement(flow, "Routine", name="PracticeTrial")
    ET.SubElement(flow, "LoopTerminator", name="PracticeLoop")
    ET.SubElement(flow, "Routine", name="PracticeEnd")
    loop_initiator(flow, "MainBlock1", "Conds/main_block1.csv")
    ET.SubElement(flow, "Routine", name="MainTrial")
    ET.SubElement(flow, "LoopTerminator", name="MainBlock1")
    ET.SubElement(flow, "Routine", name="Break")
    loop_initiator(flow, "MainBlock2", "Conds/main_block2.csv")
    ET.SubElement(flow, "Routine", name="MainTrial")
    ET.SubElement(flow, "LoopTerminator", name="MainBlock2")
    ET.SubElement(flow, "Routine", name="Break")
    loop_initiator(flow, "MainBlock3", "Conds/main_block3.csv")
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
- Trial order: fixed random order, seed `{RANDOM_SEED}`.
- Breaks: after trials 40 and 80.
- Between-trial images: random images copied from `between_trials/` into `BetweenTrials/`.
- Between-trial audio probes: 12 rows marked in `Conds/main_all_120.csv`; audio is `Audio/tsakyali.wav`; lockout is 10 seconds.
- Practice uses old practice images/audio, starts each trial with a random between-trial image, and plays `Audio/tsakyali.wav` before the last picture.
- Breaks show `Stimuli/break.png`; space is locked for 30 seconds.
- Main recordings are named with image set, condition, and picture identifier.
- Practice recordings are named with practice trial number and picture number.
- Main PNGs are local packaged copies in `MainStimuli/`, downsampled to max `{MAIN_STIMULI_MAX_DIMENSION}px on the long edge. This avoids loading trial textures from the Google Drive cloud-storage mount during the run.

Open `gurung_120_v1.psyexp` in PsychoPy Builder.

Source root used:

```text
{source_root}
```

The main trial routine uses a Code Component because trials may contain either 3 or 4 images, and the transitive/intransitive target image is dynamically centered.
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
        for dirname in ("data", "recordings"):
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

    between_images = list_between_images(out_dir)
    main_rows = build_main_rows(datasets, between_images, main_stimuli)
    practice_rows = build_practice_rows(between_images)
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
        "audio_probe_trials": sum(1 for row in main_rows if row["audio_probe"] == "1"),
        "between_trial_images": len(between_images),
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
