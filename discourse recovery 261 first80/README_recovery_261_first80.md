# Discourse recovery 261 first 80

This is a minimal, self-contained recovery experiment for the first 80 discourse trials shown in the participant 261 List 1 recording-folder screenshots from 2026-08-26.

Run `recovery_261_first80.py` from PsychoPy Coder. The folder includes local copies of the needed JPEG stimuli plus the break/finish images, so it can be downloaded separately from the normal discourse and isolated experiment folders. The task starts with a blank white screen; press Space to begin. It presents only the 80 recovered discourse trials, randomly shuffled on every run, with a 30-second break after 40 trials and a finish sign at the end.

The normal discourse trigger system is preserved:

- 198 = optional early pre-target picture onset
- 199 = picture before target onset
- 200 = target picture onset
- 1-4 = condition trigger at 200 ms after target onset
- 1-120 = item trigger at 400 ms after target onset
- 201 = optional post-target picture onset
- 202 = button-press trial end

Outputs are written to `recordings/<participant>_recovery_l1_first80_<date>/`:

- `trial_order.csv`: randomized runtime order for this recovery run
- `trial_log.csv`: per-trial timing/condition/item metadata
- `eeg_triggers.csv`: every trigger attempt with serial status
- `debug_recovery_runtime.log`: compact runtime notes

Important limitation: the screenshots show original trial number, dataset number, and condition, but not the hidden `stimulus_set`. The generated `Conds/recovery_261_first80_trials.csv` therefore selects the next legal List 1 stimulus set for each visible dataset+condition pair and marks this in `stimulus_set_inference`. If the original laptop's `runtime_main_block1.csv` and `runtime_main_block2.csv` are available, use those files to rebuild an exact version.
