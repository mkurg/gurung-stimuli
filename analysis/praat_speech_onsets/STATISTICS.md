# Descriptive Statistics and Figures

The statistics scripts and frozen report directories preserve the previous
seminar and onset summaries. These are historical outputs, not live counters.

## Latest Seminar Figures

`seminar_stats/run_20261015_01` contains 12 figures and a complete PDF report for
the 13 participants annotated at that time. Its cohort has 1,338 eligible trials:
640 Itr, 353 Tr ERG and 345 Tr zero. Overall mean SOL was 1,399.8 ms, median
1,313.6 ms; 100 eligible responses had Need help flags (7.5%). It includes
participant counts, latency distributions, noun/action/indefinite-marker
associations and participant speed versus ERG use/balance.

These figures do not include later work in 133i, 134i, 141i or 142i. The current
saved annotation backup is selected by `latest_backup.json`; do not report the
October 15 graphs as summaries of all 17 recordings.

The original source snapshot, SHA-256 manifest, CSV tables and figure-generation
scripts accompany each seminar output. Raw audio/EEG and duplicate distribution
ZIPs are excluded from Git, as are temporary PDF-rendering QA images.

## Reproduce a Frozen Report

Install `requirements-restore.txt`. From `analysis/praat_speech_onsets`, run:

```powershell
python seminar_stats.py --snapshot seminar_stats/run_20261015_01/source_snapshot.json --output-dir regenerated_stats
python ergative_associations.py --snapshot regenerated_stats/source_snapshot.json --condition-table-dir "../../isolated part/Conds" --output-dir regenerated_stats
python action_sol_stats.py --source-dir regenerated_stats
python participant_erg_sol.py --source-dir regenerated_stats
python package_seminar.py --source-dir regenerated_stats
```

To collect a fresh snapshot from the running interface instead, omit `--snapshot`
and pass `--expected-participants 17` to the first command. Only saved Praat work
is collected; use a new output directory for each run.

Eligible responses require a saved nonblank transcription, one valid acoustic
onset and no Unsuitable flag. Need help remains included. SOL is the difference
between acoustic onset and EEG S200. No SOL cutoff, outlier trimming, participant
exclusion or EEG artifact rejection is implicit in these figures.

ERG is the manual flag, not inferred from spelling. Tr zero means not marked
ERG, including absent saved decisions. Noun and indefinite-marker coding is
provisional and uses the supplied codebook; no marker is not called definite.
The plots and participant-level correlations are descriptive, not causal effects
or adjusted condition comparisons. Review the per-trial coding before inference.
