# Gurung PsychoPy Discourse Experiment

This is the Builder-compatible discourse experiment.

- Main picture stimuli are the committed JPEGs under `JpegStimuliFullRes/`.
- At the start dialog, choose experimental `list` 1 or 2. Each list has 240 picture-sequence trials.
- Trial order: practice runs in CSV order; the selected main list is shuffled at runtime on every run, then split into 40/40/40/40/40/40 for the breaks.
- Breaks: after trials 40, 80, 120, 160, and 200.
- Between-trial images: unique landscape photos sampled from `between_trials\Nepal 2025` and copied into `BetweenTrials/`; practice uses its assigned CSV images except for the speaker-icon screen after practice sequence 2, the extra practice-end probe uses one more Nepal image, and main images are shuffled at runtime without reusing practice images.
- Between-trial audio probes: 10% of main trials are selected at runtime; the four `Audio/new_disc_q_*.wav` questions each occur 6 times per 240-trial list; the first main Nepal screen after practice or any break can never be an audio-probe screen.
- EEG triggers are logged to `recordings/<participant>_l<list>_<date-time>/eeg_triggers.csv`. If `eeg_port` is filled in, the same trigger codes are also sent as single-byte serial pulses using `trigger_pulse_ms` as pulse duration.
- Discourse trigger codes: optional early pre-target picture 198, picture before target 199, target picture 200, condition 1-4 at 200 ms after target onset, item 1-120 at 400 ms after target onset, optional post-target picture 201, trial-end button press 202.
- Practice fixed audio probes: after practice sequence 2, the experiment plays `Audio/new_disc_instr2.wav` on the centered speaker-icon screen; after practice sequences 4, 7, and 10, it plays three of the `Audio/new_disc_q_*.wav` questions on Nepal-image screens.
- Speaker-icon audio screens can be replayed with Enter and can advance with Space even before the current playback finishes; the first instruction audio starts only after Space is pressed.
- Nepal-image audio probes are treated as listener questions: the audio plays first, then listener-response recording starts automatically; Space ends the response and advances only after at least 10 seconds of recording.
- Practice uses the numbered practice-story images in CSV order. Stories 1 and 2 start the matching `Audio/new_disc_orange_*.wav` and `Audio/new_disc_towel_*.wav` files simultaneously with pictures 1, 2, and 3; stories 3-10 play `Audio/new_disc_tsakyali.wav` before the last picture.
- Breaks show `Stimuli/break.png`; space is locked for 30 seconds.
- Main recordings are named with runtime main-trial number, list tag, image set, `cond`, and picture identifier.
- Practice recordings are named with participant, practice trial number, and picture number, for example `arrate_practice_08_pic02.wav`.
- Listener-response recordings are stored in `recordings/<participant>_l<list>_<date-time>/listener responses/`; main listener filenames include participant, `listener`, list tag, runtime main-trial number, image set, and `cond` for the trial immediately before the question.
- Microphone recordings are stored in `recordings/<participant>_l<list>_<date-time>/` for each run.
- Each recordings folder now also contains a continuous raw `full_session.wav`, `recording_events.csv`, and `recording_segments.csv`. The old per-picture response WAV files are still written with the same names, but they are clipped from the continuous recording using logged picture-onset and space-press sample indices, with a 0.5-second post-space tail.
- All sequence pictures use the same on-screen size across 3- and 4-picture trials; each sequence row is group-centered with horizontal jitter capped at 30% of the picture width.

Open `gurung_120_v1.psyexp` in PsychoPy Builder.

The main trial routine uses a Code Component because trials may contain either 3 or 4 images.
