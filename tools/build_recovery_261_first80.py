# -*- coding: utf-8 -*-
"""Build the discourse recovery experiment for participant 261, List 1, first 80 trials.

The screenshots of the recording folder show original trial number, dataset number, and
condition. They do not show the hidden stimulus_set, so this builder selects the next
legal List 1 row for each visible dataset+condition pair and records that inference in
the generated CSV. If exact runtime_main_block*.csv files from the original laptop are
available later, rebuild this file from those rows instead.
"""

from __future__ import annotations

import csv
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DISCOURSE_ROOT = REPO_ROOT / "discourse part"
SOURCE_CSV = DISCOURSE_ROOT / "Conds" / "main_list1_all_240.csv"
RECOVERY_DIR = REPO_ROOT / "discourse recovery 261 first80"
COND_DIR = RECOVERY_DIR / "Conds"
TRIALS_CSV = COND_DIR / "recovery_261_first80_trials.csv"
SCRIPT_PATH = RECOVERY_DIR / "recovery_261_first80.py"
README_PATH = RECOVERY_DIR / "README_recovery_261_first80.md"

OBSERVED_TRIALS = [
    (1, 13, "it_coh"),
    (2, 1, "it_ic"),
    (3, 27, "it_coh"),
    (4, 26, "tr_ic"),
    (5, 12, "it_coh"),
    (6, 8, "tr_coh"),
    (7, 24, "it_ic"),
    (8, 1, "it_coh"),
    (9, 12, "tr_coh"),
    (10, 30, "tr_coh"),
    (11, 22, "it_ic"),
    (12, 11, "it_ic"),
    (13, 21, "tr_coh"),
    (14, 6, "it_ic"),
    (15, 21, "it_coh"),
    (16, 17, "it_coh"),
    (17, 26, "it_ic"),
    (18, 4, "it_coh"),
    (19, 2, "it_coh"),
    (20, 19, "tr_ic"),
    (21, 25, "it_coh"),
    (22, 7, "tr_ic"),
    (23, 30, "it_ic"),
    (24, 25, "tr_ic"),
    (25, 4, "tr_coh"),
    (26, 23, "it_ic"),
    (27, 11, "it_coh"),
    (28, 14, "it_ic"),
    (29, 24, "it_coh"),
    (30, 10, "it_ic"),
    (31, 12, "it_ic"),
    (32, 6, "it_coh"),
    (33, 23, "tr_ic"),
    (34, 26, "tr_ic"),
    (35, 14, "it_ic"),
    (36, 23, "tr_coh"),
    (37, 2, "it_ic"),
    (38, 1, "tr_ic"),
    (39, 18, "tr_ic"),
    (40, 22, "tr_ic"),
    (41, 24, "tr_ic"),
    (42, 10, "tr_ic"),
    (43, 14, "it_coh"),
    (44, 19, "it_coh"),
    (45, 17, "tr_coh"),
    (46, 15, "tr_ic"),
    (47, 7, "it_coh"),
    (48, 3, "tr_ic"),
    (49, 22, "it_coh"),
    (50, 3, "it_coh"),
    (51, 15, "tr_ic"),
    (52, 18, "it_ic"),
    (53, 4, "tr_ic"),
    (54, 30, "it_ic"),
    (55, 26, "it_coh"),
    (56, 11, "tr_coh"),
    (57, 29, "tr_coh"),
    (58, 29, "tr_coh"),
    (59, 13, "tr_coh"),
    (60, 22, "tr_ic"),
    (61, 18, "it_coh"),
    (62, 28, "it_coh"),
    (63, 10, "it_coh"),
    (64, 15, "it_ic"),
    (65, 8, "it_coh"),
    (66, 16, "tr_ic"),
    (67, 11, "tr_coh"),
    (68, 29, "it_coh"),
    (69, 23, "it_coh"),
    (70, 25, "it_ic"),
    (71, 14, "tr_coh"),
    (72, 5, "tr_ic"),
    (73, 21, "tr_ic"),
    (74, 21, "it_ic"),
    (75, 20, "tr_coh"),
    (76, 26, "it_ic"),
    (77, 9, "tr_coh"),
    (78, 8, "it_ic"),
    (79, 24, "tr_coh"),
    (80, 1, "tr_coh"),
]


def as_int(value: object) -> int:
    return int(float(str(value).strip()))


