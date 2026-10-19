# Lab Seminar: Descriptive Statistics

Snapshot: 14 October 2026.

## Counting Rules

All 12 loaded recordings are included. Main trials only; practice and session events are excluded. SOL = annotated acoustic speech onset minus S200, in milliseconds. Eligible trials have nonblank saved transcription, exactly one valid speech onset, and are not marked Unsuitable. Need help remains included. No SOL cutoff, outlier trimming, participant exclusion, or EEG artifact rejection was applied.

Tr ERG means marked Ergative. Tr zero (Tr ∅) means not marked Ergative; a missing saved decision is not independent confirmation that case marking was absent.

## Overall

- Participants: 12; recorded main trials: 1440.
- Transcribed: 1320; valid single onset: 1317; eligible: 1110.
- Unsuitable: 210; pending annotations among non-Unsuitable trials: 120.
- Need help: 108 / 1440 main trials (7.5%); 93 / 1110 eligible trials (8.4%). Need help and Unsuitable overlap on 15 trials.
- Eligible categories: Itr 529; Tr ERG 272; Tr ∅ 309.
- Trial-weighted SOL: mean 1391.1 ms; median 1311.7 ms; SD 434.1 ms.
- SOL middle 50%: 1108.5-1560.2 ms; range 699.4-4654.8 ms.
- Equal-weight mean of participant mean SOLs: 1398.2 ms.

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
| 122i | 120/120 | 96 | 46 | 4 | 46 | 24 | 21 | 18 | 1260 | 1181 |
| 131i | 0/120 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | n.a. | n.a. |

## SOL by Category

| Category | n | Mean (ms) | Median (ms) | SD (ms) |
|---|---:|---:|---:|---:|
| Itr | 529 | 1359.5 | 1278.8 | 420.5 |
| Tr ERG | 272 | 1423.2 | 1325.4 | 477.2 |
| Tr ∅ | 309 | 1416.9 | 1327.2 | 414.3 |

## Timing Eligibility

These are timing counts only, not evidence of artifact-free EEG. For example, SOL >=1000 ms allows 600 ms plus a nominal 400 ms pre-speech gap; >=1200 ms allows 800 + 400 ms; >=1400 ms allows 800 + 600 ms. The gap still needs validation.

| Minimum SOL (ms) | Retained | Retained (%) | Below threshold | Itr | Tr ERG | Tr ∅ |
|---|---:|---:|---:|---:|---:|---:|
| 1000 | 952 | 85.8 | 158 | 442 | 230 | 280 |
| 1100 | 842 | 75.9 | 268 | 390 | 204 | 248 |
| 1200 | 706 | 63.6 | 404 | 325 | 172 | 209 |
| 1250 | 652 | 58.7 | 458 | 291 | 163 | 198 |
| 1400 | 446 | 40.2 | 664 | 194 | 118 | 134 |

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
| 122i | 0 | 0 | 0 | 0 | 0 |
| 131i | 120 | 120 | 0 | 0 | 0 |

Trials with multiple onset marks:

- 072i, main-119, S 89: 2 onset marks; not Unsuitable; excluded pending onset review.
- 091i, main-031, S 110: 2 onset marks; already marked Unsuitable.
- 101i, main-001, S 95: 2 onset marks; already marked Unsuitable.

## Figures

![01_sol_distribution.png](01_sol_distribution.png)

## Reproducibility

Source: saved Praat TextGrids and recording-scoped trial decisions in the local reference interface. The source snapshot, source hashes, all-trial rows and summary JSON accompany this report. Charts describe this frozen snapshot and do not update automatically. Original annotations and flags were not edited.
