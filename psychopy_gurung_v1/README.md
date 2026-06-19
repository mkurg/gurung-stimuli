# Gurung PsychoPy 120-Trial First Draft

This is a first Builder-compatible draft based on the design described on 2026-06-06.

- Stimulus source: set/folder `1` from the Gurung trial viewer data.
- Main trials: 30 datasets x 4 conditions = 120 trials.
- Trial order: practice runs in CSV order; main picture sequences are shuffled as one 120-trial list at runtime, then split into 40/40/40 for the breaks.
- Breaks: after trials 40 and 80.
- Between-trial images: unique landscape photos sampled from `between_trials/Nepal 2025` and copied into `BetweenTrials/`; practice uses its assigned CSV images except for the speaker-icon screen after practice sequence 2, the extra practice-end probe uses one more Nepal image, and main images are shuffled at runtime without reusing practice images.
- Between-trial audio probes: 10% of main trials are selected at runtime; `Audio/tsakyali.wav`, `Audio/bucketdog_noerg.wav`, and `Audio/chickencorn_erg.wav` each occur on one third of those trials; lockout is 10 seconds; the first main Nepal screen after practice or any break can never be an audio-probe screen.
- Practice fixed audio probes: after practice sequence 2, the experiment plays `Audio/practice_end.wav` on the centered speaker-icon screen; after practice sequences 4, 7, and 10, it plays `Audio/tsakyali.wav`, `Audio/bucketdog_noerg.wav`, and `Audio/chickencorn_erg.wav`, respectively, on Nepal-image screens. These screens use the same 10-second lock as main probes.
- Practice uses the numbered practice-story images in CSV order. Stories 1 and 2 start `Audio/tsakyali.wav`, `Audio/bucketdog_noerg.wav`, and `Audio/chickencorn_erg.wav` simultaneously with pictures 1, 2, and 3; stories 3-10 play `Audio/tsakyali.wav` before the last picture.
- Breaks show `Stimuli/break.png`; space is locked for 30 seconds.
- Main recordings are named with image set, condition, and picture identifier.
- Practice recordings are named with practice trial number and picture number.
- Microphone recordings are stored in `recordings/<participant>_<date-time>/` for each run.
- Recordings keep a 0.6-second post-space grace tail in the background before closing each segment, so buffered microphone audio is not clipped while the next screen can appear immediately.
- Main PNGs are local packaged copies in `MainStimuli/`, downsampled to max `900px` on the long edge. This avoids loading trial textures from the Google Drive cloud-storage mount during the run.
- All sequence pictures use the same on-screen size across 3- and 4-picture trials; each sequence row is group-centered with a small randomized horizontal and vertical jitter.

Open `gurung_120_v1.psyexp` in PsychoPy Builder.

Source root used:

```text
/Users/matveikurzukov/Library/CloudStorage/GoogleDrive-apazent@gmail.com/.shortcut-targets-by-id/1exBA-7XrpLfZc6s8oGNYTbmjGsu5dT6p/Gurung stimuli
```

The main trial routine uses a Code Component because trials may contain either 3 or 4 images.