def load_source_rows() -> list[dict[str, str]]:
    if not SOURCE_CSV.is_file():
        raise FileNotFoundError(f"Missing source CSV: {SOURCE_CSV}")
    with SOURCE_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def build_trial_rows() -> list[dict[str, str]]:
    source_rows = load_source_rows()
    selected: list[dict[str, str]] = []
    used_trial_ids: set[str] = set()

    for original_trial, dataset_number, condition_id in OBSERVED_TRIALS:
        candidates = [
            row
            for row in source_rows
            if as_int(row.get("dataset_number", "0")) == dataset_number
            and str(row.get("condition_id", "")).strip() == condition_id
        ]
        candidates.sort(key=lambda row: as_int(row.get("stimulus_set", "0")))
        unused = [row for row in candidates if row.get("trial_id", "") not in used_trial_ids]
        if not unused:
            candidate_ids = ", ".join(row.get("trial_id", "") for row in candidates)
            raise RuntimeError(
                f"No unused List 1 candidate for original trial {original_trial}: "
                f"imageset{dataset_number:02d} {condition_id}; candidates={candidate_ids}"
            )
        chosen = dict(unused[0])
        used_trial_ids.add(chosen.get("trial_id", ""))
        chosen["original_trial_index"] = str(original_trial)
        chosen["recovery_source"] = "recording_folder_screenshots_2026-08-26"
        chosen["candidate_stimulus_sets"] = "|".join(str(as_int(row.get("stimulus_set", "0"))) for row in candidates)
        chosen["stimulus_set_inference"] = (
            "inferred_from_visible_dataset_and_condition; screenshots_do_not_show_hidden_stimulus_set"
        )
        selected.append(chosen)

    if len(selected) != 80:
        raise RuntimeError(f"Expected 80 selected trials, got {len(selected)}")
    return selected


