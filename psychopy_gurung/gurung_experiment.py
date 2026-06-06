#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path


EXP_NAME = "gurung"
ROOT = Path(__file__).resolve().parent
CONDITIONS_DIR = ROOT / "Conds"
DATA_DIR = ROOT / "data"
RECORDINGS_DIR = ROOT / "recordings"

EVENT_FIELDS = [
    "participant",
    "session",
    "list",
    "practice",
    "trial_index",
    "trial_id",
    "dataset_number",
    "dataset_slug",
    "set_id",
    "condition_id",
    "condition_name",
    "cohesion",
    "transitivity",
    "segment_index",
    "segment_role",
    "image_path",
    "image_onset_unix",
    "response_time_sec",
    "audio_file",
]


def as_bool(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def safe_name(value: object) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value).strip())
    slug = re.sub(r"_+", "_", slug).strip("._")
    return slug or "item"


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def image_paths(row: dict[str, str]) -> list[tuple[str, Path]]:
    items: list[tuple[str, Path]] = []
    for index in range(1, 5):
        image = row.get(f"img{index}", "").strip()
        if not image:
            continue
        path = Path(image)
        if not path.is_absolute():
            path = ROOT / path
        items.append((row.get(f"img{index}_role", f"img{index}"), path))
    return items


def split_half(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    half = len(rows) // 2
    return rows[:half], rows[half:]


class AudioRecorder:
    def __init__(self, recording_dir: Path, enabled: bool, sample_rate: int = 48000) -> None:
        self.enabled = enabled
        self.recording_dir = recording_dir
        self.sample_rate = sample_rate
        self.stream = None
        self.frames = []
        self.start_time = 0.0
        self.current_file: Path | None = None
        if not enabled:
            return
        try:
            import numpy as np  # noqa: F401
            import sounddevice as sd  # noqa: F401
            import soundfile as sf  # noqa: F401
        except Exception as exc:  # pragma: no cover - depends on local audio stack
            raise RuntimeError(
                "Audio recording requested, but sounddevice/soundfile/numpy are not available "
                "in this PsychoPy Python. Install them or set record_audio to no."
            ) from exc
        self.recording_dir.mkdir(parents=True, exist_ok=True)

    def start(self, filename_stem: str) -> None:
        if not self.enabled:
            self.current_file = None
            return
        import sounddevice as sd

        self.frames = []
        self.current_file = self.recording_dir / f"{safe_name(filename_stem)}.wav"

        def callback(indata, frames, time_info, status):  # noqa: ANN001
            if status:
                print(status, file=sys.stderr)
            self.frames.append(indata.copy())

        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            callback=callback,
        )
        self.stream.start()
        self.start_time = time.time()

    def stop(self) -> str:
        if not self.enabled or self.stream is None or self.current_file is None:
            self.stream = None
            return ""
        import numpy as np
        import soundfile as sf

        self.stream.stop()
        self.stream.close()
        self.stream = None
        if self.frames:
            audio = np.concatenate(self.frames, axis=0)
            sf.write(self.current_file, audio, self.sample_rate)
            return str(self.current_file)
        return ""

    def abort(self) -> None:
        if self.stream is not None:
            self.stream.abort()
            self.stream.close()
            self.stream = None


def get_exp_info(gui_module) -> dict[str, str]:
    default = {
        "participant": f"{random.randint(0, 999999):06d}",
        "session": "001",
        "list": "1",
        "practice": "no",
        "record_audio": "yes",
        "fullscreen": "yes",
        "random_seed": "",
    }
    dlg = gui_module.DlgFromDict(default, title="Gurung", order=list(default))
    if not dlg.OK:
        raise SystemExit(0)
    return {key: str(value) for key, value in default.items()}


def condition_file_for(exp_info: dict[str, str]) -> Path:
    list_value = safe_name(exp_info.get("list", "1"))
    if list_value.endswith(".csv"):
        return CONDITIONS_DIR / list_value
    return CONDITIONS_DIR / f"trials_list{list_value}.csv"


def draw_text_screen(win, visual, event, text: str) -> None:
    message = visual.TextStim(
        win,
        text=text,
        color="white",
        height=0.032,
        wrapWidth=1.25,
        alignText="center",
        pos=(0, 0),
    )
    event.clearEvents()
    while True:
        message.draw()
        win.flip()
        keys = event.getKeys(keyList=["space", "escape"])
        if "escape" in keys:
            raise KeyboardInterrupt
        if "space" in keys:
            return


def make_layout(n_images: int) -> tuple[list[float], tuple[float, float]]:
    if n_images <= 3:
        return [-0.5, 0.0, 0.5][:n_images], (0.38, 0.57)
    return [-0.57, -0.19, 0.19, 0.57][:n_images], (0.28, 0.42)


def make_trial_stims(win, visual, row: dict[str, str]) -> tuple[list[object], list[object], list[object], list[tuple[str, Path]]]:
    items = image_paths(row)
    positions, size = make_layout(len(items))
    images = []
    masks = []
    labels = []
    for index, ((role, path), xpos) in enumerate(zip(items, positions), start=1):
        if not path.exists():
            raise FileNotFoundError(f"Missing image for {row['trial_id']}: {path}")
        images.append(visual.ImageStim(win, image=str(path), pos=(xpos, 0), size=size, interpolate=True))
        masks.append(
            visual.Rect(
                win,
                pos=(xpos, 0),
                width=size[0],
                height=size[1],
                fillColor=(-0.98, -0.98, -0.98),
                lineColor=(-0.55, -0.55, -0.55),
            )
        )
        labels.append(
            visual.TextStim(
                win,
                text=str(index),
                pos=(xpos, 0),
                color=(-0.4, -0.4, -0.4),
                height=0.04,
            )
        )
    return images, masks, labels, items


