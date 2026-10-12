# Speech Annotation: Repeatable Workflow

## Fast Steps For Every New Recording

1. Download the original EEG `.vhdr`, linked `.eeg`, and `.vmrk`, plus the complete
   original PsychoPy session folder. Keep original filenames and do not edit raw
   recordings. The PsychoPy folder must contain `full_session.wav`,
   `eeg_triggers.csv`, `recording_segments.csv`, and all original trial WAVs;
   retain `recording_events.csv` and the other experiment output files too.
2. Double-click `START_WORKFLOW.cmd` to open the same recording library. Click the
   folder-plus icon beside **Recording**. Paste the `.vhdr` path and PsychoPy
   session-folder path, confirm the matching experiment folder and microphone
   channel (`AUX1` for the current setup), and click **Import recording**.
   Alternatively, double-click `ADD_RECORDING.cmd` for Windows file/folder dialogs.
3. Wait for **Recording ready**. AUX extraction, compact trigger labels, the
   three Praat tiers, mapping checks and library registration are automatic.
   Select the new entry from **Recording**; no second server or port is needed.
4. In Praat, open the StimTrak WAV and the saved annotation TextGrid listed under
   **Praat files** in that recording. New imports always place these directly
   in the corresponding Desktop folder, for example `Desktop/EEG recs/081i/081i.wav` and
   `Desktop/EEG recs/081i/081i_annotations.TextGrid`. Select both objects with Ctrl, then
   **View & Edit**. Place onset points labelled `s` in `speech_onset`; add sentence
   intervals and text in `transcription`. Do not move points in `triggers`.
5. Use **File > Save TextGrid as text file** to the exact annotation filename
   shown in the page. Saved transcriptions/onsets update in the web page within
   about 2 seconds while it is active, or when returning to it. Listen to the
   PsychoPy full-recording window when words are unclear: it includes 3 seconds
   before trial onset and 3 seconds after trial finish, where file bounds allow.
6. Mark **Unsuitable** for behavioural exclusion, **Need help** for unclear
   transcription, and **Ergative** for an ergative response on an `S 1` transitive
   trial. Click a toggle again to remove it. These are independent manual tags,
   not automatic judgments. Use the corresponding filters to revisit them.
   The top counters total all imported main trials with both nonblank saved
   transcription and one valid speech onset, not marked Unsuitable:
   **Itr**, **Tr ERG** (Ergative marked), and **Tr ∅** (Ergative not marked).
   Need help trials are included once annotated; practice and events are not.
   Missing transcription or missing/ambiguous onset means the trial does not count.
7. Export with the table icon for the selected recording, or the files icon for
   **all recordings together**. The file-down icon exports trial flags only.
   Re-export after more saves/review decisions; CSVs are snapshots.

## What Is Kept Unchanged

**StimTrak / EEG is the timing source of truth.** MNE extracts the full microphone
channel at its original sample rate, with one constant playback gain. There is
no cropping, filtering, resampling, waveform alignment or trigger transfer to
PsychoPy. Trigger seconds are `(sample_position_1based - 1) / EEG_sample_rate`.

The page computes `speech_latency_ms = 1000 * (marked_onset - S200)` using the
saved TextGrid on that same timeline. A unique onset must lie within its main
trial's `S 200 <= time < S 202` bounds. Missing or multiple points do not create
a guessed latency. A transcription is assigned by its start within a trial's
S 200 / S 202 bounds; its end may extend beyond S 202 and the next S 200 without
a warning or reassignment. Transcription starts and onset points outside trial
bounds are listed as unassigned for review. Practice has no EEG trial triggers,
so its latency/transcription cannot be assigned by this EEG mapping.

Use the same study-defined acoustic onset criterion across recordings. Locate
the earliest reliable evidence of the intended response, including unvoiced
initial sounds; a pitch trace alone is not an onset detector. PsychoPy helps
identify the words, but its timestamps must not be copied into Praat. A numeric
latency is an annotation measurement, not a guarantee of acoustic certainty.

## Automatic Checks And Repeat Imports

Import compares the complete sent PsychoPy trigger sequence with the original
EEG sequence; every count/code must agree. It checks trial groups, condition/item
codes, WAV identities, matching condition tables/pictures, EEG/WAV sample counts,
and each original short clip's byte-for-byte location in the full recording.
The original short WAVs are still required for these checks, but are not played.

