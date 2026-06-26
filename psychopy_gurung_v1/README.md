# Gurung PsychoPy 120-Trial First Draft

This is a first Builder-compatible draft based on the design described on 2026-06-06.

- Stimulus source: set/folder `1` from the Gurung trial viewer data.
- Main trials: 30 datasets x 4 conditions = 120 trials.
- Trial order: practice runs in CSV order; main picture sequences are shuffled as one 120-trial list at runtime, then split into 40/40/40 for the breaks.
- Breaks: after trials 40 and 80.
- Between-trial images: unique landscape photos sampled from `between_trials/Nepal 2025` and copied into `BetweenTrials/`; practice uses its assigned CSV images except for the speaker-icon screen after practice sequence 2, the extra practice-end probe uses one more Nepal image, and main images are shuffled at runtime without reusing practice images.
- Between-trial audio probes: 10% of main trials are selected at runtime; `Audio/tsakyali.wav`, `Audio/bucketdog_noerg.wav`, and `Audio/chickencorn_erg.wav` each occur on one third of those trials; the first main Nepal screen after practice or any break can never be an audio-probe screen.
- Practice fixed audio probes: after practice sequence 2, the experiment plays `Audio/practice_end.wav` on the centered speaker-icon screen; after practice sequences 4, 7, and 10, it plays `Audio/tsakyali.wav`, `Audio/bucketdog_noerg.wav`, and `Audio/chickencorn_erg.wav`, respectively, on Nepal-image screens.
- Speaker-icon audio screens can be replayed with Enter and can advance with Space even before the current playback finishes; the first instruction audio starts only after Space is pressed.
- Nepal-image audio probes are treated as listener questions: the audio plays first, then listener-response recording starts automatically; Space ends the response and advances only after at least 10 seconds of recording.
- Practice uses the numbered practice-story images in CSV order. Stories 1 and 2 start `Audio/tsakyali.wav`, `Audio/bucketdog_noerg.wav`, and `Audio/chickencorn_erg.wav` simultaneously with pictures 1, 2, and 3; stories 3-10 play `Audio/tsakyali.wav` before the last picture.
- Breaks show `Stimuli/break.png`; space is locked for 30 seconds.
- Main recordings are named with runtime main-trial number, image set, condition, and picture identifier.
- Practice recordings are named with practice trial number and picture number.
- Listener-response recordings are stored in `recordings/<participant>_<date-time>/listener responses/`; main listener filenames include participant, `listener`, runtime main-trial number, image set, and condition for the trial immediately before the question.
- Microphone recordings are stored in `recordings/<participant>_<date-time>/` for each run.
- Each recordings folder now also contains a continuous raw `full_session.wav`, `recording_events.csv`, and `recording_segments.csv`. The old per-picture response WAV files are still written with the same names, but they are clipped from the continuous recording using logged picture-onset and space-press sample indices, with a 0.5-second post-space tail.
- Main PNGs are local packaged copies in `MainStimuli/`, downsampled to max `900px` on the long edge. This avoids loading trial textures from the Google Drive cloud-storage mount during the run.
- All sequence pictures use the same on-screen size across 3- and 4-picture trials; each sequence row is group-centered with horizontal jitter capped at 30% of the picture width.

Open `gurung_120_v1.psyexp` in PsychoPy Builder.

Source root used:

```text
/Users/matveikurzukov/Library/CloudStorage/GoogleDrive-apazent@gmail.com/.shortcut-targets-by-id/1exBA-7XrpLfZc6s8oGNYTbmjGsu5dT6p/Gurung stimuli
```

The main trial routine uses a Code Component because trials may contain either 3 or 4 images.
