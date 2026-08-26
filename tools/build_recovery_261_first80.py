# -*- coding: utf-8 -*-
"""Build the discourse recovery experiment for participant 261, List 1, first 80 trials.

The participant CSV screenshots show the exact trial_id values, including set1-set4,
for the first 80 discourse trials. This builder selects those exact List 1 rows.
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

EXACT_TRIAL_IDS = [
    "d013_set4_it_coh_list1",
    "d001_set3_it_ic_list1",
    "d027_set4_it_coh_list1",
    "d026_set1_tr_ic_list1",
    "d012_set4_it_coh_list1",
    "d008_set2_tr_coh_list1",
    "d024_set2_it_ic_list1",
    "d001_set4_it_coh_list1",
    "d012_set3_tr_coh_list1",
    "d030_set3_tr_coh_list1",
    "d022_set2_it_ic_list1",
    "d011_set3_it_ic_list1",
    "d021_set3_tr_coh_list1",
    "d006_set2_it_ic_list1",
    "d021_set4_it_coh_list1",
    "d017_set1_it_coh_list1",
    "d026_set2_it_ic_list1",
    "d004_set4_it_coh_list1",
    "d002_set4_it_coh_list1",
    "d019_set4_tr_ic_list1",
    "d025_set4_it_coh_list1",
    "d007_set1_tr_ic_list1",
    "d030_set3_it_ic_list1",
    "d025_set1_tr_ic_list1",
    "d004_set2_tr_coh_list1",
    "d023_set2_it_ic_list1",
    "d011_set4_it_coh_list1",
    "d014_set3_it_ic_list1",
    "d024_set1_it_coh_list1",
    "d010_set3_it_ic_list1",
    "d012_set3_it_ic_list1",
    "d006_set4_it_coh_list1",
    "d023_set1_tr_ic_list1",
    "d026_set4_tr_ic_list1",
    "d014_set2_it_ic_list1",
    "d023_set2_tr_coh_list1",
    "d002_set3_it_ic_list1",
    "d001_set4_tr_ic_list1",
    "d018_set1_tr_ic_list1",
    "d022_set1_tr_ic_list1",
    "d024_set1_tr_ic_list1",
    "d010_set4_tr_ic_list1",
    "d014_set4_it_coh_list1",
    "d019_set1_it_coh_list1",
    "d017_set3_tr_coh_list1",
    "d015_set4_tr_ic_list1",
    "d007_set4_it_coh_list1",
    "d003_set4_tr_ic_list1",
    "d022_set4_it_coh_list1",
    "d003_set1_it_coh_list1",
    "d015_set1_tr_ic_list1",
    "d018_set2_it_ic_list1",
    "d004_set1_tr_ic_list1",
    "d030_set2_it_ic_list1",
    "d026_set4_it_coh_list1",
    "d011_set3_tr_coh_list1",
    "d029_set3_tr_coh_list1",
    "d029_set2_tr_coh_list1",
    "d013_set3_tr_coh_list1",
    "d022_set4_tr_ic_list1",
    "d018_set1_it_coh_list1",
    "d028_set4_it_coh_list1",
    "d010_set1_it_coh_list1",
    "d015_set3_it_ic_list1",
    "d008_set4_it_coh_list1",
    "d016_set1_tr_ic_list1",
    "d011_set2_tr_coh_list1",
    "d029_set1_it_coh_list1",
    "d023_set4_it_coh_list1",
    "d025_set2_it_ic_list1",
    "d014_set2_tr_coh_list1",
    "d005_set1_tr_ic_list1",
    "d021_set1_tr_ic_list1",
    "d021_set2_it_ic_list1",
    "d020_set2_tr_coh_list1",
    "d026_set3_it_ic_list1",
    "d009_set2_tr_coh_list1",
    "d008_set2_it_ic_list1",
    "d024_set2_tr_coh_list1",
    "d001_set3_tr_coh_list1",
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
    by_trial_id = {row.get("trial_id", ""): row for row in source_rows}
    selected: list[dict[str, str]] = []

    for original_trial, trial_id in enumerate(EXACT_TRIAL_IDS, start=1):
        source = by_trial_id.get(trial_id)
        if source is None:
            raise RuntimeError(f"Trial id from participant CSV screenshot is not in List 1 source CSV: {trial_id}")
        chosen = dict(source)
        chosen["original_trial_index"] = str(original_trial)
        chosen["recovery_source"] = "participant_261_csv_screenshots_2026-08-26"
        selected.append(chosen)

    if len(selected) != 80:
        raise RuntimeError(f"Expected 80 selected trials, got {len(selected)}")
    if len({row["trial_id"] for row in selected}) != 80:
        raise RuntimeError("Recovery trial list contains duplicate trial_id values")
    return selected


EXPERIMENT_SCRIPT = r'''
# -*- coding: utf-8 -*-
"""Recovery experiment: participant 261, discourse List 1, first 80 missed EEG trials.

