# Gurung Trial Viewer

A local web interface for reviewing the existing experimental trials and the draft trials in each dataset's `2` folder.

Run it from the workspace root:

```sh
./start.sh
```

Then open the printed local URL, normally:

```text
http://127.0.0.1:8765
```

The server scans the Google Drive local cache directly. If the stimuli folder moves, set the root explicitly:

```sh
GURUNG_STIMULI_ROOT="/path/to/Gurung stimuli" ./start.sh
```

Export a GitHub Pages-ready static site into `docs/`:

```sh
python3 trial_viewer/export_static.py
```

The exporter keeps the local viewer intact, writes `docs/data/datasets.json`, and creates lightweight WebP copies under `docs/assets/`. Re-run the export whenever new images appear in Google Drive; unchanged WebP files are skipped.

Missing-picture ideas entered in the local viewer are saved in `trial_viewer/missing_picture_ideas.json` and included in the next static export.

Expected image names:

```text
ic_1.png
coh_1.png
coh_2.png
tr_target.png
it_target.png
end_coh_it.png
end_ic_tr.png
end_ic_it.png
```
