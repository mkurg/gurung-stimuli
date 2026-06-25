# Gurung Trial Viewer

A local web interface for reviewing numbered experimental-trial sets. The viewer currently expects
set folders `1`, `2`, `3`, and `4` inside each dataset folder.

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

The toolbar has set checkboxes so you can compare any combination, such as `1` + `3`,
`2` + `4`, or all four sets.

The exporter keeps the local viewer intact, writes `docs/data/datasets.json`, and creates
lightweight WebP copies under `docs/assets/<dataset>/<set>/`. Those WebPs are committed with the
GitHub Pages export, and `datasets.json` points at relative `assets/...` URLs by default.

When an image is drag-dropped into the local viewer, the local server saves the PNG to Google Drive,
runs the same static export, and leaves the changed `docs/data/` plus `docs/assets/` files ready to
commit for GitHub Pages. Keep `export_static.py` for manual repairs or full rebuilds; unchanged WebP
files are skipped.

Useful upload-time switches:

```sh
GURUNG_STATIC_EXPORT_ON_UPLOAD=0 ./start.sh
GURUNG_STATIC_PUBLISH_ON_UPLOAD=0 ./start.sh
GURUNG_STATIC_REMOTE="apazent@204.168.154.216:/home/apazent/gurung-trial-viewer/site" ./start.sh
GURUNG_ASSET_BASE_URL="https://gurung.duckdns.org" ./start.sh
```

Missing-picture ideas entered in the local viewer are saved in `trial_viewer/missing_picture_ideas.json` and included in the next static export.

Picture reviews are saved by the remote review server as plain text in a JSON file. See `trial_viewer/DEPLOY_HETZNER.md` for Hetzner deployment and backup commands.

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
