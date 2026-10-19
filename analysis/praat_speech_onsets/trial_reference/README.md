# Local Trial Reference

This companion to Praat displays the participant stimulus picture, the relevant
part of the full PsychoPy recording and original EEG markers together. It reads source files only.
It never shifts triggers, aligns audio or edits manual annotations.

## Shared Recording Library

The normal entry point is `../START_WORKFLOW.cmd`. Use the recording selector
to switch sessions, or the folder-plus button to add a recording. Supply its
original BrainVision header, complete PsychoPy audio folder, matching isolated
experiment folder and microphone channel. AUX extraction, a three-tier Praat
grid, validation and registration are automatic. `../ADD_RECORDING.cmd` offers
file/folder dialogs instead. See [the full workflow](../WORKFLOW.md).

New recordings appear in the same page without another server or port. Imports
are published only after validation; a shared lock prevents concurrent imports.
Reimporting identical source files reuses their existing annotations and flags.
Requests carry the recording's full content identity so sessions cannot share
trial decisions accidentally.

New imports place `<recording>.wav` and `<recording>_annotations.TextGrid`
directly in its Desktop recording folder (for example
`Desktop/EEG recs/081i`), and watch that TextGrid, even if the original header
was selected from elsewhere. Existing files are never
overwritten. Extraction metadata and baseline backups stay in the library.

Every main/practice trial has independent `Unsuitable` and `Need help` toggles.
`Ergative` is available only for S 1 transitive main trials. These decisions are
manual, saved automatically, and never inferred from the transcription. The
matching filters show flagged trials. Need help is a review flag, not an
automatic behavioural exclusion.

The top **Itr**, **Tr ERG**, and **Tr ∅** counters cover all imported main
trials with both nonblank saved transcription and one valid speech onset,
excluding Unsuitable. Missing or ambiguous onsets and absent transcriptions do
not count. Need help trials remain included once both annotations are present.
Eligible transitive trials without an Ergative mark count under Tr ∅; this does
not change the CSV's separate saved-decision fields. Totals refresh after detected
TextGrid saves, flag saves, imports, and every five seconds across recordings and
browser tabs. An unreadable or invalid TextGrid shows unavailable totals instead
of silently skipping that recording.

The header exports the selected recording's flags, selected recording's trial
analysis, or the whole library's trial analysis. All three flags are included.
A blank ergative value means no decision was saved; it is not a confirmed
non-ergative response. The combined export rejects an invalid recording rather
than silently omitting it. Expand `Praat files` for the exact WAV and watched
annotation filenames.

## Start

### Keep Available on Windows

Run `install_autostart.ps1` in PowerShell to install the per-user Windows task
`Praat Trial Reference`. It starts a hidden supervisor immediately and at sign-in,
keeps this library at `http://127.0.0.1:8765`, and retries a crashed server every
five seconds. Windows also restarts a failed supervisor. No browser is launched,
no password is stored, and no firewall or sleep settings are changed. The task
runs only while this Windows user is signed in; the computer must be awake.

The supervisor does not terminate an existing server or another application that
uses the port. It does not change recordings, TextGrids or trial decisions.
Diagnostics are in `service_runner.log` and `service_server.log`. To remove the
startup task, run `install_autostart.ps1 -Remove`; an already running server may
remain available until stopped. Keep this folder and its configured Python runtime
in place while automatic startup is enabled.

Run `../START_WORKFLOW.cmd` to start or reopen the shared viewer. The default is
`http://127.0.0.1:8765`; if occupied, the server tries the next available port.
`server_status.json` also contains the actual URL and server process ID.
The original 072i session is configured in `session_config.json`; imported
recordings have separate configs under `recordings`.

Keep this page beside Praat. Search by `S 73`, `Mk7`, `trial 17`, a WAV filename,
scene name or a time such as `454.3 s`. A time lookup selects a main trial only
if the time lies between its recorded onset and end. When no trial matches,
the page keeps the old selection and displays an explicit warning.