EXPERIMENT_SCRIPT = r'''
# -*- coding: utf-8 -*-
"""Recovery experiment: participant 261, discourse List 1, first 80 missed EEG trials.

Open this file in PsychoPy Coder and press Run. The task begins with a blank white
screen; press SPACE to start. Trials are randomly shuffled on every run and split into
2 parts of 40 trials with a 30-second break in the middle.
"""

from __future__ import annotations

import csv
import datetime as _datetime
import gc
import random
from pathlib import Path

from psychopy import core, data, event, gui, logging, visual

try:
    import serial as _serial
except Exception as _serial_error:
    _serial = None
    print("Serial trigger backend is unavailable:", _serial_error)

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DISCOURSE_ROOT = REPO_ROOT / "discourse part"
COND_FILE = SCRIPT_DIR / "Conds" / "recovery_261_first80_trials.csv"
DATA_DIR = SCRIPT_DIR / "data"
RECORDINGS_DIR = SCRIPT_DIR / "recordings"
DATA_DIR.mkdir(exist_ok=True)
RECORDINGS_DIR.mkdir(exist_ok=True)

IMAGE_ASPECT = 2.0 / 3.0
SEQUENCE_X_MARGIN = 0.02
SEQUENCE_Y_MARGIN = 0.05
SEQUENCE_GAP_RATIO = 0.12
SEQUENCE_SIZE_COUNT = 5
SEQUENCE_JITTER_SLOTS = [
    (-0.30, -0.018),
    (-0.22, 0.018),
    (-0.18, -0.018),
    (-0.06, 0.018),
    (0.06, -0.018),
    (0.18, 0.018),
    (0.22, -0.018),
    (0.30, 0.018),
]
ARROW_MAX_SIZE = 0.045
BREAK_MIN_SEC = 30.0

TRIGGER_FIRST_PRETARGET = 198
TRIGGER_PRETARGET = 199
TRIGGER_TARGET = 200
TRIGGER_AFTER_TARGET = 201
TRIGGER_TRIAL_END = 202

TRIGGER_STATE = {
    "serial": None,
    "port": "",
    "pulse_ms": 5.0,
    "status": "not_initialized",
    "index": 0,
}
CURRENT_CONTEXT = {
    "runtime_order": "",
    "original_trial_index": "",
    "dataset_number": "",
    "stimulus_set": "",
    "condition_id": "",
}
JITTER_BAG = []
TRIGGER_HANDLE = None
TRIGGER_WRITER = None
TRIAL_HANDLE = None
TRIAL_WRITER = None
DEBUG_HANDLE = None


def safe(value):
    text = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in str(value))
    while "__" in text:
        text = text.replace("__", "_")
    return text.strip("._") or "value"


def text(value):
    if value is None:
        return ""
    value = str(value).strip()
    if value.lower() in {"none", "nan", "null"}:
        return ""
    return value


def as_int(value, default=0):
    try:
        value = text(value)
        if value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def as_float(value, default=0.0):
    try:
        value = text(value)
        if value == "":
            return default
        return float(value)
    except Exception:
        return default


def asset_path(relative_value):
    relative_value = text(relative_value)
    if not relative_value:
        return ""
    path = Path(relative_value)
    if path.is_absolute():
        return str(path)
    local_path = SCRIPT_DIR / path
    if local_path.is_file():
        return str(local_path)
    return str(DISCOURSE_ROOT / path)


def log_debug(message):
    if DEBUG_HANDLE is None:
        return
    DEBUG_HANDLE.write(f"{core.getTime():.6f}\t{message}\n")
    DEBUG_HANDLE.flush()


def open_serial(port, pulse_ms):
    TRIGGER_STATE["port"] = port
    TRIGGER_STATE["pulse_ms"] = max(0.0, as_float(pulse_ms, 5.0))
    if not port:
        TRIGGER_STATE["status"] = "disabled_blank_port"
        log_debug("trigger_serial_disabled blank_port")
        return
    if _serial is None:
        TRIGGER_STATE["status"] = "unavailable_missing_pyserial"
        log_debug("trigger_serial_unavailable missing_pyserial")
        return
    try:
        TRIGGER_STATE["serial"] = _serial.Serial(port=port, baudrate=115200, timeout=0)
        TRIGGER_STATE["status"] = "open"
        log_debug(f"trigger_serial_opened port={port} pulse_ms={TRIGGER_STATE['pulse_ms']}")
    except Exception as err:
        TRIGGER_STATE["serial"] = None
        TRIGGER_STATE["status"] = "open_failed"
        log_debug(f"trigger_serial_open_failed port={port} err={err}")


def close_serial():
    serial_port = TRIGGER_STATE.get("serial")
    TRIGGER_STATE["serial"] = None
    if serial_port is None:
        return
    try:
        serial_port.write(bytes([0]))
        serial_port.flush()
    except Exception:
        pass
    try:
        serial_port.close()
        TRIGGER_STATE["status"] = "closed"
        log_debug("trigger_serial_closed")
    except Exception as err:
        TRIGGER_STATE["status"] = "close_failed"
        log_debug(f"trigger_serial_close_failed {err}")


def log_trigger(code, label, send_mode, serial_sent, details):
    if TRIGGER_WRITER is None:
        return
    TRIGGER_STATE["index"] = int(TRIGGER_STATE.get("index", 0)) + 1
    row = {
        "trigger_index": TRIGGER_STATE["index"],
        "local_time": _datetime.datetime.now().isoformat(timespec="milliseconds"),
        "core_time": f"{core.getTime():.6f}",
        "runtime_order": CURRENT_CONTEXT.get("runtime_order", ""),
        "original_trial_index": CURRENT_CONTEXT.get("original_trial_index", ""),
        "dataset_number": CURRENT_CONTEXT.get("dataset_number", ""),
        "stimulus_set": CURRENT_CONTEXT.get("stimulus_set", ""),
        "condition_id": CURRENT_CONTEXT.get("condition_id", ""),
        "trigger_code": int(code),
        "label": label,
        "send_mode": send_mode,
        "serial_port": TRIGGER_STATE.get("port", ""),
        "serial_status": TRIGGER_STATE.get("status", ""),
        "serial_sent": "1" if serial_sent else "0",
        "pulse_ms": f"{as_float(TRIGGER_STATE.get('pulse_ms', 0), 0.0):.3f}",
        "details": details,
    }
    TRIGGER_WRITER.writerow(row)
    TRIGGER_HANDLE.flush()


def send_trigger(code, label="", send_mode="immediate"):
    code = as_int(code, 0)
    if code <= 0 or code > 255:
        log_trigger(code, label, send_mode, False, "invalid_code")
        return
    serial_port = TRIGGER_STATE.get("serial")
    serial_sent = False
    details = text(TRIGGER_STATE.get("status", ""))
    if serial_port is not None:
        try:
            serial_port.write(bytes([code]))
            serial_port.flush()
            pulse_sec = max(0.0, as_float(TRIGGER_STATE.get("pulse_ms", 5.0), 5.0) / 1000.0)
            if pulse_sec:
                core.wait(pulse_sec)
            serial_port.write(bytes([0]))
            serial_port.flush()
            serial_sent = True
            details = "serial_sent"
        except Exception as err:
            TRIGGER_STATE["status"] = "send_failed"
            details = f"serial_error={err}"
            log_debug(f"trigger_serial_send_failed code={code} label={label} err={err}")
    log_trigger(code, label, send_mode, serial_sent, details)
    log_debug(f"trigger code={code} label={label} mode={send_mode} serial_sent={serial_sent} details={details}")


def trigger_on_flip(win, code, label=""):
    try:
        win.callOnFlip(send_trigger, code, label, "on_flip")
    except Exception as err:
        log_debug(f"trigger_call_on_flip_failed code={code} label={label} err={err}")
        send_trigger(code, label, "on_flip_fallback")


def load_trials():
    if not COND_FILE.is_file():
        raise FileNotFoundError(f"Missing recovery trial file: {COND_FILE}")
    with COND_FILE.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 80:
        raise RuntimeError(f"Expected 80 recovery trials, found {len(rows)} in {COND_FILE}")
    random.shuffle(rows)
    return rows


def roles_and_paths(row):
    roles = []
    paths = []
    for idx in range(1, 5):
        image_value = text(row.get(f"img{idx}", ""))
        role_value = text(row.get(f"img{idx}_role", ""))
        if image_value:
            path = asset_path(image_value)
            if not Path(path).is_file():
                raise FileNotFoundError(f"Missing stimulus image: {path}")
            paths.append(path)
            roles.append(role_value or f"img{idx}")
    return roles, paths


def target_index(roles):
    for role in ("tr_target", "it_target"):
        if role in roles:
            return roles.index(role)
    return max(0, len(roles) - 1)


def segment_trigger(roles, segment_index):
    target = int(target_index(roles))
    if segment_index < target - 1:
        return TRIGGER_FIRST_PRETARGET
    if segment_index == target - 1:
        return TRIGGER_PRETARGET
    if segment_index == target:
        return TRIGGER_TARGET
    if segment_index > target:
        return TRIGGER_AFTER_TARGET
    return 0


def window_aspect(win):
    try:
        return max(float(win.size[0]) / float(win.size[1]), 1.0)
    except Exception:
        return 1.5


def next_jitter():
    global JITTER_BAG
    if not JITTER_BAG:
        JITTER_BAG = list(SEQUENCE_JITTER_SLOTS)
        random.shuffle(JITTER_BAG)
    return JITTER_BAG.pop()


def sequence_layout(win, roles):
    sequence_count = max(1, len(roles))
    size_count = max(SEQUENCE_SIZE_COUNT, sequence_count)
    jitter_x_width_max = max(abs(pos[0]) for pos in SEQUENCE_JITTER_SLOTS)
    jitter_y_max = max(abs(pos[1]) for pos in SEQUENCE_JITTER_SLOTS)
    horizontal_room = max(0.1, window_aspect(win) - (2 * SEQUENCE_X_MARGIN))
    vertical_room = max(0.1, 1.0 - (2 * (SEQUENCE_Y_MARGIN + jitter_y_max)))
    width_from_horizontal = horizontal_room / (
        size_count + ((size_count - 1) * SEQUENCE_GAP_RATIO) + (2 * jitter_x_width_max)
    )
    image_height = min(vertical_room, width_from_horizontal / IMAGE_ASPECT)
    image_width = image_height * IMAGE_ASPECT
    gap = image_width * SEQUENCE_GAP_RATIO
    step = image_width + gap
    row_center = (len(roles) - 1) / 2.0
    jitter_x_factor, jitter_y = next_jitter()
    jitter_x = jitter_x_factor * image_width
    positions = [((idx - row_center) * step + jitter_x, jitter_y) for idx in range(len(roles))]
    arrow_size = min(ARROW_MAX_SIZE, max(0.02, gap * 0.9))
    return (image_width, image_height), positions, (arrow_size, arrow_size), (jitter_x, jitter_y)


def make_arrow(win, pos, size):
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


def make_sequence(win, roles, paths):
    image_size, positions, arrow_size, jitter = sequence_layout(win, roles)
    images = [visual.ImageStim(win, image=path, pos=pos, size=image_size, interpolate=True) for path, pos in zip(paths, positions)]
    arrows = [make_arrow(win, ((left[0] + right[0]) / 2, (left[1] + right[1]) / 2), arrow_size) for left, right in zip(positions, positions[1:])]
    log_debug(f"make_sequence roles={roles} jitter={jitter} paths={paths}")
    return images, arrows, jitter


def release_stims(*groups):
    for group in groups:
        if not group:
            continue
        for stim in group:
            try:
                clear_textures = getattr(stim, "clearTextures", None)
                if clear_textures is not None:
                    clear_textures()
            except Exception:
                pass
    gc.collect()


def draw_sequence(win, images, arrows, reveal_count):
    win.color = "white"
    for idx in range(reveal_count):
        images[idx].draw()
    for idx in range(max(0, reveal_count - 1)):
        arrows[idx].draw()


def wait_blank_start(win):
    win.color = "white"
    event.clearEvents()
    while True:
        win.flip()
        keys = event.getKeys(keyList=["space", "escape"])
        if "escape" in keys:
            raise KeyboardInterrupt
        if "space" in keys:
            event.clearEvents()
            return


def show_break(win):
    pause_path = Path(asset_path("Stimuli/break.png"))
    pause_stim = visual.ImageStim(win, image=str(pause_path), pos=(0, 0), size=(0.22, 0.22), interpolate=True)
    timer = core.Clock()
    event.clearEvents()
    while True:
        win.color = "white"
        pause_stim.draw()
        win.flip()
        keys = event.getKeys(keyList=["space", "escape"])
        if "escape" in keys:
            raise KeyboardInterrupt
        if "space" in keys and timer.getTime() >= BREAK_MIN_SEC:
            event.clearEvents()
            release_stims([pause_stim])
            return


def show_finish(win):
    finish_path = Path(asset_path("Stimuli/finish.png"))
    finish_stim = visual.ImageStim(win, image=str(finish_path), pos=(0, 0), size=(0.55, 0.275), interpolate=True)
    event.clearEvents()
    while True:
        win.color = "white"
        finish_stim.draw()
        win.flip()
        keys = event.getKeys(keyList=["space", "escape"])
        if "space" in keys or "escape" in keys:
            release_stims([finish_stim])
            return


def mark_started(state):
    state["started"] = True
    state["core_time"] = core.getTime()


def run_trial(win, row, runtime_order):
    roles, paths = roles_and_paths(row)
    images, arrows, jitter = make_sequence(win, roles, paths)
    target = int(target_index(roles))
    condition_trigger = as_int(row.get("condition_trigger", "0"), 0)
    item_trigger = as_int(row.get("item_trigger", "0"), 0)
    original_trial = as_int(row.get("original_trial_index", "0"), 0)
    dataset_number = as_int(row.get("dataset_number", "0"), 0)
    stimulus_set = as_int(row.get("stimulus_set", "0"), 0)
    condition_id = text(row.get("condition_id", ""))

    CURRENT_CONTEXT.update(
        {
            "runtime_order": runtime_order,
            "original_trial_index": original_trial,
            "dataset_number": dataset_number,
            "stimulus_set": stimulus_set,
            "condition_id": condition_id,
        }
    )

    segment_rts = []
    trial_clock = core.Clock()
    for segment in range(len(images)):
        event.clearEvents()
        segment_clock = core.Clock()
        target_clock = core.Clock()
        target_state = {"started": False, "condition_sent": False, "item_sent": False}
        trigger_scheduled = False
        while True:
            draw_sequence(win, images, arrows, segment + 1)
            if not trigger_scheduled:
                code = segment_trigger(roles, segment)
                if code:
                    trigger_on_flip(
                        win,
                        code,
                        f"recovery_runtime{runtime_order:03d}_original{original_trial:03d}_set{stimulus_set}_seg{segment + 1}_{roles[segment]}",
                    )
                if segment == target:
                    win.callOnFlip(target_clock.reset)
                    win.callOnFlip(mark_started, target_state)
                trigger_scheduled = True
            win.flip()

            if target_state.get("started"):
                if (not target_state.get("condition_sent")) and target_clock.getTime() >= 0.200:
                    send_trigger(
                        condition_trigger,
                        f"recovery_runtime{runtime_order:03d}_original{original_trial:03d}_condition_{condition_id}",
                    )
                    target_state["condition_sent"] = True
                if (not target_state.get("item_sent")) and target_clock.getTime() >= 0.400:
                    send_trigger(
                        item_trigger,
                        f"recovery_runtime{runtime_order:03d}_original{original_trial:03d}_item{item_trigger:03d}",
                    )
                    target_state["item_sent"] = True

            keys = event.getKeys(keyList=["space", "escape"], timeStamped=core.monotonicClock)
            key_names = [key[0] if isinstance(key, tuple) else key for key in keys]
            if "escape" in key_names:
                raise KeyboardInterrupt
            can_advance = segment != target or target_state.get("item_sent")
            if "space" in key_names and can_advance:
                segment_rts.append(f"{segment_clock.getTime():.6f}")
                if segment >= len(images) - 1:
                    send_trigger(TRIGGER_TRIAL_END, f"recovery_runtime{runtime_order:03d}_original{original_trial:03d}_end")
                event.clearEvents()
                break

    TRIAL_WRITER.writerow(
        {
            "runtime_order": runtime_order,
            "original_trial_index": original_trial,
            "dataset_number": dataset_number,
            "stimulus_set": stimulus_set,
            "condition_id": condition_id,
            "condition_trigger": condition_trigger,
            "item_trigger": item_trigger,
            "n_images": len(images),
            "roles": "|".join(roles),
            "paths": "|".join(paths),
            "jitter_x": f"{jitter[0]:.6f}",
            "jitter_y": f"{jitter[1]:.6f}",
            "segment_rts": "|".join(segment_rts),
            "trial_duration": f"{trial_clock.getTime():.6f}",
        }
    )
    TRIAL_HANDLE.flush()
    release_stims(images, arrows)


def write_runtime_order(rows, path):
    fieldnames = list(rows[0].keys())
    if "runtime_order" not in fieldnames:
        fieldnames = ["runtime_order"] + fieldnames
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for index, row in enumerate(rows, start=1):
            out = dict(row)
            out["runtime_order"] = index
            writer.writerow(out)


def main():
    global TRIGGER_HANDLE, TRIGGER_WRITER, TRIAL_HANDLE, TRIAL_WRITER, DEBUG_HANDLE

    exp_info = {
        "participant": "261",
        "eeg_port": "",
        "trigger_pulse_ms": "5",
    }
    dlg = gui.DlgFromDict(dictionary=exp_info, sortKeys=False, title="Discourse recovery 261 first 80")
    if not dlg.OK:
        core.quit()
    exp_info["date"] = data.getDateStr()

    participant = safe(exp_info.get("participant", "261"))
    session_dir = RECORDINGS_DIR / f"{participant}_recovery_l1_first80_{safe(exp_info['date'])}"
    session_dir.mkdir(parents=True, exist_ok=True)

    DEBUG_HANDLE = (session_dir / "debug_recovery_runtime.log").open("w", encoding="utf-8")
    TRIGGER_HANDLE = (session_dir / "eeg_triggers.csv").open("w", encoding="utf-8", newline="")
    trigger_fields = [
        "trigger_index",
        "local_time",
        "core_time",
        "runtime_order",
        "original_trial_index",
        "dataset_number",
        "stimulus_set",
        "condition_id",
        "trigger_code",
        "label",
        "send_mode",
        "serial_port",
        "serial_status",
        "serial_sent",
        "pulse_ms",
        "details",
    ]
    TRIGGER_WRITER = csv.DictWriter(TRIGGER_HANDLE, fieldnames=trigger_fields, lineterminator="\n")
    TRIGGER_WRITER.writeheader()
    TRIGGER_HANDLE.flush()

    TRIAL_HANDLE = (session_dir / "trial_log.csv").open("w", encoding="utf-8", newline="")
    trial_fields = [
        "runtime_order",
        "original_trial_index",
        "dataset_number",
        "stimulus_set",
        "condition_id",
        "condition_trigger",
        "item_trigger",
        "n_images",
        "roles",
        "paths",
        "jitter_x",
        "jitter_y",
        "segment_rts",
        "trial_duration",
    ]
    TRIAL_WRITER = csv.DictWriter(TRIAL_HANDLE, fieldnames=trial_fields, lineterminator="\n")
    TRIAL_WRITER.writeheader()
    TRIAL_HANDLE.flush()

    rows = load_trials()
    write_runtime_order(rows, session_dir / "trial_order.csv")

    logging.console.setLevel(logging.WARNING)
    open_serial(text(exp_info.get("eeg_port", "")), exp_info.get("trigger_pulse_ms", "5"))
    win = visual.Window(fullscr=True, color="white", units="height", allowGUI=False)

    try:
        wait_blank_start(win)
        for runtime_order, row in enumerate(rows, start=1):
            run_trial(win, row, runtime_order)
            if runtime_order == 40:
                show_break(win)
        show_finish(win)
    finally:
        close_serial()
        try:
            win.close()
        except Exception:
            pass
        for handle in (TRIAL_HANDLE, TRIGGER_HANDLE, DEBUG_HANDLE):
            try:
                if handle is not None:
                    handle.flush()
                    handle.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()
'''.strip() + "\n"


