# Lab Seminar: Descriptive Statistics

Snapshot: 13 October 2026.

## Counting Rules

All ten recordings are included. Main trials only; practice and session events are excluded. SOL = annotated acoustic speech onset minus S200, in milliseconds. Eligible trials have nonblank saved transcription, exactly one valid speech onset, and are not marked Unsuitable. Need help remains included. No SOL cutoff, outlier trimming, participant exclusion, or EEG artifact rejection was applied.

Tr ERG means marked Ergative. Tr zero (Tr ∅) means not marked Ergative; a missing saved decision is not independent confirmation that case marking was absent.

## Overall

- Participants: 10; recorded main trials: 1200.
- Transcribed: 1200; valid single onset: 1197; eligible: 1014.
- Unsuitable: 185; pending annotations among non-Unsuitable trials: 1.
- Need help: 87 / 1200 main trials (7.2%); 75 / 1014 eligible trials (7.4%). Need help and Unsuitable overlap on 12 trials.
- Eligible categories: Itr 483; Tr ERG 268; Tr ∅ 263.
- Trial-weighted SOL: mean 1403.5 ms; median 1323.5 ms; SD 442.0 ms.
- SOL middle 50%: 1116.7-1584.6 ms; range 699.4-4654.8 ms.
- Equal-weight mean of participant mean SOLs: 1412.0 ms.

SD above describes trials, not uncertainty of the group mean. No inferential test or Gaussian assumption is used.

## Participant Summary

| Participant | Transcribed | Eligible | Itr | Tr ERG | Tr ∅ | Unsuitable | Need help (all) | Need help (eligible) | Mean SOL (ms) | Median SOL (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 072i | 120/120 | 117 | 57 | 44 | 16 | 2 | 11 | 11 | 1593 | 1538 |
| 073i | 120/120 | 98 | 41 | 35 | 22 | 22 | 8 | 6 | 1287 | 1175 |
| 081i | 120/120 | 113 | 54 | 29 | 30 | 7 | 9 | 9 | 1350 | 1295 |
| 082i | 120/120 | 113 | 56 | 15 | 42 | 7 | 14 | 13 | 1352 | 1298 |
| 091i | 120/120 | 73 | 34 | 19 | 20 | 47 | 12 | 9 | 1588 | 1509 |
| 092i | 120/120 | 100 | 44 | 51 | 5 | 20 | 8 | 4 | 992 | 955 |
| 101i | 120/120 | 84 | 37 | 25 | 22 | 36 | 6 | 5 | 1536 | 1472 |
| 111i | 120/120 | 90 | 45 | 3 | 42 | 30 | 4 | 3 | 1711 | 1577 |
| 112i | 120/120 | 111 | 57 | 18 | 36 | 9 | 1 | 1 | 1151 | 1073 |
| 121i | 120/120 | 115 | 58 | 29 | 28 | 5 | 14 | 14 | 1560 | 1460 |

## SOL by Category

| Category | n | Mean (ms) | Median (ms) | SD (ms) |
|---|---:|---:|---:|---:|
| Itr | 483 | 1376.1 | 1291.8 | 425.5 |
| Tr ERG | 268 | 1424.0 | 1325.4 | 480.4 |
| Tr ∅ | 263 | 1433.0 | 1350.4 | 429.6 |

## Timing Eligibility

These are timing counts only, not evidence of artifact-free EEG. For example, SOL >=1000 ms allows 600 ms plus a nominal 400 ms pre-speech gap; >=1200 ms allows 800 + 400 ms; >=1400 ms allows 800 + 600 ms. The gap still needs validation.

| Minimum SOL (ms) | Retained | Retained (%) | Below threshold | Itr | Tr ERG | Tr ∅ |
|---|---:|---:|---:|---:|---:|---:|
| 1000 | 868 | 85.6 | 146 | 406 | 226 | 236 |
| 1100 | 776 | 76.5 | 238 | 365 | 200 | 211 |
| 1200 | 659 | 65.0 | 355 | 308 | 169 | 182 |
| 1250 | 611 | 60.3 | 403 | 278 | 160 | 173 |
| 1400 | 426 | 42.0 | 588 | 191 | 116 | 119 |

## Annotation Checks

Missing transcription and missing/multiple onset counts can overlap, and include Unsuitable trials. Unassigned speech-tier points can include deliberately added resting-state marks; they are preserved and not silently attached to trials.

| Participant | No transcription | No onset | Multiple onsets | Unassigned points | Unassigned text intervals |
|---|---:|---:|---:|---:|---:|
| 072i | 0 | 0 | 1 | 0 | 0 |
| 073i | 0 | 0 | 0 | 0 | 0 |
| 081i | 0 | 0 | 0 | 0 | 0 |
| 082i | 0 | 0 | 0 | 0 | 0 |
| 091i | 0 | 0 | 1 | 0 | 0 |
| 092i | 0 | 0 | 0 | 0 | 0 |
| 101i | 0 | 0 | 1 | 0 | 0 |
| 111i | 0 | 0 | 0 | 0 | 0 |
| 112i | 0 | 0 | 0 | 0 | 0 |
| 121i | 0 | 0 | 0 | 0 | 0 |

Trials with multiple onset marks:

- 072i, main-119, S 89: 2 onset marks; not Unsuitable; excluded pending onset review.
- 091i, main-031, S 110: 2 onset marks; already marked Unsuitable.
- 101i, main-001, S 95: 2 onset marks; already marked Unsuitable.

## Figures

![01_sol_distribution.png](01_sol_distribution.png)
![02_sol_by_participant.png](02_sol_by_participant.png)
![03_transitive_counts.png](03_transitive_counts.png)
![04_progress_and_review.png](04_progress_and_review.png)
![05_sol_by_category.png](05_sol_by_category.png)
![06_eligible_overview.png](06_eligible_overview.png)

## Reproducibility

Source: saved Praat TextGrids and recording-scoped trial decisions in the local reference interface. The source snapshot, source hashes, all-trial rows and summary JSON accompany this report. Charts describe this frozen snapshot and do not update automatically. Original annotations and flags were not edited.
