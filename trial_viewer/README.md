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