README_TEXT = """# Discourse recovery 261 first 80

This is a minimal, self-contained recovery experiment for the first 80 discourse trials shown in the participant 261 List 1 recording-folder screenshots from 2026-08-26.

Run `recovery_261_first80.py` from PsychoPy Coder. The folder includes local copies of the needed JPEG stimuli plus the break/finish images, so it can be downloaded separately from the normal discourse and isolated experiment folders. The task starts with a blank white screen; press Space to begin. It presents only the 80 recovered discourse trials, randomly shuffled on every run, with a 30-second break after 40 trials and a finish sign at the end.

The normal discourse trigger system is preserved:

- 198 = optional early pre-target picture onset
- 199 = picture before target onset
- 200 = target picture onset
- 1-4 = condition trigger at 200 ms after target onset
- 1-120 = item trigger at 400 ms after target onset
- 201 = optional post-target picture onset
- 202 = button-press trial end

Outputs are written to `recordings/<participant>_recovery_l1_first80_<date>/`:

- `trial_order.csv`: randomized runtime order for this recovery run
- `trial_log.csv`: per-trial timing/condition/item metadata
- `eeg_triggers.csv`: every trigger attempt with serial status
- `debug_recovery_runtime.log`: compact runtime notes

Important limitation: the screenshots show original trial number, dataset number, and condition, but not the hidden `stimulus_set`. The generated `Conds/recovery_261_first80_trials.csv` therefore selects the next legal List 1 stimulus set for each visible dataset+condition pair and marks this in `stimulus_set_inference`. If the original laptop's `runtime_main_block1.csv` and `runtime_main_block2.csv` are available, use those files to rebuild an exact version.
"""

