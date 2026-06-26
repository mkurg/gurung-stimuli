# Gurung Experimental Trial Viewer

This repository contains two versions of the same trial-review interface:

- `trial_viewer/`: local working viewer that scans the Google Drive-backed stimuli folder live.
- `docs/`: static GitHub Pages export with lightweight WebP image copies.

## Local working viewer

```sh
./start.sh --port 8766
```

Open:

```text
http://127.0.0.1:8766/
```

This mode reads directly from the local Google Drive cache and updates when files appear in the dataset folders.

## GitHub Pages export

```sh
python3 trial_viewer/export_static.py
```

The export writes:

- `docs/index.html`
- `docs/app.js`
- `docs/styles.css`
- `docs/data/datasets.json`
- `docs/assets/**/*.webp`

Re-run the export whenever new pictures are added or changed. Existing WebP files are skipped when they are already current.

Missing-picture ideas are saved locally in:

```text
trial_viewer/missing_picture_ideas.json
```

Use the local viewer to edit those notes. The next static export bakes them into `docs/data/datasets.json`, so they appear on GitHub Pages after commit and push.

## PsychoPy Experiments

The current runnable PsychoPy experiments are included in the repo:

- `psychopy_gurung_v1/`: Discourse experiment, 120 picture-sequence trials.
- `psychopy_gurung_isolated/`: Isolated experiment, 120 single-target-picture trials plus resting-state screens.

Open these files in PsychoPy Builder:

```text
psychopy_gurung_v1/gurung_120_v1.psyexp
psychopy_gurung_isolated/gurung_isolated_v1.psyexp
```

Both packages include the local audio, condition tables, packaged image stimuli, and current generated `*_lastrun.py` scripts needed to run from a cloned copy. Participant outputs are intentionally ignored by Git:

```text
psychopy_gurung_v1/data/
psychopy_gurung_v1/recordings/
psychopy_gurung_isolated/data/
psychopy_gurung_isolated/recordings/
```

The current experiments were built with PsychoPy `2026.1.3`; see `psychopy_requirements.txt` for Python package dependencies.

To rebuild the isolated package inside the repo:

```sh
python tools/build_gurung_isolated.py
```

The older workspace package is generated in:

```text
psychopy_gurung/
```

To rebuild the older package:

```sh
python3 tools/build_psychopy_package.py --out psychopy_gurung
```

A normalized image-copy package for running from Google Drive was also generated under the Gurung stimuli folder:

```text
Gurung stimuli/PsychoPy package 2026-06-06/
```

It contains `Stimuli/set1/...`, `Stimuli/set2/...`, the same condition tables, and `gurung_experiment.py` with relative image paths.

## Publish on GitHub

Commit the repository, push it to GitHub, then enable Pages from:

```text
Settings -> Pages -> Deploy from a branch -> main / docs
```
