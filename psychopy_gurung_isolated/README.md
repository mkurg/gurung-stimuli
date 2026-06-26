# Gurung Isolated PsychoPy Experiment

This is the isolated-picture version of the Gurung experiment.

- Resting-state sequence comes before the experiment instruction screen: eyes-open prompt, 2-minute blank screen, 1.3-second xylophone-style tritone chime, eyes-closed prompt, 2-minute blank screen, 1.3-second xylophone-style tritone chime, ready prompt with the eyes-open icon.
- Resting-state blank screens end automatically after 120 seconds, but Space can move forward earlier.
- The isolated instruction screen uses `Audio/isolated_instr.wav`; the first Space starts audio, and a later Space advances.
- Practice has 10 fixed single-picture trials in CSV order, using the `isolated_practice_*.png` files in `Stimuli/`.
- Practice trials 1 and 2 are the voiced orange-picking and goat-milking pictures; they play `Audio/chickencorn_erg.wav` simultaneously with the picture. Practice trials 3-10 have no picture audio.
- The main part has 120 isolated target-picture trials built from the Discourse main table. Target pictures are the `tr_target` or `it_target` image from each Discourse trial.
- Main trial order is reshuffled at runtime on every run, then split into 60 trials, a 30-second break, and 60 trials.
- There are no Nepal images, questions, or audio probes between isolated trials.
- Picture size matches the Discourse sequence pictures, but isolated pictures have no jitter: every practice and main picture is always centered at `(0, 0)`.
- Microphone recording uses the same continuous-session WAV and reproducible clipping scheme as the Discourse experiment.

Open `gurung_isolated_v1.psyexp` in PsychoPy Builder.
