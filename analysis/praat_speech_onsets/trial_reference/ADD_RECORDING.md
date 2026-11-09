# Add Another Recording

See [the full step-by-step workflow](../WORKFLOW.md).

1. Keep the original BrainVision `.vhdr`, `.vmrk` and `.eeg` together. Collect
   the complete PsychoPy audio folder, including `full_session.wav`, the short
   WAVs and logs, and the matching isolated-task experiment tables/pictures.
2. Run `../START_WORKFLOW.cmd`, then use the folder-plus button to supply the
   header, PsychoPy folder, experiment folder and microphone channel. Alternatively,
   run `../ADD_RECORDING.cmd` for file/folder dialogs.
3. The pipeline extracts AUX without changing its timebase, creates a three-tier
   Praat grid, validates the trigger/picture/audio mapping, and adds the recording
   to the same interface. Wait for `Recording ready` before opening it.
4. Expand `Praat files`, open its WAV and watched annotation TextGrid together
   in Praat, and save annotations to that exact filename. New working files always
   go directly in `Desktop/EEG recs/<recording>/`: `<recording>.wav` and
   `<recording>_annotations.TextGrid`. Existing files are not overwritten. The interface reads
   saved changes automatically and computes onset minus S 200 on the EEG timeline.
5. Use `Unsuitable`, `Need help`, and, for S 1 transitive trials, `Ergative`.
   Export the selected recording or all recordings together using the header icons.

There is no extra server, port, manual config, waveform alignment or timing offset
to enter. Only the same isolated-task protocol is supported; changed protocols
are rejected rather than guessed. Reimporting the same recording preserves its
existing annotation file and decisions. Keep the source folders in place and
back up the workflow folder, database, recording configs and annotation snapshots.

## Restarted EEG Without Initial Rest

If the EEG file starts after the complete initial eyes-open/eyes-closed rest block,
the importer accepts the four missing `S 150` log entries only when their labels
are exactly the initial rest start/finish sequence and every remaining EEG trigger
matches the sent log in order. It also accepts a missing complete initial eyes-open
pair when the retained eyes-closed pair matches the logged intervals to trial 001
within 50 ms. This interval comparison resolves identical `S 150` codes without
changing EEG times or estimating a playback offset. Missing trial markers,
incomplete pairs, missing timing evidence and other mismatches still stop the
import. The unmatched rest entries are retained in the
manifest and provenance without invented EEG times. EEG samples and all trial times
remain unchanged. Recover the initial rest from its separate original recording,
not from the later EEG file.

For a split header such as `172ipt2.vhdr`, the working files are
`Desktop/EEG recs/172i/172ipt2.wav` and `172ipt2_annotations.TextGrid` in the same
folder. The viewer retains the actual source name `172ipt2`.

## A Task Split Across Two EEG Files

For a recording such as `203i.vhdr` followed by `203ipt2.vhdr`, keep both original
file sets. Extract each AUX channel separately. The working pairs are
`203i.wav` / `203i_annotations.TextGrid` and
`203ipt2.wav` / `203ipt2_annotations.TextGrid`, all in `Desktop/EEG recs/203i/`.

Register one configuration with an explicitly ordered `parts` array. Each part
contains its own absolute `vhdr`, `stimtrak_wav` and `textgrid` paths. The top-level
paths identify the first part; `audio_dir` and `experiment_dir` identify the
shared PsychoPy session and stimulus folder. Use `import_recording.register`
under `recording_library.import_lock` after preparing and validating both pairs.
The ordinary single-header import form does not infer multiple recording parts.

The combined trigger-code sequence must match the sent log. The viewer keeps
each part's original clock, watches both TextGrids and switches the displayed
Praat filename with the selected trial. SOL is always onset minus S 200 within
one part. A trial crossing the interruption displays a warning; no gap duration
or cross-part latency is invented. For 203i this is trial 013: its S 200 is in the
first part and its S 202 is in the second. Trials 014–120 use the second pair.
Save annotations in the corresponding TextGrid. The combined analysis export
includes the source part, grid hash and interruption flag, and counts the
recording once. Backup/restore preserves both grids under the one recording.

## An Unreadable Short Trial WAV

The interface plays `full_session.wav`, not the short clips. An unreadable main
clip can therefore use its logged full-recording sample window only when the
full WAV and clip bounds are valid and the immediately preceding and following
main clips both match the full WAV byte-for-byte in chronological windows.
The trial displays a warning; the damaged file hash, fallback and validating
neighbors are saved in the manifest and provenance. Original audio is not
repaired or overwritten, and EEG timestamps are never shifted. A readable clip
with mismatched samples still stops the import. This check does not automatically
recover damaged boundary trials or consecutive damaged main clips.
