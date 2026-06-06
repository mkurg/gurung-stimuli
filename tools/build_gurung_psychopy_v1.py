#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import random
import re
import shutil
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
]


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
    audio_dir.mkdir(parents=True, exist_ok=True)
    stim_dir.mkdir(parents=True, exist_ok=True)
    placeholder_dir.mkdir(parents=True, exist_ok=True)

    for path in sorted((old_dir / "Audio").iterdir(), key=lambda item: item.name):
        if path.is_file():
            shutil.copy2(path, audio_dir / path.name)

    for path in sorted((old_dir / "old_stimuli").iterdir(), key=lambda item: item.name):
        if path.is_file():
            shutil.copy2(path, stim_dir / path.name)

    probe_source = audio_dir / "isolated_instr.wav"
    if probe_source.is_file():
        shutil.copy2(probe_source, audio_dir / "probe_placeholder.wav")

    placeholder_source = stim_dir / "break.png"
    for index in range(1, 121):
        shutil.copy2(placeholder_source, placeholder_dir / f"between_{index:03d}.png")


def build_main_rows(datasets: list[dict[str, object]]) -> list[dict[str, str]]:
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
                row[f"img{index}"] = str(Path(dataset["set_folder"]) / f"{stem}.png")
                row[f"img{index}_role"] = stem
            rows.append(row)

    rng = random.Random(RANDOM_SEED)
    rng.shuffle(rows)
    probe_indices = set(rng.sample(range(len(rows)), 12))
    for index, row in enumerate(rows, start=1):
        row["random_order"] = str(index)
        row["between_image"] = f"Placeholders/between_{index:03d}.png"
        if index - 1 in probe_indices:
            row["audio_probe"] = "1"
            row["between_audio"] = "Audio/probe_placeholder.wav"
            row["between_audio_lock_sec"] = "30"
    return rows


def build_practice_rows() -> list[dict[str, str]]:
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
G_DATA_DIR.mkdir(exist_ok=True)
G_RECORDINGS_DIR.mkdir(exist_ok=True)
G_IMAGE_SIZE = (0.30, 0.45)
G_PLACEHOLDER_SIZE = (0.48, 0.48)
G_ARROW_SIZE = (0.065, 0.065)
G_STEP = 0.34
G_MAIN_TRIAL_INDEX = 0
G_PRACTICE_TRIAL_INDEX = 0
G_SPEAKER = None

try:
    event.globalKeys.add(key="escape", func=core.quit, name="gurung_escape_quit")
except Exception as _gurung_global_key_error:
    print("Global escape key was not registered:", _gurung_global_key_error)


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


def g_path(value):
    value = g_text(value)
    if not value:
        return ""
    path = Path(value)
    if path.is_absolute():
        return str(path)
    return str(G_ROOT / path)


def g_choose_speaker():
    if SpeakerDevice is None:
        return None
    try:
        devices = SpeakerDevice.getAvailableDevices()
    except Exception as err:
        print("Could not list speaker devices:", err)
        return None
    names = [g_text(device.get("deviceName") or device.get("name")) for device in devices]
    print("Available speaker devices:", names)
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
            print("Using speaker device:", speaker.name)
            return speaker
        except Exception as err:
            print(f"Could not open speaker {name!r}:", err)
    print("No usable speaker found; PsychoPy will use its default audio device.")
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

    def start(self, stem):
        self.stop()
        if not G_RECORDING_AVAILABLE:
            return ""
        self.frames = []
        self.path = self.root / f"{g_safe(stem)}.wav"

        def callback(indata, frames, time_info, status):
            if status:
                print(status)
            self.frames.append(indata.copy())

        self.stream = _gurung_sd.InputStream(
            samplerate=48000,
            channels=1,
            dtype="float32",
            callback=callback,
        )
        self.stream.start()
        return str(self.path)

    def stop(self):
        if self.stream is None:
            return ""
        self.stream.stop()
        self.stream.close()
        self.stream = None
        if self.path and self.frames:
            audio = _gurung_np.concatenate(self.frames, axis=0)
            _gurung_sf.write(str(self.path), audio, 48000)
            return str(self.path)
        return ""

    def abort(self):
        if self.stream is not None:
            self.stream.abort()
            self.stream.close()
            self.stream = None


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
practice_phase = "segment"
practice_audio = None
practice_audio_clock = core.Clock()
practice_audio_duration = 0
practice_stem = f"{expInfo['participant']}_practice_{G_PRACTICE_TRIAL_INDEX:02d}_seg{practice_segment + 1}_{practice_roles[practice_segment]}"
practice_audio_file = G_RECORDER.start(practice_stem)
thisExp.addData("practice_trial_index", G_PRACTICE_TRIAL_INDEX)
event.clearEvents()
'''

PRACTICE_EACH = r'''
if practice_phase == "segment":
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
                practice_stem = f"{expInfo['participant']}_practice_{G_PRACTICE_TRIAL_INDEX:02d}_seg{practice_segment + 1}_{practice_roles[practice_segment]}"
                G_RECORDER.start(practice_stem)
        event.clearEvents()