Open this file in PsychoPy Coder and press Run. The task begins with a blank white
screen; press SPACE to start. Trials are randomly shuffled on every run and split into
2 parts of 40 trials with a 30-second break in the middle.
"""

from __future__ import annotations

import atexit
import csv
import datetime as _datetime
import gc
import queue
import random
import threading
from pathlib import Path

from psychopy import core, data, event, gui, logging, visual

try:
    import serial as _serial
except Exception as _serial_error:
    _serial = None
    print("Serial trigger backend is unavailable:", _serial_error)

try:
    import sounddevice as _sd
    import soundfile as _sf
    RECORDING_AVAILABLE = True
except Exception as _recording_error:
    _sd = None
    _sf = None
    RECORDING_AVAILABLE = False
    print("Audio recording is unavailable:", _recording_error)

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
RECORDING_STOP_GRACE_SEC = 0.5

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
RECORDER = None
SESSION_INFO = {"participant": "261", "list_tag": "l1"}


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


def key_names(keys):
    names = []
    for key in keys or []:
        if isinstance(key, (tuple, list)) and key:
            key = key[0]
        name = getattr(key, "name", None) or getattr(key, "key", None)
        if name is None:
            name = key
        names.append(str(name))
    return names


def key_time(keys, key_name, default=None):
    if default is None:
        default = core.getTime()
    for key in keys or []:
        if isinstance(key, (tuple, list)) and key:
            if str(key[0]) == key_name and len(key) > 1:
                return as_float(key[-1], default)
        else:
            name = getattr(key, "name", None) or getattr(key, "key", None)
            if str(name or key) == key_name:
                rt = getattr(key, "rt", None)
                return as_float(rt, default) if rt is not None else default
    return default


def get_keys_with_time():
    try:
        return event.getKeys(keyList=["space", "escape"], timeStamped=core.monotonicClock)
    except Exception:
        return event.getKeys(keyList=["space", "escape"])


def wait_for_space_or_escape():
    try:
        keys = event.waitKeys(keyList=["space", "escape"], timeStamped=core.monotonicClock)
    except Exception:
        keys = event.waitKeys(keyList=["space", "escape"])
    names = key_names(keys)
    if "escape" in names:
        raise KeyboardInterrupt
    return key_time(keys, "space", core.getTime())

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


def recovery_main_stem(original_trial, dataset_number, condition_id, picture_index, role):
    participant = safe(SESSION_INFO.get("participant", "261"))
    list_tag = safe(SESSION_INFO.get("list_tag", "l1"))
    return (
        f"{participant}_main_{list_tag}_trial{int(original_trial):03d}_"
        f"imageset{int(dataset_number):02d}_cond_{safe(condition_id)}_"
        f"pic{int(picture_index):02d}_{safe(role)}"
    )


class RecoveryRecorder:
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
        if RECORDING_AVAILABLE:
            self._ensure_stream()
        else:
            self._log_event("recording_unavailable", details="sounddevice/soundfile import failed")

    def start(self, stem, subdir=None):
        self.stop()
        if not RECORDING_AVAILABLE:
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
        path = target_dir / f"{safe(stem)}.wav"
        with self.lock:
            self.segment_index += 1
            segment = {
                "id": self.segment_index,
                "stem": safe(stem),
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

    def mark_onset_on_flip(self, win):
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
        if not RECORDING_AVAILABLE:
            return

        def callback(indata, frames, time_info, status):
            if status:
                log_debug(f"rec_callback_status {status}")
            block = indata.copy()
            callback_core_time = core.getTime()
            with self.lock:
                block_start = self.total_frames
                block_end = block_start + int(frames)
                self.total_frames = block_end
                self.last_callback_core_time = callback_core_time
                self.last_callback_end_sample = block_end
            self.write_queue.put(("full", block))

        log_debug("rec_stream_open_start")
        try:
            self.full_writer = _sf.SoundFile(
                str(self.full_path),
                mode="w",
                samplerate=self.sample_rate,
                channels=1,
            )
            self.stream = _sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
                callback=callback,
            )
            self.stream.start()
            self._log_event("full_session_start", sample_index=0, details=str(self.full_path))
            log_debug("rec_stream_open_done")
        except Exception as err:
            log_debug(f"rec_stream_open_failed {err}")
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
            grace_sec = RECORDING_STOP_GRACE_SEC
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
                log_debug(f"rec_writer_loop_error {err}")
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
        if not RECORDING_AVAILABLE:
            return
        if not self.full_path.exists():
            self._log_event("segment_clip_failed", details=f"missing_full_session={self.full_path}")
            return
        try:
            with _sf.SoundFile(str(self.full_path), mode="r") as full_audio:
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
                    _sf.write(str(segment["path"]), audio, full_audio.samplerate)
                    status = "written"
                    notes = text(segment.get("notes", ""))
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
            log_debug(f"rec_full_writer_close_failed {err}")

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
            log_debug(f"recording_event_log_open_failed {err}")
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
                log_debug(f"recording_event_log_write_failed {err}")
        log_debug(f"recording_event {event_type} segment={segment_id} sample={row['sample_index']} {details}")

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
            log_debug(f"recording_segments_log_write_failed {err}")

    def _wait_for_pending_tail(self):
        deadline = core.getTime() + RECORDING_STOP_GRACE_SEC + 0.2
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
                log_debug("rec_stream_stop_start")
                stream.stop()
                log_debug("rec_stream_stop_done")
            except Exception as err:
                log_debug(f"rec_stream_stop_failed {err}")
            try:
                stream.close()
                log_debug("rec_stream_close_done")
            except Exception as err:
                log_debug(f"rec_stream_close_failed {err}")
        self._force_close_open_segments()
        try:
            self.write_queue.join()
        except Exception as err:
            log_debug(f"rec_write_queue_join_failed {err}")
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



def cleanup_recorder(wait_for_post_pad=True):
    global RECORDER
    try:
        if RECORDER is not None:
            RECORDER.finalize(wait_for_post_pad=wait_for_post_pad)
    except Exception as err:
        log_debug(f"recorder_cleanup_failed {err}")

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
    segment_audio_files = []
    trial_clock = core.Clock()
    try:
        for segment in range(len(images)):
            segment_clock = core.Clock()
            target_clock = core.Clock()
            target_state = {"started": False, "condition_sent": False, "item_sent": False}
            advance_requested = False
            advance_core_time = None
            event.clearEvents(eventType="keyboard")

            stem = recovery_main_stem(original_trial, dataset_number, condition_id, segment + 1, roles[segment])
            audio_file = ""
            if RECORDER is not None:
                audio_file = RECORDER.start(stem)
            segment_audio_files.append(audio_file)

            draw_sequence(win, images, arrows, segment + 1)
            code = segment_trigger(roles, segment)
            if code:
                trigger_on_flip(
                    win,
                    code,
                    f"recovery_runtime{runtime_order:03d}_original{original_trial:03d}_set{stimulus_set}_seg{segment + 1}_{roles[segment]}",
                )
            if RECORDER is not None:
                RECORDER.mark_onset_on_flip(win)
            if segment == target:
                win.callOnFlip(target_clock.reset)
                win.callOnFlip(mark_started, target_state)
            win.flip()

            if segment != target:
                advance_core_time = wait_for_space_or_escape()
                if RECORDER is not None:
                    RECORDER.stop(event_core_time=advance_core_time)
                segment_rts.append(f"{segment_clock.getTime():.6f}")
                continue

            if not target_state.get("started"):
                target_clock.reset()
                mark_started(target_state)

            while True:
                draw_sequence(win, images, arrows, segment + 1)
                win.flip()

                elapsed = target_clock.getTime()
                if (not target_state.get("condition_sent")) and elapsed >= 0.200:
                    send_trigger(
                        condition_trigger,
                        f"recovery_runtime{runtime_order:03d}_original{original_trial:03d}_condition_{condition_id}",
                    )
                    target_state["condition_sent"] = True
                if (not target_state.get("item_sent")) and elapsed >= 0.400:
                    send_trigger(
                        item_trigger,
                        f"recovery_runtime{runtime_order:03d}_original{original_trial:03d}_item{item_trigger:03d}",
                    )
                    target_state["item_sent"] = True

                keys = get_keys_with_time()
                names = key_names(keys)
                if "escape" in names:
                    raise KeyboardInterrupt
                if "space" in names and not advance_requested:
                    advance_requested = True
                    advance_core_time = key_time(keys, "space", core.getTime())
                if advance_requested and target_state.get("item_sent"):
                    if RECORDER is not None:
                        RECORDER.stop(event_core_time=advance_core_time)
                    segment_rts.append(f"{segment_clock.getTime():.6f}")
                    break

        send_trigger(TRIGGER_TRIAL_END, f"recovery_runtime{runtime_order:03d}_original{original_trial:03d}_end")
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
                "segment_audio_files": "|".join(segment_audio_files),
                "trial_duration": f"{trial_clock.getTime():.6f}",
            }
        )
        TRIAL_HANDLE.flush()
    finally:
        if RECORDER is not None:
            RECORDER.stop(grace_sec=0.0)
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
    global TRIGGER_HANDLE, TRIGGER_WRITER, TRIAL_HANDLE, TRIAL_WRITER, DEBUG_HANDLE, JITTER_BAG, RECORDER

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
    RECORDER = None
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
    SESSION_INFO["participant"] = participant
    SESSION_INFO["list_tag"] = "l1"
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
        "segment_audio_files",
        "trial_duration",
    ]
    TRIAL_WRITER = csv.DictWriter(TRIAL_HANDLE, fieldnames=trial_fields, lineterminator="\n")
    TRIAL_WRITER.writeheader()
    TRIAL_HANDLE.flush()

    RECORDER = RecoveryRecorder(session_dir)
    try:
        atexit.register(cleanup_recorder)
    except Exception as err:
        log_debug(f"recorder_atexit_register_failed {err}")

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
        cleanup_recorder(wait_for_post_pad=True)
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
        RECORDER = None


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
'''.strip() + "\n"


README_TEXT = """# Discourse recovery 261 first 80

