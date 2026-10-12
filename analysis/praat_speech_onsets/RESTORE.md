# Restore Annotation Work on Another Device

This public GitHub backup contains the current workflow and interface, saved
Praat annotations, all three manual trial decisions, original trigger/log
metadata, per-recording analysis CSVs, and historical SOL plots. It does not
contain raw EEG or participant audio. Transcriptions and trial decisions are
public, as requested.

The October 12, 2026 snapshot covers 072i, 073i, 081i, 082i, 091i, 092i, 101i,
111i, 112i and 121i. The first nine have 120 transcribed trials each; 121i is
still in progress. Only changes saved to disk in Praat can be backed up.

## 1. Get the Code and Saved Work

```powershell
git clone --branch codex/praat-workflow-backup-20261012 https://github.com/mkurg/gurung-stimuli.git
cd gurung-stimuli\analysis\praat_speech_onsets
```

This is a separate branch based on the experiment repository's `main` branch.
The matching stimulus pictures and condition tables come with the checkout.

## 2. Copy the Private Recordings

Transfer the entire `Desktop\EEG recs` folder using a private drive or approved
private storage. Keep each recording's directory structure unchanged, including:

- Original `.vhdr`, `.vmrk`, and `.eeg` files.
- Extracted StimTrak `<recording>.wav` files, including 072i's nested export.
- Complete PsychoPy audio folders: `full_session.wav`, short trial WAVs,
  `eeg_triggers.csv`, and `recording_segments.csv`.

The existing EEG/audio collection is approximately 19.5 GiB. These files are not
recoverable from this GitHub backup alone. Do not upload participant voices or
raw EEG to this public repository.

The directory can have a different username or drive on the new device. The
restore command remaps paths from the new `EEG recs` root. Do not edit the
original headers, logs, or WAVs: their identities protect the trial decisions.

## 3. Set Up Python and Restore

Use Python 3.14 to match the recorded runtime. In PowerShell:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-restore.txt
.\.venv\Scripts\python.exe backup_work.py verify
.\.venv\Scripts\python.exe backup_work.py restore --recordings-root "$env:USERPROFILE\Desktop\EEG recs" --dry-run
.\.venv\Scripts\python.exe backup_work.py restore --recordings-root "$env:USERPROFILE\Desktop\EEG recs" --praat "C:\path\to\Praat.exe"
```

An existing MNE-Python installation is also usable: run `backup_work.py` with its
`python.exe`, and omit virtual-environment creation. `--python` can specify a
different installed extraction/viewer interpreter when needed.

Restore verifies every saved file checksum, database integrity, original
recording identity, source-log/table hashes, StimTrak WAV hash, and annotation
trigger times before writing anything. It reconnects all ten sessions using the
same session IDs, preserving `Unsuitable`, `Ergative`, and `Need help` decisions.
It restores TextGrids to their original relative locations under the new
recording root, and creates local viewer/runtime configurations with new paths.

Different existing TextGrids, configurations, or databases are never
overwritten. Stop the viewer before restoring. On a device with newer work,
keep that work and use a fresh checkout rather than replacing its database.

## 4. Continue Working

Double-click `START_WORKFLOW.cmd`, or run:

```powershell
.\.venv\Scripts\python.exe run_workflow.py
```

Select the recording in the viewer. Open its unchanged StimTrak WAV and watched
TextGrid together in Praat. Save annotations to the exact filename shown under
`Praat files`; the viewer continues synchronizing saved transcription and SOL.
The original [workflow instructions](WORKFLOW.md) cover annotation and imports.

## Files in the Backup

- `saved_work/backup.json`: recording inventory, counts, and file checksums.
- `saved_work/recordings/<recording>/*_annotations.TextGrid`: exact saved bytes.
- `saved_work/recordings/<recording>/trial_analysis.csv`: all trials, not just
  suitable trials; apply the usual suitability/onset/transcription criteria.
- `saved_work/recordings/<recording>/trial_flags.csv`: saved decisions, including
  the distinction between an unreviewed and an explicitly unchecked ERG flag.
- `saved_work/trial_decisions.sqlite3`: consistent SQLite backup, including
  committed WAL changes. `trial_decisions.json` is its readable counterpart.
- `saved_work/recordings/<recording>/source_metadata`: unchanged header, marker,
  and PsychoPy CSV files; `source_metadata.json` records their original locations.
- `plots`: previous plots and their JSON snapshots. They describe the data at
  their creation time, not necessarily the current library.

No participant exclusion or SOL cutoff was applied while capturing this backup.
Resting-state marks and unassigned annotations remain intact in the TextGrids.

## Capture Future Work

Save Praat first. Capture into a new directory so an older backup cannot be
overwritten accidentally:

```powershell
.\.venv\Scripts\python.exe backup_work.py capture --recordings-root "$env:USERPROFILE\Desktop\EEG recs" --output saved_work_YYYYMMDD
```

When using the original local workflow rather than this checkout, add
`--source "C:\path\to\praat_speech_onsets"`. The backup tool validates that
workflow's registered sessions and reads its own decision database.

Commit a new snapshot only after reviewing its inventory. Preserve exact backup
bytes in Git: the included `.gitattributes` prevents newline conversion under
`saved_work` and `saved_work_*` directories.
