# Gurung PsychoPy 120-Trial First Draft

This is a first Builder-compatible draft based on the design described on 2026-06-06.

- Stimulus source: set/folder `1` from the Gurung trial viewer data.
- Main trials: 30 datasets x 4 conditions = 120 trials.
- Trial order: fixed random order, seed `20260606`.
- Breaks: after trials 40 and 80.
- Between-trial images: random images copied from `between_trials/` into `BetweenTrials/`.
- Between-trial audio probes: 12 rows marked in `Conds/main_all_120.csv`; audio is `Audio/tsakyali.wav`; lockout is 10 seconds.
- Practice uses old practice images/audio, starts each trial with a random between-trial image, and plays `Audio/tsakyali.wav` before the last picture.
- Breaks show `Stimuli/break.png`; space is locked for 30 seconds.
- Main recordings are named with image set, condition, and picture identifier.
- Practice recordings are named with practice trial number and picture number.
- Main PNGs are local packaged copies in `MainStimuli/`, downsampled to max `900px on the long edge. This avoids loading trial textures from the Google Drive cloud-storage mount during the run.

Open `gurung_120_v1.psyexp` in PsychoPy Builder.

Source root used:

```text
/Users/matveikurzukov/Library/CloudStorage/GoogleDrive-apazent@gmail.com/.shortcut-targets-by-id/1exBA-7XrpLfZc6s8oGNYTbmjGsu5dT6p/Gurung stimuli
```

The main trial routine uses a Code Component because trials may contain either 3 or 4 images, and the transitive/intransitive target image is dynamically centered.