This is a minimal, self-contained recovery experiment for the first 80 discourse trials shown in the participant 261 List 1 CSV screenshots from 2026-08-26.

Open `recovery_261_first80.psyexp` in PsychoPy Builder, or run `recovery_261_first80.py` from PsychoPy Coder. The folder includes local copies of the needed JPEG stimuli plus the break/finish images, so it can be downloaded separately from the normal discourse and isolated experiment folders. The task starts with a blank white screen; press Space to begin. It presents only the 80 recovered discourse trials, randomly shuffled on every run, with a 30-second break after 40 trials and a finish sign at the end.

The normal discourse trigger system is preserved:

- 198 = optional early pre-target picture onset
- 199 = picture before target onset
- 200 = target picture onset
- 1-4 = condition trigger at 200 ms after target onset
- 1-120 = item trigger at 400 ms after target onset
- 201 = optional post-target picture onset
- 202 = button-press trial end

Outputs are written to `recordings/<participant>_recovery_l1_first80_<date>/`:

- Per-picture response WAV clips use the original discourse naming style, for example `261_main_l1_trial016_imageset17_cond_it_coh_pic03_it_target.wav`.
- `full_session.wav`: continuous raw microphone recording for the whole recovery run.
- `recording_events.csv` and `recording_segments.csv`: reproducible logs of picture-onset samples, Space-press stop samples, and clip boundaries.
- `trial_order.csv`: randomized runtime order for this recovery run.
- `trial_log.csv`: per-trial timing/condition/item metadata, including per-picture audio filenames.
- `eeg_triggers.csv`: every trigger attempt with serial status.
- `debug_recovery_runtime.log`: compact runtime notes.

This version uses the exact `trial_id` values visible in the participant CSV screenshots, including the `set1`/`set2`/`set3`/`set4` part of each item.
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
