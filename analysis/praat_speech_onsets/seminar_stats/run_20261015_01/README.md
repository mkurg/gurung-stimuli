# Seminar Summary: 13 Participants

Frozen saved-data snapshot: 2026-10-15T20:21:07.023952+00:00.

Open output/pdf/lab_seminar_13_participants.pdf for all 12 figures.
FULL_REPORT.md contains all counts, definitions, tables and interpretation notes.
Individual high-resolution PNGs are alongside this file. CSV tables use UTF-8 with BOM.

Eligible = main trial + saved nonblank transcription + exactly one valid onset + not Unsuitable.
Need help is included. No SOL cutoff, participant exclusion, outlier trimming or EEG artifact rejection.
SOL = saved acoustic onset minus EEG S200. ERG is the manual flag; not marked ERG is not independently verified absence.
Noun and indefinite-marker coding is provisional; inspect trial_linguistic_coding.csv.

## Reproduce From This Snapshot

Requires Python with numpy, scipy, matplotlib, pillow, reportlab and pypdf.
Run from this extracted bundle; use a new output directory:

```powershell
python reproducibility/seminar_stats.py --snapshot source_snapshot.json --output-dir regenerated
python reproducibility/ergative_associations.py --snapshot regenerated/source_snapshot.json --codebook reproducibility/ergative_codebook.json --condition-table-dir reproducibility/condition_tables --output-dir regenerated
python reproducibility/action_sol_stats.py --source-dir regenerated
python reproducibility/participant_erg_sol.py --source-dir regenerated
python reproducibility/package_seminar.py --source-dir regenerated
```

To collect newer saved data on the original computer, omit --snapshot in the first command and add --expected-participants 13.
The interface must be running for a new collection; frozen-snapshot reproduction does not need it.
Run the four test modules from the reproducibility directory with python -m unittest.
MANIFEST.json records SHA-256 hashes of included files. Original EEG, audio and working annotations were not changed.
The bundle contains participant transcriptions and decisions, but no raw audio/EEG.
