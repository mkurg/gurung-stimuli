#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from datetime import datetime
from pathlib import Path


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
    {
        "condition_id": "tr_coh",
        "condition_name": "transitive_cohesive",
        "cohesion": "cohesive",
        "transitivity": "transitive",
        "steps": ["coh_1", "coh_2", "tr_target"],
    },
    {
        "condition_id": "it_coh",
        "condition_name": "intransitive_cohesive",
        "cohesion": "cohesive",
        "transitivity": "intransitive",
        "steps": ["coh_1", "coh_2", "it_target", "end_coh_it"],
    },
    {
        "condition_id": "tr_ic",
        "condition_name": "transitive_incohesive",
        "cohesion": "incohesive",
        "transitivity": "transitive",
        "steps": ["ic_1", "tr_target", "end_ic_tr"],
    },
    {
        "condition_id": "it_ic",
        "condition_name": "intransitive_incohesive",
        "cohesion": "incohesive",
        "transitivity": "intransitive",
        "steps": ["ic_1", "it_target", "end_ic_it"],
    },
]

CSV_FIELDS = [
    "trial_id",
    "dataset_number",
    "dataset_slug",
    "dataset_label",
    "set_id",
    "set_label",
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
    "source_dataset_folder",
    "source_set_folder",
]

SCRIPT_NAME = "gurung_experiment.py"


def natural_key(value: str) -> list[object]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", value)]


def slugify(value: str) -> str:
    value = value.strip().replace(" ", "_")
    chars = [char.lower() if char.isalnum() or char in {"_", "-", "."} else "_" for char in value]
    slug = "".join(chars)
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("._") or "item"


def parse_dataset_folder(path: Path) -> tuple[int, str] | None:
    match = re.match(r"^(\d+)_(.+)$", path.name)
    if not match:
        return None
    return int(match.group(1)), match.group(2)


def default_source_root() -> Path:
    cloud = Path.home() / "Library" / "CloudStorage" / "GoogleDrive-apazent@gmail.com"
    return (
        cloud
        / ".shortcut-targets-by-id"
        / "1exBA-7XrpLfZc6s8oGNYTbmjGsu5dT6p"
        / "Gurung stimuli"
    )


def scan_source(root: Path) -> list[dict[str, object]]:
    datasets: list[dict[str, object]] = []
    missing: list[str] = []
    extras: list[str] = []

    for folder in sorted(root.iterdir(), key=lambda p: natural_key(p.name)):
        if not folder.is_dir():
            continue
        parsed = parse_dataset_folder(folder)
        if parsed is None:
            continue
        number, label = parsed
        dataset_slug = f"{number:03d}_{slugify(label)}"
        set_folders: dict[int, Path] = {}
        for set_id in (1, 2):
            set_folder = folder / str(set_id)
            if not set_folder.is_dir():
                missing.append(str(set_folder))
                continue
            set_folders[set_id] = set_folder
            found = {child.stem for child in set_folder.glob("*.png") if child.is_file()}
            for stem in EXPECTED_IMAGES:
                if stem not in found:
                    missing.append(str(set_folder / f"{stem}.png"))
            for stem in sorted(found - set(EXPECTED_IMAGES), key=natural_key):
                extras.append(str(set_folder / f"{stem}.png"))
        datasets.append(
            {
                "number": number,
                "label": label,
                "slug": dataset_slug,
                "folder": folder,
                "sets": set_folders,
            }
        )

    if missing:
        raise FileNotFoundError("Missing expected stimuli:\n" + "\n".join(missing[:80]))
    if extras:
        raise ValueError("Unexpected extra PNG files:\n" + "\n".join(extras[:80]))
    if len(datasets) != 30:
        raise ValueError(f"Expected 30 dataset folders, found {len(datasets)} in {root}")
    return datasets


def rel_stimulus_path(dataset_slug: str, set_id: int, stem: str) -> str:
    return f"Stimuli/set{set_id}/{dataset_slug}/{stem}.png"


