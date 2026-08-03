# Ergativity EEG

This repository contains the current PsychoPy experiments plus the trial-review interface.

## Trial Viewer

The viewer has two versions:

- `trial_viewer/`: local working viewer that scans the Google Drive-backed stimuli folder live.
- `docs/`: static GitHub Pages export, including lightweight WebP image copies in `docs/assets/`.

## Local working viewer

```sh
./start.sh --port 8766
```

Open:

```text
http://127.0.0.1:8766/
```

This mode reads directly from the local Google Drive cache and updates when files appear in the dataset folders.
Each dataset folder is expected to contain numbered set folders: `1`, `2`, `3`, and `4`.
Use the set checkboxes in the toolbar to compare only the columns you need, such as `1` + `3`
or `2` + `4`.

## Static Export

```sh
python3 trial_viewer/export_static.py
```

The export writes:

- `docs/index.html`
- `docs/app.js`
- `docs/styles.css`
- `docs/data/datasets.json`
- `docs/assets/**/*.webp`

The exported image URLs are relative `assets/...` paths by default, so GitHub Pages serves the
images directly from this repository. When you drag-drop a picture in the local viewer, the server
saves the PNG to Google Drive and refreshes the static WebP export. Commit `docs/data/` and
`docs/assets/` to publish the updated pictures on GitHub Pages. Existing WebP files are skipped when
they are already current.

Missing-picture ideas are saved locally in:

```text
trial_viewer/missing_picture_ideas.json
```

Use the local viewer to edit those notes. The next static export bakes them into `docs/data/datasets.json`, so they appear on GitHub Pages after commit and push.

## PsychoPy Experiments

The current runnable PsychoPy experiments are included in the repo:

- `discourse part/`: Discourse experiment, two selectable 240-trial picture-sequence lists.
- `isolated part/`: Isolated experiment, two selectable 120-target-picture lists plus resting-state screens.

Open these files in PsychoPy Builder:

```text
discourse part/discourse_part.psyexp
isolated part/isolated_part.psyexp
```

The repo includes the local audio, condition tables, packaged JPEG main stimuli, and current generated `*_lastrun.py` scripts needed to run from a cloned copy. Participant outputs are intentionally ignored by Git:

```text
discourse part/data/
discourse part/recordings/
isolated part/data/
isolated part/recordings/
```

The current experiments were built with PsychoPy `2026.1.3`; see `psychopy_requirements.txt` for Python package dependencies.

### EEG Trigger Checks

Each real run writes a trigger log here:

```text
discourse part/recordings/<participant>_l<list>_<date-time>/eeg_triggers.csv
isolated part/recordings/<participant>_l<list>_<date-time>/eeg_triggers.csv
```

The log includes trigger code, label, whether it was sent on a screen flip, COM port, serial status, pulse width, and whether the serial write succeeded.

Before a session, validate the trigger coding in all condition files:

```sh
python tools/test_eeg_triggers.py --validate-only
```

To send a short known trigger sequence through the TriggerBox, replace `COM4` with the lab port:

```sh
python tools/test_eeg_triggers.py --smoke-only --port COM4 --pulse-ms 5
```

After a short real run, validate the run log. Add `--require-serial` when the TriggerBox was connected:

```sh
python tools/test_eeg_triggers.py --validate-only --log "discourse part/recordings/<participant>_l<list>_<date-time>/eeg_triggers.csv" --require-serial
```

To rebuild the isolated package inside the repo:

```sh
python tools/build_gurung_isolated.py
```

## Publish on GitHub

Commit the repository, push it to GitHub, then enable Pages from:

```text
Settings -> Pages -> Deploy from a branch -> main / docs
```