Select a row to see the full image and original trial filename. The audio player
streams `full_session.wav` directly, starting 3 seconds before the trial's
logged `onset_sample` and ending 3 seconds after its `stop_sample`. Both are
sample indices in the PsychoPy full recording, not EEG timestamps. The seek
slider, current-time readout and window bounds show absolute PsychoPy seconds.
Play, pause, replay, seeking, speed, volume and looping apply to this window.
The window is clamped to the file bounds if there is less than 3 seconds available.
No new cropped WAVs are generated. At the end of the window playback stops, or
restarts at the window start if Loop is checked.
Switching trials stops the old recording and does not autoplay the new one.
PsychoPy audio is a listening reference, not the source of EEG onset timestamps.

Every main-trial short WAV must be readable and match its logged samples in the
full recording. A practice-only short WAV with a damaged header may use its
logged window in the intact full recording instead, with an explicit warning.
The remaining readable clips still undergo exact sample matching; at least one
must validate successfully. The damaged file and its hash are retained in the
manifest/provenance, and the original is never repaired or overwritten.
An unreadable or truncated full recording stops import before AUX extraction.

## Saved Praat Annotations

The current config watches:

```text
C:/Users/Sofya/Desktop/EEG recs/072i/praat_export/072i_AUX1/072i_transcription.TextGrid
```

In Praat, use `File > Save TextGrid as text file` and save to this exact filename.
The web page checks the saved file every 2 seconds and when it regains focus.
Unsaved editor changes cannot be read. The refresh icon beside `Praat annotations`
also checks immediately. Saving under a different name requires changing the
config's `textgrid` path and restarting that session's server.

Use the three tiers `triggers` (points), `speech_onset` (points), and
`transcription` (intervals). Each point in `speech_onset` is treated as an onset,
including an unlabelled point; `s` is a convenient label. Transcribe each sentence
in its own interval starting within its trial's S 200 / S 202 bounds. The end
may extend beyond S 202 and the next trial's S 200 without a warning; the start
determines the trial, and the original end time is retained. A trial can contain
more than one transcription interval; their text is displayed in time order.
Transcription boundaries do not create onset measurements.

For each main trial, the interface computes:

```text
speech_latency_s = manually_marked_speech_onset_eeg_s - S200_textgrid_eeg_s
speech_latency_ms = speech_latency_s * 1000
```

Both times come from the saved TextGrid on the unchanged EEG/StimTrak timeline.
All saved stimulus codes/times must first match the original EEG markers, within
half an EEG sample for numeric rounding. Long legacy `MkN: Stimulus/S...` labels
and compact `S ...` labels both work. A cropped, shifted or mismatching grid is
rejected and cannot be exported as valid measurements.

An onset is assigned only when S 200 <= onset < S 202 for one main trial.
Missing onset points produce an empty latency, not zero. Multiple points produce
an explicit warning and no selected latency: inspect/correct the tier in Praat.
Points outside trial bounds and transcription intervals starting outside trial
bounds remain unassigned and are listed in the page. Nothing is silently attached to the
nearest preceding trigger. Practice cannot be matched on this EEG timebase
because it has no trial triggers, so its onset/transcription fields stay empty.

The table-shaped export icon downloads `<recording>_trial_analysis.csv` with
transcriptions, absolute onsets, latencies in seconds and milliseconds, annotation
status, all point/interval candidates, original trial identifiers, and suitability
flags. It reads the latest saved TextGrid again when exporting. The flags export
icon downloads the suitability/ergative/need-help CSV. No CSV automatically drops
flagged trials: apply `unsuitable=1` as an exclusion in analysis and check missing,
multiple and unassigned annotations before treating a trial as complete.

