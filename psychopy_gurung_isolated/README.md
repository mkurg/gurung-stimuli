# Gurung Isolated PsychoPy Experiment

This is the isolated-picture version of the Gurung experiment.

- Resting-state sequence comes before the experiment instruction screen: eyes-open prompt, 2-minute blank screen, 1.3-second xylophone-style tritone chime, eyes-closed prompt, 2-minute blank screen, 1.3-second xylophone-style tritone chime, ready prompt with the eyes-open icon.
- Resting-state blank screens end automatically after 120 seconds, but Space can move forward earlier.
- Resting-state blank intervals send/log trigger 150 at eyes-open start, eyes-open finish, eyes-closed start, and eyes-closed finish.
- The isolated instruction screen uses `Audio/isolated_instr.wav`; the first Space starts audio, and a later Space advances.
- Practice has 10 fixed single-picture trials in CSV order, using the `isolated_practice_*.jpg` files in `Stimuli/`.
- Practice trials 1 and 2 are the voiced orange-picking and goat-milking pictures; they play `Audio/chickencorn_erg.wav` simultaneously with the picture. Practice trials 3-10 have no picture audio.
- At the start dialog, choose experimental `list` 1 or 2. The main part has 120 isolated target-picture trials for the selected list, built from the Discourse list tables.
- Main target pictures are JPEGs referenced from the Discourse `JpegStimuliFullRes/` package with relative paths.
- Main trial order is reshuffled at runtime on every run, then split into 60 trials, a 30-second break, and 60 trials.
- EEG triggers are logged to `recordings/<participant>_l<list>_<date-time>/eeg_triggers.csv`. If `eeg_port` is filled in, the same trigger codes are also sent as single-byte serial pulses using `trigger_pulse_ms` as pulse duration.
- Isolated main trigger codes: target picture onset 200, transitivity condition 1/2 at 200 ms after target onset, item 1-120 at 400 ms after target onset, trial-end button press 202.
- There are no Nepal images, questions, or audio probes between isolated trials.
- Picture size matches the Discourse sequence pictures, but isolated pictures have no jitter: every practice and main picture is always centered at `(0, 0)`.
- Microphone recording uses the same continuous-session WAV and reproducible clipping scheme as the Discourse experiment. Practice recordings use names like `arrate_practice_08_pic01.wav`; main recordings use `isolated_main_l1` or `isolated_main_l2` and isolated `cond_tr`/`cond_it`.

Open `gurung_isolated_v1.psyexp` in PsychoPy Builder.