def copy_recovery_asset(relative_value: str) -> None:
    relative_value = str(relative_value or "").strip()
    if not relative_value:
        return
    rel_path = Path(relative_value)
    if rel_path.is_absolute():
        return
    source = DISCOURSE_ROOT / rel_path
    target = RECOVERY_DIR / rel_path
    if not source.is_file():
        raise FileNotFoundError(f"Missing source asset: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def copy_local_assets(selected_rows: list[dict[str, str]]) -> None:
    copied = set()
    for row in selected_rows:
        for idx in range(1, 5):
            value = str(row.get(f"img{idx}", "")).strip()
            if value and value not in copied:
                copy_recovery_asset(value)
                copied.add(value)
    for value in ("Stimuli/break.png", "Stimuli/finish.png"):
        copy_recovery_asset(value)
        copied.add(value)
    print(f"Copied {len(copied)} local recovery assets")



def write_outputs() -> None:
    RECOVERY_DIR.mkdir(exist_ok=True)
    COND_DIR.mkdir(exist_ok=True)
    (RECOVERY_DIR / "data").mkdir(exist_ok=True)
    (RECOVERY_DIR / "recordings").mkdir(exist_ok=True)

    selected_rows = build_trial_rows()
    copy_local_assets(selected_rows)
    source_fieldnames = list(load_source_rows()[0].keys())
    extra_fields = [
        "original_trial_index",
        "recovery_source",
        "candidate_stimulus_sets",
        "stimulus_set_inference",
    ]
    fieldnames = extra_fields + [field for field in source_fieldnames if field not in extra_fields]
    with TRIALS_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in selected_rows:
            writer.writerow(row)

    SCRIPT_PATH.write_text(EXPERIMENT_SCRIPT, encoding="utf-8")
    README_PATH.write_text(README_TEXT, encoding="utf-8")
    print(f"Wrote {TRIALS_CSV}")
    print(f"Wrote {SCRIPT_PATH}")
    print(f"Wrote {README_PATH}")


if __name__ == "__main__":
    write_outputs()