def draw_reveal(win, visual, images, masks, labels, reveal_count: int, show_arrows: bool) -> None:  # noqa: ANN001
    for image in images:
        image.draw()
    for index in range(reveal_count, len(images)):
        masks[index].draw()
        labels[index].draw()
    if show_arrows and len(images) > 1:
        xs = [image.pos[0] for image in images]
        for left, right in zip(xs, xs[1:]):
            arrow = visual.TextStim(
                win,
                text=">",
                pos=((left + right) / 2, 0),
                color="white",
                height=0.04,
            )
            arrow.draw()


def wait_for_space(win, event, draw_func) -> float:  # noqa: ANN001
    from psychopy import core

    clock = core.Clock()
    event.clearEvents()
    while True:
        draw_func()
        win.flip()
        keys = event.getKeys(keyList=["space", "escape"])
        if "escape" in keys:
            raise KeyboardInterrupt
        if "space" in keys:
            return clock.getTime()


def open_event_log(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("w", encoding="utf-8", newline="")
    writer = csv.DictWriter(handle, fieldnames=EVENT_FIELDS)
    writer.writeheader()
    return handle, writer


def run_trial(
    win,
    visual,
    event,
    row: dict[str, str],
    trial_index: int,
    exp_info: dict[str, str],
    recorder: AudioRecorder,
    event_writer,
    practice: bool = False,
) -> None:
    images, masks, labels, items = make_trial_stims(win, visual, row)
    show_arrows = practice
    for segment_index, (role, image_path) in enumerate(items, start=1):
        reveal_count = segment_index
        stem = (
            f"{exp_info['participant']}_s{exp_info['session']}_"
            f"{row['trial_id']}_seg{segment_index}_{role}"
        )
        onset = time.time()
        if not practice:
            recorder.start(stem)
        response_time = wait_for_space(
            win,
            event,
            lambda: draw_reveal(win, visual, images, masks, labels, reveal_count, show_arrows),
        )
        audio_file = "" if practice else recorder.stop()
        event_writer.writerow(
            {
                "participant": exp_info["participant"],
                "session": exp_info["session"],
                "list": exp_info["list"],
                "practice": "1" if practice else "0",
                "trial_index": str(trial_index),
                "trial_id": row["trial_id"],
                "dataset_number": row["dataset_number"],
                "dataset_slug": row["dataset_slug"],
                "set_id": row["set_id"],
                "condition_id": row["condition_id"],
                "condition_name": row["condition_name"],
                "cohesion": row["cohesion"],
                "transitivity": row["transitivity"],
                "segment_index": str(segment_index),
                "segment_role": role,
                "image_path": str(image_path),
                "image_onset_unix": f"{onset:.6f}",
                "response_time_sec": f"{response_time:.6f}",
                "audio_file": audio_file,
            }
        )
    fixation = visual.TextStim(win, text="+", color="white", height=0.06, pos=(0, 0))
    fixation.draw()
    win.flip()
    from psychopy import core

    core.wait(0.5)


def main() -> None:
    from psychopy import core, event, gui, visual

    exp_info = get_exp_info(gui)
    condition_path = condition_file_for(exp_info)
    if not condition_path.exists():
        raise FileNotFoundError(f"Condition table not found: {condition_path}")

    rows = load_rows(condition_path)
    seed = exp_info.get("random_seed", "").strip()
    rng = random.Random(seed if seed else None)
    rng.shuffle(rows)

    date = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_id = f"{safe_name(exp_info['participant'])}_{EXP_NAME}_{date}"
    event_log_path = DATA_DIR / f"{run_id}_events.csv"
    meta_path = DATA_DIR / f"{run_id}_info.json"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps({"exp_info": exp_info, "condition_file": str(condition_path)}, indent=2) + "\n")

    win = visual.Window(
        fullscr=as_bool(exp_info.get("fullscreen", "yes")),
        color="black",
        units="height",
        allowGUI=False,
    )
    recorder = AudioRecorder(RECORDINGS_DIR / run_id, enabled=as_bool(exp_info.get("record_audio", "yes")))
    event_handle, event_writer = open_event_log(event_log_path)

    try:
        draw_text_screen(
            win,
            visual,
            event,
            "Press SPACE to reveal each picture. Describe each revealed picture aloud, then press SPACE again. Press ESCAPE to quit.",
        )
        if as_bool(exp_info.get("practice", "no")):
            practice_rows = load_rows(CONDITIONS_DIR / "practice.csv")
            draw_text_screen(win, visual, event, "Practice trials. Press SPACE to begin.")
            for index, row in enumerate(practice_rows, start=1):
                run_trial(win, visual, event, row, index, exp_info, recorder, event_writer, practice=True)
            draw_text_screen(win, visual, event, "Practice is finished. Press SPACE to start the experiment.")

        first_half, second_half = split_half(rows)
        trial_index = 0
        for row in first_half:
            trial_index += 1
            run_trial(win, visual, event, row, trial_index, exp_info, recorder, event_writer)
        draw_text_screen(win, visual, event, "Break. Press SPACE when you are ready to continue.")
        for row in second_half:
            trial_index += 1
            run_trial(win, visual, event, row, trial_index, exp_info, recorder, event_writer)
        draw_text_screen(win, visual, event, "Thank you. Press SPACE to finish.")
    except KeyboardInterrupt:
        recorder.abort()
    finally:
        event_handle.close()
        win.close()
        core.quit()


if __name__ == "__main__":
    main()