elif practice_phase == "practice_audio":
    g_draw_sequence(practice_images, practice_arrows, 2)
    if practice_audio_clock.getTime() >= practice_audio_duration:
        practice_phase = "segment"
        practice_stem = f"{expInfo['participant']}_practice_{G_PRACTICE_TRIAL_INDEX:02d}_seg{practice_segment + 1}_{practice_roles[practice_segment]}"
        G_RECORDER.start(practice_stem)
        event.clearEvents()
'''

PRACTICE_END = r'''
G_RECORDER.stop()
if practice_audio:
    practice_audio.stop()
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
main_placeholder = visual.ImageStim(
    win,
    image=g_path(between_image),
    pos=(0, 0),
    size=G_PLACEHOLDER_SIZE,
    interpolate=True,
)
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
        main_stem = f"{expInfo['participant']}_main_{G_MAIN_TRIAL_INDEX:03d}_{trial_id}_seg{main_segment + 1}_{main_roles[main_segment]}"
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
            main_stem = f"{expInfo['participant']}_main_{G_MAIN_TRIAL_INDEX:03d}_{trial_id}_seg{main_segment + 1}_{main_roles[main_segment]}"
            G_RECORDER.start(main_stem)
        event.clearEvents()
'''

MAIN_END = r'''
G_RECORDER.stop()
if main_between_audio:
    main_between_audio.stop()
'''

BREAK_BEGIN = r'''
win.color = "white"
break_image = visual.ImageStim(win, image=g_path("Stimuli/break.png"), pos=(0, 0), size=(0.55, 0.55), interpolate=True)
event.clearEvents()
'''

BREAK_EACH = r'''
break_image.draw()
keys = event.getKeys(keyList=["space", "escape"])
if "escape" in keys:
    core.quit()
if "space" in keys:
    continueRoutine = False
'''

END_BEGIN = r'''
win.color = "white"
finish_image = visual.ImageStim(win, image=g_path("Stimuli/finish.png"), pos=(0, 0), size=(0.55, 0.55), interpolate=True)
event.clearEvents()
'''

END_EACH = r'''
finish_image.draw()
keys = event.getKeys(keyList=["space", "escape"])
if "escape" in keys or "space" in keys:
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
- Between-trial placeholder images: `Placeholders/between_001.png` ... `between_120.png`.
- Between-trial audio probes: 12 rows marked in `Conds/main_all_120.csv`; placeholder audio is `Audio/probe_placeholder.wav`; lockout is 30 seconds.
- Practice uses old practice images and old audio files from `old/`.

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

    if out_dir.exists() and args.clean:
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    datasets = scan_dataset_set1(source_root)
    copy_assets(out_dir, old_dir)

    main_rows = build_main_rows(datasets)
    practice_rows = build_practice_rows()
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
