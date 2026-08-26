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


def _run_session(exp_info, win=None, close_window=True):
    global TRIGGER_HANDLE, TRIGGER_WRITER, TRIAL_HANDLE, TRIAL_WRITER, DEBUG_HANDLE, JITTER_BAG

    exp_info = dict(exp_info or {})
    exp_info.setdefault("participant", "261")
    exp_info.setdefault("eeg_port", "")
    exp_info.setdefault("trigger_pulse_ms", "5")
    if not text(exp_info.get("date", "")):
        exp_info["date"] = data.getDateStr()

    TRIGGER_HANDLE = None
    TRIGGER_WRITER = None
    TRIAL_HANDLE = None
    TRIAL_WRITER = None
    DEBUG_HANDLE = None
    JITTER_BAG = []
    CURRENT_CONTEXT.update(
        {
            "runtime_order": "",
            "original_trial_index": "",
            "dataset_number": "",
            "stimulus_set": "",
            "condition_id": "",
        }
    )
    TRIGGER_STATE.update(
        {
            "serial": None,
            "port": "",
            "pulse_ms": 5.0,
            "status": "not_initialized",
            "index": 0,
        }
    )

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
    if win is None:
        win = visual.Window(fullscr=True, color="white", units="height", allowGUI=False)
        close_window = True

    try:
        wait_blank_start(win)
        for runtime_order, row in enumerate(rows, start=1):
            run_trial(win, row, runtime_order)
            if runtime_order == 40:
                show_break(win)
        show_finish(win)
    finally:
        close_serial()
        if close_window:
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
        TRIAL_HANDLE = None
        TRIAL_WRITER = None
        TRIGGER_HANDLE = None
        TRIGGER_WRITER = None
        DEBUG_HANDLE = None


def run_from_builder(builder_win, builder_exp_info):
    _run_session(builder_exp_info, win=builder_win, close_window=False)


def main():
    exp_info = {
        "participant": "261",
        "eeg_port": "",
        "trigger_pulse_ms": "5",
    }
    dlg = gui.DlgFromDict(dictionary=exp_info, sortKeys=False, title="Discourse recovery 261 first 80")
    if not dlg.OK:
        core.quit()
    exp_info["date"] = data.getDateStr()
    _run_session(exp_info, win=None, close_window=True)



if __name__ == "__main__":
    main()