A failed import is not published in the selector. Existing recordings and
annotations are not overwritten. Importing the same source recording again
reuses its entry without extracting another WAV. Only one import runs at a time,
including when the browser and desktop launcher are used together.

All currently supported recordings use the **same isolated-task protocol** as
072i. Discourse or changed trigger/WAV naming conventions require another adapter;
the importer stops instead of guessing. Always select the actual experiment
version used for that recording, not a different version with similar images.

## Files And Backups

Each validated recording has a content identity and a folder below
`trial_reference/recordings/<first_20_identity_characters>/` containing:

- `config.json`: source, audio, experiment and watched annotation paths.
- `manifest.json`: trial/picture/audio/EEG mapping and input checksums.
- `provenance.json`: raw EEG and extraction checksums, tool hashes, versions and
  timing recipe.
- `registration.json`: published only after successful validation.
- `aux/...`: archived extraction WAV, initial empty baseline TextGrid, marker TSV
  and extraction metadata. The working WAV and editable
  `<recording>_annotations.TextGrid` are placed directly in
  `Desktop/EEG recs/<recording>/`, not kept only in this internal library folder.

The existing 072i entry references its current WAV and
`072i_transcription.TextGrid`; importing it into the library does not re-extract
audio or replace those manual annotations. Future recordings always use
`Desktop/EEG recs/<header_filename_without_extension>/` for working Praat files,
even if the original header was selected from another directory. Keep each
recording's `.vhdr` in its respective Desktop EEG folder when possible. Existing output filenames
cause an explicit conflict, never an overwrite. The page shows the precise
watched filename, and repeat imports keep it unchanged.

Flags for all recordings are stored separately by full session identity + trial
ID in `trial_reference/suitability.sqlite3`. Do not join recordings using only a
trial number or repeated code such as `S 200`.

Each successfully read annotation version is copied to
`trial_reference/annotation_snapshots/<identity_prefix>/<sha256>.TextGrid` with
its computed versioned JSON mapping (`<sha256>_mapping_v2.json`; older version-1
maps are kept). CSVs include that hash and mapping version, plus the
original trial identifiers, candidate points/intervals and all three flag types.

Back up the complete `praat_speech_onsets` workflow folder, including the database,
configs, `recordings`, annotation snapshots and exported CSVs, together with the
original EEG/PsychoPy folders and matching experiment assets. The new imports
reference original media locally; they do not upload it or make replacement raw
recordings. Close the viewer before copying the database, or include its `-wal`
and `-shm` files in a consistent backup.

## Analysis

The combined CSV retains every main/practice trial, including incomplete or
flagged trials. Apply behavioural exclusion with `unsuitable=1`. Use `need_help=1`
as a review queue, not an automatic exclusion. `ergative=1` means manually marked;
blank means no ergative decision was saved, not proven non-ergative.
The top **Tr ∅** counter groups eligible annotated transitive trials without an
Ergative mark together, including those with no saved flag decision; the CSV still
preserves that distinction. All three counters require both transcription and
one valid saved onset, and update when a new TextGrid save is detected.
`decision_saved` and the separate flag decision columns distinguish unreviewed
rows from saved decisions. Check annotation status/warnings and phase before
analysis; `ok` only means one structurally matchable onset.

All-recordings export fails explicitly if any recording or saved TextGrid cannot
be read/validated; no recordings are silently skipped. The files remain editable
in Praat, and corrections can be saved and exported again.

## Reopening And Command Line

`START_WORKFLOW.cmd` reopens the already-running local library, or starts it if
needed. It does not deliberately start a separate viewer per participant.
Keep imports running until completion; do not terminate the server during an
import. Browser refreshes can reconnect to an ongoing web import.

For repeatable command-line imports, from `trial_reference`, run with the viewer
Python listed in `pipeline_config.json`:

```powershell
python import_recording.py --vhdr "C:\data\073i\073i.vhdr" --audio-dir "C:\data\073i\psychopy-session" --experiment-dir "C:\experiment\isolated part" --channel AUX1
```

The current Windows launchers contain this computer's installed Python paths.
On another computer, update both launchers and `trial_reference/pipeline_config.json`
(`mne_python`, `viewer_python`, `praat`, `praat_output_root`, default experiment path) and the local
`lucide` path in `session_config.json`. The viewer's pinned PraatIO dependency is
included in `vendor`; the installed MNE runtime handles AUX extraction.
No packages need to be installed for each new recording.