Each successfully read content version is archived under
`annotation_snapshots/<first_20_session_id_characters>/<sha256>.TextGrid` with a
matching `<sha256>_mapping_v2.json` mapping. Older version-1 JSON maps are retained.
Exports include the source filename, SHA-256, saved time and mapping version so
the exact annotation source can be recovered after later Praat edits. These
copies do not alter the original file. The pinned [PraatIO reader](https://timmahrt.github.io/praatIO/praatio/utilities/textgrid_io.html)
is installed locally in `vendor`; UTF-8/UTF-16 long and short text formats are
supported. No network access is needed while using the interface.

## Behavioural Suitability

Each main/practice trial has an `Unsuitable` toggle. Click once to flag a trial,
and again to remove the flag. The pressed state is red and the trial list shows
a matching icon. `Saved` appears only after the database transaction succeeds;
a failed save leaves the previous flag unchanged. Use `Unsuitable only` to
filter the list. Session/rest events do not have trial-suitability decisions.

Decisions are saved automatically in `suitability.sqlite3` in this folder.
They survive browser refreshes, server restarts and switching session configs.
They are keyed by the source recording's content identity plus trial ID, not
just participant number. Moving the source files does not mix or reset flags.
The EEG, audio and Praat TextGrid files are never changed by a suitability flag.

The export icon at the top downloads `<recording>_suitability.csv`, including
trial number, phase, condition, item code, WAV name and original EEG times.
Use `unsuitable=1` as the behavioural exclusion flag in analysis. An unflagged
trial is not automatically confirmed suitable: `decision_saved=0` means no
decision has been recorded, while `decision_saved=1` means the toggle was saved.
Practice rows are included and are distinguishable by `phase`.

The database is the authoritative record of decisions; CSVs are snapshots.

## Mapping and Reproducibility

1. Read the original BrainVision header and markers using the original converter.
2. Match the entire ordered sequence of recorded EEG stimulus codes against
   log entries whose `serial_sent` is `1`. Both counts and every code must agree;
   the build fails on missing or mismatched triggers. This is a sequence check,
   not proof that the acquisition computer displayed an image correctly.
3. Group the PsychoPy labels by trial number (picture onset, condition, item, end).
4. Use the logged item trigger and experiment list to select an explicit row
   from `isolated_main_listN_all_120.csv`, including the stimulus-set number.
   Validate the condition and image-set against the WAV filename.
5. Resolve the participant picture through that row's `target_image`. Pictures
   are reconstructed from the local experiment's condition table, not recovered
   screenshots from the recording computer. The picture-source disclosure gives
   the exact source path. Keep the original experiment tables with the data.
6. Retain the EEG marker time `(sample_1based - 1) / EEG_sample_rate` unchanged.
7. Locate the WAV stem in `recording_segments.csv`. Validate that the original
   short clip's PCM samples equal the corresponding full-file sample slice,
   byte-for-byte, for every trial. The logged onset/stop sample indices define
   the listening window, with 3 seconds added on each side. The full file itself
   is not cropped or modified. This does not transfer EEG markers to PsychoPy.
8. Save `session_manifest.json` with all links and SHA-256 hashes of the header,
   marker file, trigger log, condition tables, segment log and full recording.
   No EEG-to-audio clock mapping is used.

For 072i this validates 120 main trials, 484 sent stimulus triggers, 10 practice
WAVs and 4 unsent log entries. Unsent entries are excluded from recorded triggers.
Practice pictures use the sequential practice table from the local experiment.
There are no practice trial EEG triggers, so the interface assigns no EEG times
to those pictures or audio clips. Their listening windows still use the logged
PsychoPy full-file sample indices; these are not EEG times.

Use the folder-plus import button for another participant. Separate configs
and exports are created automatically. For advanced single-config diagnostics:

```powershell
python server.py --config participant_config.json --check
python server.py --config participant_config.json
```

The reader currently supports this isolated-task WAV naming scheme and
four-trigger main trials. It deliberately rejects different layouts instead of
guessing how to map them. This is not yet a discourse-task viewer.

See `ADD_RECORDING.md` and `../WORKFLOW.md` for the intake workflow.
`start_reference.cmd` accepts `--config`, `--check` and `--port` for diagnostics;
normal use keeps all recordings in one shared viewer. Each has its own source
identity and decisions. A per-recording manifest is retained in
`session_manifests`, in addition to the latest `session_manifest.json`.

All media are served from an explicit allowlist on loopback only. There are no
third-party services, uploads or internet dependencies. The player supports HTTP
byte ranges for WAV seeking. Do not expose this server on a public network.
Suitability writes require same-origin JSON requests and the matching session ID.

## Short TextGrid Labels

`../simplify_trigger_labels.praat` reads a saved grid using Praat, creates a new
copy and shortens the trigger text to `S 200`, `S 73`, etc. It then reads the copy
back and checks every point time, interval time and manual annotation against
the source. The non-stimulus startup point is retained at its original time with
a blank label. Original full marker metadata remains in the BrainVision `.vmrk`
and exported marker TSV. Never replace a grid containing unsaved Praat edits.
