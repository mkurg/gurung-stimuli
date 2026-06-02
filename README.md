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

## Publish on GitHub

Commit the repository, push it to GitHub, then enable Pages from:

```text
Settings -> Pages -> Deploy from a branch -> main / docs
```
