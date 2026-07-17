#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import os
import json
import math
import shutil
import wave
import xml.etree.ElementTree as ET
from copy import deepcopy
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw

import build_gurung_psychopy_v1 as discourse


MAIN_FIELDS = [
    "trial_id",
    "source_trial_id",
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
    "target_image",
    "target_role",
]

PRACTICE_FIELDS = [
    "trial_id",
    "practice_index",
    "target_image",
    "target_role",
    "practice_audio",
    "source_n_images",
]

REST_BEEP = "rest_beep.wav"
ISOLATED_PRACTICE_ITEMS = [
    (
        "isolated_practice_01_orange_and_man",
        "Stimuli/isolated_practice_01_orange_and_man.jpg",
        "orange_and_man",
        "Audio/new_isol_man_orange.wav",
    ),
    (
        "isolated_practice_02_woman_milking_goat",
        "Stimuli/isolated_practice_02_woman_milking_goat.jpg",
        "woman_milking_goat",
        "Audio/new_isol_milk_goat.wav",
    ),
    (
        "isolated_practice_03_boy_bicycle",
        "Stimuli/isolated_practice_03_boy_bicycle.jpg",
        "boy_bicycle",
        "",
    ),
    (
        "isolated_practice_04_woman_chopping_greens",
        "Stimuli/isolated_practice_05_woman_chopping_greens.jpg",
        "woman_chopping_greens",
        "",
    ),
    (
        "isolated_practice_05_old_man_corn",
        "Stimuli/isolated_practice_04_old_man_corn.jpg",
        "old_man_corn",
        "",
    ),
    (
        "isolated_practice_06_woman_phone",
        "Stimuli/isolated_practice_06_woman_phone.jpg",
        "woman_phone",
        "",
    ),
    (
        "isolated_practice_07_man_motorcycle",
        "Stimuli/isolated_practice_07_man_motorcycle.jpg",
        "man_motorcycle",
        "",
    ),
    (
        "isolated_practice_08_butterfly_phone",
        "Stimuli/isolated_practice_09_butterfly_phone.jpg",
        "butterfly_phone",
        "",
    ),
    (
        "isolated_practice_09_badminton_wind",
        "Stimuli/isolated_practice_10_badminton_wind.jpg",
        "badminton_wind",
        "",
    ),
    (
        "isolated_practice_10_girl_towel_old_man",
        "Stimuli/isolated_practice_08_girl_towel_old_man.jpg",
        "girl_towel_old_man",
        "",
    ),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def target_from_discourse_row(row: dict[str, str]) -> tuple[str, str]:
    for index in range(1, 5):
        role = (row.get(f"img{index}_role") or "").strip()
        if role in {"tr_target", "it_target"}:
            image = (row.get(f"img{index}") or "").strip()
            if image:
                return image, role
    raise ValueError(f"No target image in discourse trial {row.get('trial_id', '<unknown>')}")


def build_main_rows(discourse_dir: Path, list_id: str, image_prefix: str = ".") -> list[dict[str, str]]:
    rows = []
    if list_id not in discourse.LIST_RULES:
        raise ValueError(f"Unknown experimental list: {list_id}")
    selected_by_set = {
        set_key: condition_ids[0]
        for set_key, condition_ids in discourse.LIST_RULES[list_id].items()
    }
    source_path = discourse_dir / "Conds" / f"main_list{list_id}_all_240.csv"
    for source in read_csv(source_path):
        set_key = (source.get("stimulus_set") or "").strip()
        if source.get("condition_id", "") != selected_by_set.get(set_key):
            continue
        target_image, target_role = target_from_discourse_row(source)
        if image_prefix and image_prefix != "." and not Path(target_image).is_absolute():
            target_image = f"{image_prefix}/{target_image}".replace("\\", "/")
        transitivity = source.get("transitivity", "")
        condition_trigger = "1" if transitivity == "transitive" else "2"
        rows.append(
            {
                "trial_id": f"isolated_list{list_id}_{source.get('trial_id', '')}",
                "source_trial_id": source.get("trial_id", ""),
                "experiment_list": list_id,
                "dataset_number": source.get("dataset_number", ""),
                "dataset_slug": source.get("dataset_slug", ""),
                "dataset_label": source.get("dataset_label", ""),
                "stimulus_set": source.get("stimulus_set", ""),
                "condition_id": source.get("condition_id", ""),
                "condition_name": source.get("condition_name", ""),
                "cohesion": source.get("cohesion", ""),
                "transitivity": transitivity,
                "condition_trigger": condition_trigger,
                "item_trigger": source.get("item_trigger", ""),
                "target_image": target_image,
                "target_role": target_role,
            }
        )
    if len(rows) != 120:
        raise ValueError(f"Expected 120 isolated rows for list {list_id}, got {len(rows)} from {source_path}")
    return rows


def build_practice_rows(discourse_dir: Path) -> list[dict[str, str]]:
    rows = []
    stimuli_dir = discourse_dir / "Stimuli"
    for practice_index, (trial_id, target_image, target_role, practice_audio) in enumerate(ISOLATED_PRACTICE_ITEMS, start=1):
        if not (stimuli_dir / Path(target_image).name).is_file():
            raise FileNotFoundError(stimuli_dir / Path(target_image).name)
        rows.append(
            {
                "trial_id": trial_id,
                "practice_index": str(practice_index),
                "target_image": target_image,
                "target_role": target_role,
                "practice_audio": practice_audio,
                "source_n_images": "1",
            }
        )
    return rows


def copy_assets(discourse_dir: Path, out_dir: Path) -> None:
    for dirname in ("Audio", "Stimuli"):
        source = discourse_dir / dirname
        target = out_dir / dirname
        if not source.is_dir():
            raise FileNotFoundError(source)
        shutil.copytree(source, target, dirs_exist_ok=True)
    make_rest_icons(out_dir / "Stimuli")
    make_rest_beep(out_dir / "Audio" / REST_BEEP)


def make_rest_icons(stimuli_dir: Path) -> None:
    stimuli_dir.mkdir(parents=True, exist_ok=True)
    source_path = Path(__file__).resolve().parent / "assets" / "resting_eye_icons_source.png"
    if not source_path.exists():
        raise FileNotFoundError(f"Missing resting-state eye icon source: {source_path}")

    source = Image.open(source_path).convert("RGBA")
    crop_specs = {
        "eyes_open.png": (29, 88, 297, 220),
        "eyes_closed.png": (316, 94, 584, 218),
    }

    def remove_white_background(image: Image.Image) -> Image.Image:
        image = image.convert("RGBA")
        pixels = image.load()
        for y in range(image.height):
            for x in range(image.width):
                red, green, blue, alpha = pixels[x, y]
                luminance = (0.2126 * red) + (0.7152 * green) + (0.0722 * blue)
                if luminance > 210:
                    pixels[x, y] = (255, 255, 255, 0)
                else:
                    icon_alpha = min(255, int((210 - luminance) * 2.8))
                    pixels[x, y] = (0, 0, 0, min(alpha, icon_alpha))
        return image

    for filename, crop_box in crop_specs.items():
        eye = remove_white_background(source.crop(crop_box))
        eye_width = 180
        eye_height = round(eye.height * (eye_width / eye.width))
        eye = eye.resize((eye_width, eye_height), Image.Resampling.LANCZOS)
        image = Image.new("RGBA", (512, 512), (255, 255, 255, 0))
        gap = 46
        left_x = (512 - ((2 * eye_width) + gap)) // 2
        top_y = (512 - eye_height) // 2
        image.alpha_composite(eye, (left_x, top_y))
        image.alpha_composite(eye, (left_x + eye_width + gap, top_y))
        image.save(stimuli_dir / filename)


def make_rest_beep(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 48000
    duration = 1.30
    amplitude = 0.28
    notes = (
        (0.00, 1046.50),  # C6
        (0.42, 1479.98),  # F#6, tritone above C6
    )
    n_frames = int(sample_rate * duration)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        frames = bytearray()
        for index in range(n_frames):
            t = index / sample_rate
            value = 0.0
            for onset, frequency in notes:
                note_t = t - onset
                if note_t < 0:
                    continue
                attack = min(1.0, note_t / 0.008)
                decay = math.exp(-4.8 * note_t)
                tone = (
                    math.sin(2 * math.pi * frequency * note_t)
                    + 0.34 * math.sin(2 * math.pi * frequency * 2.01 * note_t)
                    + 0.16 * math.sin(2 * math.pi * frequency * 3.02 * note_t)
                )
                value += attack * decay * tone
            sample = int(max(-0.95, min(0.95, amplitude * value)) * 32767)
            frames.extend(sample.to_bytes(2, "little", signed=True))
        handle.writeframes(bytes(frames))


def isolated_shared_code() -> str:
    startup = "G_SPEAKER = g_choose_speaker()\ng_init_between_images()\ng_prepare_runtime_main_blocks()"
    replacement = "G_SPEAKER = g_choose_speaker()"
    base = discourse.SHARED_CODE.replace(startup, replacement)
    base = base.replace('G_LISTENER_RESPONSE_DIRNAME = "listener responses"\n', '')
    base = base.replace('    (folder / G_LISTENER_RESPONSE_DIRNAME).mkdir(parents=True, exist_ok=True)\n', '')
    if startup in base:
        raise RuntimeError("Could not disable discourse between-trial startup code")
    return base + r'''

G_ISOLATED_MAIN_BLOCK_SIZE = 60
G_ISOLATED_RUNTIME_STATE = {"prepared": False, "files": []}
G_ISOLATED_MAIN_TRIAL_INDEX = 0
G_ISOLATED_PRACTICE_INDEX = 0
G_REST_DURATION_SEC = 120.0
G_ISOLATED_DISCOURSE_SIZE_X_RESERVE_WIDTHS = 0.30
G_ISOLATED_DISCOURSE_SIZE_Y_RESERVE = 0.018


def g_isolated_image_size(win):
    # This reserve matches Discourse picture size only. Isolated pictures stay fixed at pos=(0, 0).
    horizontal_room = max(0.1, g_window_aspect(win) - (2 * G_SEQUENCE_X_MARGIN))
    vertical_room = max(0.1, 1.0 - (2 * (G_SEQUENCE_Y_MARGIN + G_ISOLATED_DISCOURSE_SIZE_Y_RESERVE)))
    width_from_horizontal = horizontal_room / (
        G_SEQUENCE_SIZE_COUNT
        + ((G_SEQUENCE_SIZE_COUNT - 1) * G_SEQUENCE_GAP_RATIO)
        + (2 * G_ISOLATED_DISCOURSE_SIZE_X_RESERVE_WIDTHS)
    )
    image_height = min(vertical_room, width_from_horizontal / G_IMAGE_ASPECT)
    image_width = image_height * G_IMAGE_ASPECT
    return (image_width, image_height)


def g_isolated_main_stem(trial_index, dataset_number, condition_value):
    return (
        f"{g_participant_tag()}_isolated_main_{g_list_tag()}_trial{int(trial_index):03d}_"
        f"imageset{int(dataset_number):02d}_cond_{g_transitivity_tag(condition_value)}"
    )


def g_isolated_prepare_runtime_main_blocks():
    if G_ISOLATED_RUNTIME_STATE.get("prepared"):
        return
    list_id = g_selected_list()
    conditions_path = f"Conds/isolated_main_list{list_id}_all_120.csv"
    rows = list(data.importConditions(conditions_path))
    if len(rows) != 120:
        raise RuntimeError(f"Expected 120 isolated main trials in {conditions_path}, found {len(rows)}")
    _gurung_random.shuffle(rows)
    fieldnames = list(rows[0].keys())
    block_files = []
    block_sizes = []
    for block_index in range(2):
        block_rows = rows[
            block_index * G_ISOLATED_MAIN_BLOCK_SIZE : (block_index + 1) * G_ISOLATED_MAIN_BLOCK_SIZE
        ]
        block_sizes.append(len(block_rows))
        block_path = G_DATA_DIR / f"runtime_isolated_main_block{block_index + 1}.csv"
        with block_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
            writer.writeheader()
            for row in block_rows:
                writer.writerow({field: "" if g_is_blank(row.get(field, "")) else row.get(field, "") for field in fieldnames})
        block_files.append(str(block_path))
    G_ISOLATED_RUNTIME_STATE["files"] = block_files
    G_ISOLATED_RUNTIME_STATE["prepared"] = True
    g_log(f"isolated_main_targets_shuffled list={list_id} count={len(rows)} block_sizes={block_sizes}")


def g_isolated_runtime_main_block_file(block_index):
    if not G_ISOLATED_RUNTIME_STATE.get("prepared"):
        g_isolated_prepare_runtime_main_blocks()
    files = G_ISOLATED_RUNTIME_STATE.get("files") or []
    index = int(block_index) - 1
    if index < 0 or index >= len(files):
        raise RuntimeError(f"Invalid isolated main block index: {block_index}")
    return files[index]
'''


def instruction_begin(audio_file: str) -> str:
    return f'''
win.color = "white"
instruction_icon = visual.ImageStim(win, image=g_path("Stimuli/sound.png"), pos=(0, 0), size=(0.22, 0.22), interpolate=True)
instruction_audio_value = "{audio_file}"
instruction_audio = None
instruction_started = False
instruction_clock = core.Clock()
instruction_duration = 0.0
event.clearEvents()
'''


INSTRUCTION_EACH = r'''
instruction_icon.draw()
keys = event.getKeys(keyList=["space", "return", "escape"])
if "escape" in keys:
    g_abort_and_quit()
if "return" in keys:
    if instruction_audio:
        instruction_audio.stop()
    instruction_audio = g_play_audio(instruction_audio_value)
    instruction_started = True
    instruction_clock.reset()
    instruction_duration = g_float(instruction_audio.getDuration() if instruction_audio else 0, 0.0)
    event.clearEvents()
elif "space" in keys:
    if not instruction_started:
        instruction_audio = g_play_audio(instruction_audio_value)
        instruction_started = True
        instruction_clock.reset()
        instruction_duration = g_float(instruction_audio.getDuration() if instruction_audio else 0, 0.0)
        event.clearEvents()
    else:
        if instruction_audio:
            instruction_audio.stop()
        continueRoutine = False
'''


def rest_prompt_begin(label: str, icon: str, audio: str) -> str:
    return f'''
win.color = "white"
rest_prompt_label = "{label}"
rest_prompt_audio_value = "{audio}"
rest_prompt_icon = visual.ImageStim(win, image=g_path("{icon}"), pos=(0, 0), size=(0.44, 0.44), interpolate=True)
rest_prompt_audio = g_play_audio(rest_prompt_audio_value)
rest_prompt_clock = core.Clock()
thisExp.addData(f"{{rest_prompt_label}}_prompt_audio", g_path(rest_prompt_audio_value))
event.clearEvents()
'''


REST_PROMPT_EACH = r'''
rest_prompt_icon.draw()
keys = event.getKeys(keyList=["space", "return", "escape"])
if "escape" in keys:
    g_abort_and_quit()
if "return" in keys:
    if rest_prompt_audio:
        rest_prompt_audio.stop()
    rest_prompt_audio = g_play_audio(rest_prompt_audio_value)
    rest_prompt_clock.reset()
    event.clearEvents()
elif "space" in keys:
    if rest_prompt_audio:
        rest_prompt_audio.stop()
    thisExp.addData(f"{rest_prompt_label}_prompt_rt", rest_prompt_clock.getTime())
    continueRoutine = False
'''


def rest_blank_begin(label: str, trigger_code: int = 150) -> str:
    return f'''
win.color = "white"
rest_blank_label = "{label}"
rest_blank_trigger_code = {int(trigger_code)}
rest_blank_clock = core.Clock()
rest_blank_finish_trigger_sent = False
thisExp.addData(f"{{rest_blank_label}}_start_core_time", core.getTime())
g_trigger_on_flip(rest_blank_trigger_code, f"{{rest_blank_label}}_start")
event.clearEvents()
'''


REST_BLANK_EACH = r'''
keys = event.getKeys(keyList=["space", "escape"])
if "escape" in keys:
    g_abort_and_quit()
if "space" in keys or rest_blank_clock.getTime() >= G_REST_DURATION_SEC:
    if not rest_blank_finish_trigger_sent:
        g_send_trigger(rest_blank_trigger_code, f"{rest_blank_label}_finish")
        rest_blank_finish_trigger_sent = True
    thisExp.addData(f"{rest_blank_label}_duration", rest_blank_clock.getTime())
    thisExp.addData(f"{rest_blank_label}_ended_by", "space" if "space" in keys else "timeout")
    continueRoutine = False
'''


REST_BEEP_BEGIN = r'''
win.color = "white"
rest_beep_audio = g_play_audio("Audio/rest_beep.wav")
rest_beep_clock = core.Clock()
rest_beep_duration = g_float(rest_beep_audio.getDuration() if rest_beep_audio else 1.3, 1.3)
event.clearEvents()
'''


REST_BEEP_EACH = r'''
keys = event.getKeys(keyList=["space", "escape"])
if "escape" in keys:
    g_abort_and_quit()
if "space" in keys or rest_beep_clock.getTime() >= rest_beep_duration:
    if rest_beep_audio:
        rest_beep_audio.stop()
    continueRoutine = False
'''


ISOLATED_PRACTICE_MID_BEGIN = discourse.PRACTICE_DONE_BEGIN.replace(
    "Audio/new_disc_instr3.wav", "Audio/new_isol_instr2.wav"
)
ISOLATED_PRACTICE_MID_EACH = discourse.PRACTICE_DONE_EACH.replace(
    "Audio/new_disc_instr3.wav", "Audio/new_isol_instr2.wav"
)
ISOLATED_PRACTICE_DONE_BEGIN = discourse.PRACTICE_DONE_BEGIN.replace(
    "Audio/new_disc_instr3.wav", "Audio/new_isol_instr3.wav"
)
ISOLATED_PRACTICE_DONE_EACH = discourse.PRACTICE_DONE_EACH.replace(
    "Audio/new_disc_instr3.wav", "Audio/new_isol_instr3.wav"
)


ISOLATED_PRACTICE_BEGIN = r'''
G_ISOLATED_PRACTICE_INDEX += 1
win.color = "white"
isolated_practice_image_path = g_path(target_image)
isolated_practice_image = visual.ImageStim(
    win,
    image=isolated_practice_image_path,
    pos=(0, 0),
    size=g_isolated_image_size(win),
    interpolate=True,
)
isolated_practice_audio_value = g_text(globals().get("practice_audio", ""))
isolated_practice_audio = None
if isolated_practice_audio_value:
    try:
        isolated_practice_audio = sound.Sound(g_path(isolated_practice_audio_value))
    except Exception as err:
        g_log(f"practice_audio_load_failed {isolated_practice_audio_value}: {err}")
isolated_practice_audio_duration = g_float(isolated_practice_audio.getDuration() if isolated_practice_audio else 0, 0.0)
isolated_practice_audio_clock = core.Clock()
isolated_practice_audio_started = False
isolated_practice_clock = core.Clock()
isolated_practice_stem = g_practice_stem(G_ISOLATED_PRACTICE_INDEX, 1)
G_RECORDER.start(isolated_practice_stem)
thisExp.addData("isolated_practice_index", G_ISOLATED_PRACTICE_INDEX)
thisExp.addData("isolated_practice_image", isolated_practice_image_path)
thisExp.addData("isolated_practice_audio", g_path(isolated_practice_audio_value) if isolated_practice_audio_value else "")
event.clearEvents()
'''


ISOLATED_PRACTICE_EACH = r'''
isolated_practice_image.draw()
G_RECORDER.mark_onset_on_flip()
if isolated_practice_audio is not None and not isolated_practice_audio_started:
    win.callOnFlip(isolated_practice_audio.play)
    win.callOnFlip(isolated_practice_audio_clock.reset)
    isolated_practice_audio_started = True
keys = event.getKeys(keyList=["space", "escape"], timeStamped=core.monotonicClock)
key_names = g_key_names(keys)
if "escape" in key_names:
    g_abort_and_quit()
isolated_practice_audio_done = (
    isolated_practice_audio is None
    or (isolated_practice_audio_started and isolated_practice_audio_clock.getTime() >= isolated_practice_audio_duration)
)
if "space" in key_names and isolated_practice_audio_done:
    isolated_practice_file = G_RECORDER.stop(event_core_time=g_key_time(keys, "space"))
    thisExp.addData("isolated_practice_rt", isolated_practice_clock.getTime())
    thisExp.addData("isolated_practice_response_audio", isolated_practice_file)
    if isolated_practice_audio:
        isolated_practice_audio.stop()
    continueRoutine = False
    event.clearEvents()
'''


ISOLATED_PRACTICE_END = r'''
G_RECORDER.stop()
if isolated_practice_audio:
    isolated_practice_audio.stop()
g_release_stims([isolated_practice_image])
isolated_practice_image = None
'''


ISOLATED_MAIN_BEGIN = r'''
G_ISOLATED_MAIN_TRIAL_INDEX += 1
win.color = "white"
isolated_main_image_path = g_path(target_image)
isolated_main_image = visual.ImageStim(
    win,
    image=isolated_main_image_path,
    pos=(0, 0),
    size=g_isolated_image_size(win),
    interpolate=True,
)
isolated_main_clock = core.Clock()
isolated_main_dataset_number = g_int(globals().get("dataset_number", 0), 0)
isolated_main_condition_id = g_text(globals().get("condition_id", "unknown_condition"))
isolated_main_transitivity = g_text(globals().get("transitivity", isolated_main_condition_id))
isolated_main_target_role = g_text(globals().get("target_role", "target"))
isolated_main_stimulus_set = g_int(globals().get("stimulus_set", 0), 0)
isolated_main_condition_trigger = g_int(globals().get("condition_trigger", 0), 0)
isolated_main_item_trigger = g_int(globals().get("item_trigger", 0), 0)
isolated_main_trigger_scheduled = False
isolated_main_target_clock = core.Clock()
isolated_main_target_state = {"started": False, "condition_sent": False, "item_sent": False}
isolated_main_stem = g_isolated_main_stem(
    G_ISOLATED_MAIN_TRIAL_INDEX,
    isolated_main_dataset_number,
    isolated_main_transitivity,
)
G_RECORDER.start(isolated_main_stem)
thisExp.addData("isolated_main_trial_index", G_ISOLATED_MAIN_TRIAL_INDEX)
thisExp.addData("experiment_list", g_selected_list())
thisExp.addData("isolated_dataset_number", isolated_main_dataset_number)
thisExp.addData("isolated_stimulus_set", isolated_main_stimulus_set)
thisExp.addData("isolated_condition_id", isolated_main_condition_id)
thisExp.addData("isolated_target_role", isolated_main_target_role)
thisExp.addData("isolated_target_image", isolated_main_image_path)
thisExp.addData("condition_trigger", isolated_main_condition_trigger)
thisExp.addData("item_trigger", isolated_main_item_trigger)
event.clearEvents()
'''


ISOLATED_MAIN_EACH = r'''
isolated_main_image.draw()
if not isolated_main_trigger_scheduled:
    G_RECORDER.mark_onset_on_flip()
    g_trigger_on_flip(200, f"isolated_trial{G_ISOLATED_MAIN_TRIAL_INDEX:03d}_target_onset")
    win.callOnFlip(isolated_main_target_clock.reset)
    win.callOnFlip(g_mark_clock_started, isolated_main_target_state)
    isolated_main_trigger_scheduled = True
if isolated_main_target_state.get("started"):
    if (not isolated_main_target_state.get("condition_sent")) and isolated_main_target_clock.getTime() >= 0.200:
        g_send_trigger(
            isolated_main_condition_trigger,
            f"isolated_trial{G_ISOLATED_MAIN_TRIAL_INDEX:03d}_condition_{isolated_main_condition_trigger}",
        )
        isolated_main_target_state["condition_sent"] = True
    if (not isolated_main_target_state.get("item_sent")) and isolated_main_target_clock.getTime() >= 0.400:
        g_send_trigger(
            isolated_main_item_trigger,
            f"isolated_trial{G_ISOLATED_MAIN_TRIAL_INDEX:03d}_item{isolated_main_item_trigger:03d}",
        )
        isolated_main_target_state["item_sent"] = True
keys = event.getKeys(keyList=["space", "escape"], timeStamped=core.monotonicClock)
key_names = g_key_names(keys)
if "escape" in key_names:
    g_abort_and_quit()
if "space" in key_names and isolated_main_target_state.get("item_sent"):
    isolated_main_file = G_RECORDER.stop(event_core_time=g_key_time(keys, "space"))
    thisExp.addData("isolated_main_rt", isolated_main_clock.getTime())
    thisExp.addData("isolated_main_response_audio", isolated_main_file)
    g_send_trigger(202, f"isolated_trial{G_ISOLATED_MAIN_TRIAL_INDEX:03d}_end")
    continueRoutine = False
    event.clearEvents()
'''


ISOLATED_MAIN_END = r'''
G_RECORDER.stop()
g_release_stims([isolated_main_image])
isolated_main_image = None
'''


def patch_settings(settings: ET.Element) -> None:
    discourse.patch_settings(settings)
    for param in settings.findall("Param"):
        name = param.get("name")
        if name == "expName":
            param.set("val", "gurung_isolated_v1")
        elif name == "Data filename":
            param.set("val", "u'data/%s_%s_%s' % (expInfo['participant'], expName, expInfo['date'])")
        elif name == "Window size (pixels)":
            param.set("val", "(1200, 800)")
            param.set("valType", "list")


def add_routine(routines: ET.Element, name: str, code_name: str, **code_parts: str) -> None:
    discourse.add_routine(routines, name, code_name, **code_parts)


def build_psyexp(out_dir: Path, template: Path) -> Path:
    template_root = ET.parse(template).getroot()
    settings = template_root.find("Settings")
    if settings is None:
        raise ValueError(f"Template has no Settings: {template}")
    settings = deepcopy(settings)
    patch_settings(settings)

    root = ET.Element("PsychoPy2experiment", encoding="utf-8", version="2026.1.3")
    root.append(settings)
    routines = ET.SubElement(root, "Routines")
    add_routine(
        routines,
        "RestEyesOpenPrompt",
        "rest_open_prompt_code",
        begin_experiment=isolated_shared_code(),
        begin_routine=rest_prompt_begin("rest_eyes_open", "Stimuli/eyes_open.png", "Audio/new_isol_rs_eyesopen_start.wav"),
        each_frame=REST_PROMPT_EACH,
    )
    add_routine(
        routines,
        "RestEyesOpen",
        "rest_open_code",
        begin_routine=rest_blank_begin("rest_eyes_open"),
        each_frame=REST_BLANK_EACH,
    )
    add_routine(routines, "RestBeep", "rest_beep_code", begin_routine=REST_BEEP_BEGIN, each_frame=REST_BEEP_EACH)
    add_routine(
        routines,
        "RestEyesClosedPrompt",
        "rest_closed_prompt_code",
        begin_routine=rest_prompt_begin("rest_eyes_closed", "Stimuli/eyes_closed.png", "Audio/new_isol_rs_eyesclosed_start.wav"),
        each_frame=REST_PROMPT_EACH,
    )
    add_routine(
        routines,
        "RestEyesClosed",
        "rest_closed_code",
        begin_routine=rest_blank_begin("rest_eyes_closed"),
        each_frame=REST_BLANK_EACH,
    )
    add_routine(
        routines,
        "RestReadyPrompt",
        "rest_ready_prompt_code",
        begin_routine=rest_prompt_begin("rest_ready", "Stimuli/eyes_open.png", "Audio/new_isol_rs_eyesclosed_finish.wav"),
        each_frame=REST_PROMPT_EACH,
    )
    add_routine(
        routines,
        "Instructions",
        "instructions_code",
        begin_routine=instruction_begin("Audio/new_isol_instr1.wav"),
        each_frame=INSTRUCTION_EACH,
    )
    add_routine(
        routines,
        "PracticeTrial",
        "practice_trial_code",
        begin_routine=ISOLATED_PRACTICE_BEGIN,
        each_frame=ISOLATED_PRACTICE_EACH,
        end_routine=ISOLATED_PRACTICE_END,
    )
    add_routine(
        routines,
        "PracticeMidInstruction",
        "practice_mid_instruction_code",
        begin_routine=ISOLATED_PRACTICE_MID_BEGIN,
        each_frame=ISOLATED_PRACTICE_MID_EACH,
    )
    add_routine(
        routines,
        "PracticeEnd",
        "practice_end_code",
        begin_routine=ISOLATED_PRACTICE_DONE_BEGIN,
        each_frame=ISOLATED_PRACTICE_DONE_EACH,
    )
    add_routine(
        routines,
        "MainTrial",
        "main_trial_code",
        begin_routine=ISOLATED_MAIN_BEGIN,
        each_frame=ISOLATED_MAIN_EACH,
        end_routine=ISOLATED_MAIN_END,
    )
    add_routine(routines, "Break", "break_code", begin_routine=discourse.BREAK_BEGIN, each_frame=discourse.BREAK_EACH)
    add_routine(routines, "EndExperiment", "end_code", begin_routine=discourse.END_BEGIN, each_frame=discourse.END_EACH)
    add_routine(
        routines,
        "PostRestEyesOpenPrompt",
        "post_rest_open_prompt_code",
        begin_routine=rest_prompt_begin("post_rest_eyes_open", "Stimuli/eyes_open.png", "Audio/new_isol_rs_eyesopen_start.wav"),
        each_frame=REST_PROMPT_EACH,
    )
    add_routine(
        routines,
        "PostRestEyesOpen",
        "post_rest_open_code",
        begin_routine=rest_blank_begin("post_rest_eyes_open", trigger_code=151),
        each_frame=REST_BLANK_EACH,
    )
    add_routine(
        routines,
        "PostRestEyesClosedPrompt",
        "post_rest_closed_prompt_code",
        begin_routine=rest_prompt_begin("post_rest_eyes_closed", "Stimuli/eyes_closed.png", "Audio/new_isol_rs_eyesclosed_start.wav"),
        each_frame=REST_PROMPT_EACH,
    )
    add_routine(
        routines,
        "PostRestEyesClosed",
        "post_rest_closed_code",
        begin_routine=rest_blank_begin("post_rest_eyes_closed", trigger_code=151),
        each_frame=REST_BLANK_EACH,
    )
    add_routine(
        routines,
        "PostRestReadyPrompt",
        "post_rest_ready_prompt_code",
        begin_routine=rest_prompt_begin("post_rest_ready", "Stimuli/eyes_open.png", "Audio/new_isol_rs_eyesclosed_finish.wav"),
        each_frame=REST_PROMPT_EACH,
    )

    flow = ET.SubElement(root, "Flow")
    ET.SubElement(flow, "Routine", name="RestEyesOpenPrompt")
    ET.SubElement(flow, "Routine", name="RestEyesOpen")
    ET.SubElement(flow, "Routine", name="RestBeep")
    ET.SubElement(flow, "Routine", name="RestEyesClosedPrompt")
    ET.SubElement(flow, "Routine", name="RestEyesClosed")
    ET.SubElement(flow, "Routine", name="RestBeep")
    ET.SubElement(flow, "Routine", name="RestReadyPrompt")
    ET.SubElement(flow, "Routine", name="Instructions")
    discourse.loop_initiator(flow, "PracticeVoicedLoop", "Conds/isolated_practice_voiced.csv", loop_type="sequential")
    ET.SubElement(flow, "Routine", name="PracticeTrial")
    ET.SubElement(flow, "LoopTerminator", name="PracticeVoicedLoop")
    ET.SubElement(flow, "Routine", name="PracticeMidInstruction")
    discourse.loop_initiator(flow, "PracticeUnvoicedLoop", "Conds/isolated_practice_unvoiced.csv", loop_type="sequential")
    ET.SubElement(flow, "Routine", name="PracticeTrial")
    ET.SubElement(flow, "LoopTerminator", name="PracticeUnvoicedLoop")
    ET.SubElement(flow, "Routine", name="PracticeEnd")
    discourse.loop_initiator(flow, "MainBlock1", "$g_isolated_runtime_main_block_file(1)", loop_type="sequential")
    ET.SubElement(flow, "Routine", name="MainTrial")
    ET.SubElement(flow, "LoopTerminator", name="MainBlock1")
    ET.SubElement(flow, "Routine", name="Break")
    discourse.loop_initiator(flow, "MainBlock2", "$g_isolated_runtime_main_block_file(2)", loop_type="sequential")
    ET.SubElement(flow, "Routine", name="MainTrial")
    ET.SubElement(flow, "LoopTerminator", name="MainBlock2")
    ET.SubElement(flow, "Routine", name="EndExperiment")
    ET.SubElement(flow, "Routine", name="PostRestEyesOpenPrompt")
    ET.SubElement(flow, "Routine", name="PostRestEyesOpen")
    ET.SubElement(flow, "Routine", name="RestBeep")
    ET.SubElement(flow, "Routine", name="PostRestEyesClosedPrompt")
    ET.SubElement(flow, "Routine", name="PostRestEyesClosed")
    ET.SubElement(flow, "Routine", name="RestBeep")
    ET.SubElement(flow, "Routine", name="PostRestReadyPrompt")

    ET.indent(root, space="  ")
    path = out_dir / "gurung_isolated_v1.psyexp"
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
    return path


def write_readme(out_dir: Path) -> None:
    readme = """# Gurung Isolated PsychoPy Experiment

This is the isolated-picture version of the Gurung experiment.

- Resting-state sequence comes before the experiment instruction screen: eyes-open prompt, 2-minute blank screen, 1.3-second xylophone-style tritone chime, eyes-closed prompt, 2-minute blank screen, 1.3-second xylophone-style tritone chime, ready prompt with the eyes-open icon. The same resting-state sequence runs again after the finish-flags screen at task end.
- Resting-state blank screens end automatically after 120 seconds, but Space can move forward earlier.
- Pre-task resting-state blank intervals send/log trigger 150 at eyes-open start, eyes-open finish, eyes-closed start, and eyes-closed finish; post-task resting-state blank intervals use trigger 151 for the same four events.
- Isolated practice uses three speaker instruction screens: `Audio/new_isol_instr1.wav` before practice trials 1-2, `Audio/new_isol_instr2.wav` before practice trials 3-10, and `Audio/new_isol_instr3.wav` after practice before the main task.
- Practice has 10 fixed single-picture trials in CSV order, using the `isolated_practice_*.jpg` files in `Stimuli/`; the flow runs `isolated_practice_voiced.csv` followed by `isolated_practice_unvoiced.csv`.
- Practice trials 1 and 2 are the voiced orange-picking and goat-milking pictures; they play `Audio/new_isol_man_orange.wav` and `Audio/new_isol_milk_goat.wav` simultaneously with the picture. Practice trials 3-10 have no picture audio.
- At the start dialog, choose experimental `list` 1 or 2. The main part has 120 isolated target-picture trials for the selected list, built from the Discourse list tables.
- Main target pictures are JPEGs referenced from the Discourse `JpegStimuliFullRes/` package with relative paths.
- Main trial order is reshuffled at runtime on every run, then split into 60 trials, a 30-second break, and 60 trials.
- EEG triggers are logged to `recordings/<participant>_l<list>_<date-time>/eeg_triggers.csv`. If `eeg_port` is filled in, the same trigger codes are also sent as single-byte serial pulses using `trigger_pulse_ms` as pulse duration.
- Isolated main trigger codes: target picture onset 200, transitivity condition 1/2 at 200 ms after target onset, item 1-120 at 400 ms after target onset, trial-end button press 202.
- There are no Nepal images, questions, or audio probes between isolated trials.
- Picture size matches the Discourse sequence pictures, but isolated pictures have no jitter: every practice and main picture is always centered at `(0, 0)`.
- Microphone recording uses the same continuous-session WAV and reproducible clipping scheme as the Discourse experiment. Practice recordings use names like `arrate_practice_08_pic01.wav`; main recordings use `isolated_main_l1` or `isolated_main_l2` and isolated `cond_tr`/`cond_it`.

Open `gurung_isolated_v1.psyexp` in PsychoPy Builder.
"""
    (out_dir / "README.md").write_text(readme, encoding="utf-8")


def build(args: argparse.Namespace) -> dict[str, object]:
    repo = Path(args.repo).expanduser().resolve()
    discourse_dir = Path(args.discourse_dir).expanduser()
    if not discourse_dir.is_absolute():
        discourse_dir = repo / discourse_dir
    discourse_dir = discourse_dir.resolve()
    out_dir = Path(args.out).expanduser()
    if not out_dir.is_absolute():
        out_dir = repo / out_dir
    out_dir = out_dir.resolve()
    template = Path(args.template).expanduser()
    if not template.is_absolute():
        template = repo / template
    template = template.resolve()

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "Conds").mkdir(exist_ok=True)
    (out_dir / "data").mkdir(exist_ok=True)
    (out_dir / "recordings").mkdir(exist_ok=True)
    copy_assets(discourse_dir, out_dir)
    image_prefix = os.path.relpath(discourse_dir, out_dir).replace("\\", "/")
    main_rows_by_list = {
        list_id: build_main_rows(discourse_dir, list_id, image_prefix)
        for list_id in sorted(discourse.LIST_RULES)
    }
    practice_rows = build_practice_rows(discourse_dir)
    for list_id, main_rows in main_rows_by_list.items():
        write_csv(out_dir / "Conds" / f"isolated_main_list{list_id}_all_120.csv", main_rows, MAIN_FIELDS)
    write_csv(out_dir / "Conds" / "isolated_practice.csv", practice_rows, PRACTICE_FIELDS)
    write_csv(out_dir / "Conds" / "isolated_practice_voiced.csv", practice_rows[:2], PRACTICE_FIELDS)
    write_csv(out_dir / "Conds" / "isolated_practice_unvoiced.csv", practice_rows[2:], PRACTICE_FIELDS)
    psyexp = build_psyexp(out_dir, template)
    write_readme(out_dir)
    tools_dir = out_dir / "tools"
    tools_dir.mkdir(exist_ok=True)
    shutil.copy2(repo / "tools" / "build_gurung_isolated.py", tools_dir / "build_gurung_isolated.py")
    source_assets_dir = repo / "tools" / "assets"
    if source_assets_dir.is_dir():
        shutil.copytree(source_assets_dir, tools_dir / "assets", dirs_exist_ok=True)

    def manifest_path(path: Path) -> str:
        try:
            return str(path.relative_to(repo)).replace("\\", "/")
        except ValueError:
            return str(path)

    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "out_dir": manifest_path(out_dir),
        "psyexp": manifest_path(psyexp),
        "discourse_dir": manifest_path(discourse_dir),
        "main_trials_per_list": 120,
        "experimental_lists": sorted(discourse.LIST_RULES),
        "practice_trials": len(practice_rows),
        "practice_blocks": [2, 8],
        "main_blocks": [60, 60],
        "resting_state_seconds_each": 120,
    }
    (out_dir / "package_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def parse_args() -> argparse.Namespace:
    repo_default = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(repo_default))
    parser.add_argument("--discourse-dir", default="psychopy_gurung_v1")
    parser.add_argument("--out", default="psychopy_gurung_isolated")
    parser.add_argument("--template", default="psychopy_gurung_v1/gurung_120_v1.psyexp")
    return parser.parse_args()


def main() -> None:
    print(json.dumps(build(parse_args()), indent=2))


if __name__ == "__main__":
    main()