def image_path_for(
    dataset: dict[str, object],
    set_id: int,
    stem: str,
    copy_images: bool,
) -> str:
    if copy_images:
        return rel_stimulus_path(str(dataset["slug"]), set_id, stem)
    source = Path(dataset["sets"][set_id]) / f"{stem}.png"  # type: ignore[index]
    return str(source)


def build_all_rows(datasets: list[dict[str, object]], copy_images: bool) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for dataset in datasets:
        number = int(dataset["number"])
        for set_id in (1, 2):
            for path in TRIAL_PATHS:
                row = {
                    "trial_id": f"d{number:03d}_s{set_id}_{path['condition_id']}",
                    "dataset_number": str(number),
                    "dataset_slug": str(dataset["slug"]),
                    "dataset_label": str(dataset["label"]).replace(" ", "_"),
                    "set_id": str(set_id),
                    "set_label": f"set{set_id}",
                    "condition_id": str(path["condition_id"]),
                    "condition_name": str(path["condition_name"]),
                    "cohesion": str(path["cohesion"]),
                    "transitivity": str(path["transitivity"]),
                    "n_images": str(len(path["steps"])),
                    "source_dataset_folder": str(dataset["folder"]),
                    "source_set_folder": str(dataset["sets"][set_id]),  # type: ignore[index]
                }
                for index in range(1, 5):
                    row[f"img{index}"] = ""
                    row[f"img{index}_role"] = ""
                for index, stem in enumerate(path["steps"], start=1):
                    row[f"img{index}"] = image_path_for(dataset, set_id, stem, copy_images)
                    row[f"img{index}_role"] = stem
                rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_balanced_lists(conds_dir: Path, rows: list[dict[str, str]]) -> None:
    by_key = {
        (int(row["dataset_number"]), int(row["set_id"]), row["condition_id"]): row
        for row in rows
    }
    condition_ids = [path["condition_id"] for path in TRIAL_PATHS]
    dataset_numbers = sorted({int(row["dataset_number"]) for row in rows})

    for list_index in range(8):
        list_rows: list[dict[str, str]] = []
        for dataset_pos, dataset_number in enumerate(dataset_numbers):
            condition_id = condition_ids[(dataset_pos + list_index) % len(condition_ids)]
            set_id = 1 + ((dataset_pos + (list_index // len(condition_ids))) % 2)
            list_rows.append(by_key[(dataset_number, set_id, condition_id)])
        write_csv(conds_dir / f"trials_list{list_index + 1}.csv", list_rows)


def write_condition_tables(out_dir: Path, rows: list[dict[str, str]]) -> None:
    conds_dir = out_dir / "Conds"
    write_csv(conds_dir / "trials_all_240.csv", rows)
    write_csv(conds_dir / "trials_set1_all_conditions.csv", [row for row in rows if row["set_id"] == "1"])
    write_csv(conds_dir / "trials_set2_all_conditions.csv", [row for row in rows if row["set_id"] == "2"])
    write_balanced_lists(conds_dir, rows)

    practice_rows = []
    for index, path in enumerate(TRIAL_PATHS):
        dataset_number = index + 1
        match = next(
            row
            for row in rows
            if int(row["dataset_number"]) == dataset_number
            and row["set_id"] == "1"
            and row["condition_id"] == path["condition_id"]
        )
        practice_rows.append(match)
    write_csv(conds_dir / "practice.csv", practice_rows)


def copy_stimuli(out_dir: Path, datasets: list[dict[str, object]]) -> list[dict[str, str]]:
    manifest: list[dict[str, str]] = []
    for dataset in datasets:
        for set_id in (1, 2):
            for stem in EXPECTED_IMAGES:
                source = Path(dataset["sets"][set_id]) / f"{stem}.png"  # type: ignore[index]
                dest = out_dir / rel_stimulus_path(str(dataset["slug"]), set_id, stem)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)
                stat = dest.stat()
                manifest.append(
                    {
                        "dataset_number": str(dataset["number"]),
                        "dataset_slug": str(dataset["slug"]),
                        "set_id": str(set_id),
                        "stem": stem,
                        "source": str(source),
                        "destination": str(dest),
                        "bytes": str(stat.st_size),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                    }
                )
    return manifest


def write_manifest(out_dir: Path, payload: dict[str, object], copy_manifest: list[dict[str, str]]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "package_manifest.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    if copy_manifest:
        manifest_path = out_dir / "stimuli_copy_manifest.csv"
        fields = ["dataset_number", "dataset_slug", "set_id", "stem", "source", "destination", "bytes", "modified"]
        with manifest_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(copy_manifest)


def write_readme(out_dir: Path, copy_images: bool, source_root: Path) -> None:
    stimulus_note = (
        "This package contains normalized PNG copies under `Stimuli/`."
        if copy_images
        else "This lightweight workspace package points the CSV image columns at the Google Drive source PNGs."
    )
    text = f"""# Gurung PsychoPy Package

Generated for the Gurung picture-sequence experiment.

{stimulus_note}

## Run

Open `gurung_experiment.py` in PsychoPy Coder, or run it with the PsychoPy Standalone Python:

```sh
/Applications/PsychoPy.app/Contents/MacOS/python gurung_experiment.py
```

The participant dialog defaults to the balanced counterbalancing table `Conds/trials_list1.csv`.

## Condition Tables

- `Conds/trials_list1.csv` ... `Conds/trials_list8.csv`: balanced 30-trial participant lists. Each list shows one condition per dataset and balances set 1/set 2.
- `Conds/trials_all_240.csv`: all datasets x both sets x all four path types, for audit or piloting.
- `Conds/trials_set1_all_conditions.csv` and `Conds/trials_set2_all_conditions.csv`: all four path types for one stimulus set.
- `Conds/practice.csv`: four real-stimulus practice examples. The experiment dialog defaults practice to `no` until separate practice-only stimuli are approved.

## Source

Source root used at generation time:

```text
{source_root}
```

The four path types follow the current viewer/docs:

- `transitive_cohesive`: `coh_1 -> coh_2 -> tr_target`
- `intransitive_cohesive`: `coh_1 -> coh_2 -> it_target -> end_coh_it`
- `transitive_incohesive`: `ic_1 -> tr_target -> end_ic_tr`
- `intransitive_incohesive`: `ic_1 -> it_target -> end_ic_it`
"""
    (out_dir / "README.md").write_text(text, encoding="utf-8")


EXPERIMENT_SCRIPT = r'''#!/usr/bin/env python3
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
'''


def write_experiment_script(out_dir: Path) -> None:
    path = out_dir / SCRIPT_NAME
    path.write_text(EXPERIMENT_SCRIPT, encoding="utf-8")
    path.chmod(0o755)


def build_package(args: argparse.Namespace) -> dict[str, object]:
    source_root = Path(args.source_root).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()
    if not source_root.is_dir():
        raise FileNotFoundError(f"Source root not found: {source_root}")

    datasets = scan_source(source_root)
    out_dir.mkdir(parents=True, exist_ok=True)
    copy_manifest: list[dict[str, str]] = []
    if args.copy_images:
        copy_manifest = copy_stimuli(out_dir, datasets)

    rows = build_all_rows(datasets, copy_images=args.copy_images)
    write_condition_tables(out_dir, rows)
    write_experiment_script(out_dir)
    write_readme(out_dir, copy_images=args.copy_images, source_root=source_root)

    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_root": str(source_root),
        "out_dir": str(out_dir),
        "copy_images": bool(args.copy_images),
        "dataset_count": len(datasets),
        "expected_images": EXPECTED_IMAGES,
        "trial_paths": TRIAL_PATHS,
        "tables": {
            "balanced_lists": 8,
            "balanced_list_trials": 30,
            "all_trials": len(rows),
            "set_trials": 120,
            "practice_trials": 4,
        },
    }
    write_manifest(out_dir, manifest, copy_manifest)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", default=str(default_source_root()))
    parser.add_argument("--out", default="psychopy_gurung")
    parser.add_argument(
        "--copy-images",
        action="store_true",
        help="Copy PNGs into a normalized Stimuli tree and write relative image paths.",
    )
    return parser.parse_args()


def main() -> None:
    manifest = build_package(parse_args())
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
