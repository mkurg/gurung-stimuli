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
