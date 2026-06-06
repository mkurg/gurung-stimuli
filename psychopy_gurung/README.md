# Gurung PsychoPy Package

Generated for the Gurung picture-sequence experiment.

This lightweight workspace package points the CSV image columns at the Google Drive source PNGs.

## Run

Open `gurung_experiment.py` in PsychoPy Coder, or run it with the PsychoPy Standalone Python:

```sh
/Applications/PsychoPy.app/Contents/MacOS/python gurung_experiment.py
```

The participant dialog defaults to the balanced counterbalancing table `Conds/trials_list1.csv`.

## Condition Tables

- `Conds/trials_list1.csv` ... `Conds/trials_list8.csv`: balanced 30-trial participant lists. Each list shows one condition per dataset and balances set 1/set 2.
- `Conds/trials_all_240.csv`: all datasets x both sets x all four path types, for audit or piloting.
- `Conds/trials_set1_all_conditions.csv` and `Conds/trials_set2_all_conditions.csv`: all four path types for one stimulus set.
- `Conds/practice.csv`: four real-stimulus practice examples. The experiment dialog defaults practice to `no` until separate practice-only stimuli are approved.

## Source

Source root used at generation time:

```text
/Users/matveikurzukov/Library/CloudStorage/GoogleDrive-apazent@gmail.com/.shortcut-targets-by-id/1exBA-7XrpLfZc6s8oGNYTbmjGsu5dT6p/Gurung stimuli
```

The four path types follow the current viewer/docs:

- `transitive_cohesive`: `coh_1 -> coh_2 -> tr_target`
- `intransitive_cohesive`: `coh_1 -> coh_2 -> it_target -> end_coh_it`
- `transitive_incohesive`: `ic_1 -> tr_target -> end_ic_tr`
- `intransitive_incohesive`: `ic_1 -> it_target -> end_ic_it`
