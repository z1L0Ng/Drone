# Phase2 Top2 Eval Runbook 2026W14

## Data Acquisition Path
- Metadata cache root: `/tmp/audb_cache_2026w14_lexical`.
- Datasets and versions: `quechua@1.0.2`, `nemo@1.0.1` (metadata-only pull via audb).
- Manifest output: `analysis/cross_language_emergency/phase2_top2_lexical_manifest_2026w14.csv`.

## Preprocessing Normalization Steps
1. Join file-level emotion table with sentence table (transcription/raw_text).
2. Unicode normalize (NFKC), trim spaces, lowercase -> `normalized_utterance_text`.
3. Apply canonical mapping: anger/fear->emergency; neutral/calm/calmness->normal; others excluded.
4. Split policy:
   - Quechua: keep source `test`; source `train` split into train/dev by deterministic hash (10% dev).
   - Polish/NEMO: deterministic hash split into train/dev/test = 80/10/10.

## Lexical Cluster Method
1. Build monolingual lexical clusters using `normalized_utterance_text` identity.
2. Keep only `include_flag=1` rows for analysis.
3. Strict cross-language clusters require non-NA `english_gloss`; current batch cannot form strict cross-language clusters yet.

## Reproducible Command Skeletons
```bash
cd /Users/zilongzeng/.codex/worktrees/d2e0/Drone
python3 - <<'PY'
import audb
cache="/tmp/audb_cache_2026w14_lexical"
audb.load("quechua", version="1.0.2", only_metadata=True, full_path=False, cache_root=cache, verbose=False)
audb.load("nemo", version="1.0.1", only_metadata=True, full_path=False, cache_root=cache, verbose=False)
PY
```

## Class Counts by Language and Split (include_flag=1)
| language | split | emergency | normal | included_total |
|---|---|---:|---:|---:|
| Quechua | train | 822 | 832 | 1654 |
| Quechua | dev | 95 | 87 | 182 |
| Quechua | test | 1836 | 1839 | 3675 |
| Polish | train | 1188 | 645 | 1833 |
| Polish | dev | 159 | 80 | 239 |
| Polish | test | 138 | 84 | 222 |

## Excluded Rows (top reasons)
| language | split | exclusion_reason | count |
|---|---|---|---:|
| Quechua | train | non_canonical_emotion_label | 2071 |
| Quechua | train | missing_transcription_text | 2 |
| Quechua | dev | non_canonical_emotion_label | 229 |
| Quechua | test | non_canonical_emotion_label | 4599 |
| Quechua | test | missing_transcription_text | 4 |
| Polish | train | non_canonical_emotion_label | 1213 |
| Polish | train | sensitivity_only_surprise | 531 |
| Polish | dev | non_canonical_emotion_label | 151 |
| Polish | dev | sensitivity_only_surprise | 80 |
| Polish | test | non_canonical_emotion_label | 154 |
| Polish | test | sensitivity_only_surprise | 58 |

## Risk Notes
- License risk: `nemo` is CC-BY-NC-SA (research-friendly, non-commercial constraint).
- Domain shift: both are acted/scripted emotional speech; operational emergency speech mismatch risk remains.
- Imbalance risk: per-split class distributions should be monitored before downstream statistics.
- Lexical comparability risk: missing English gloss blocks strict cross-language gloss clustering in current batch.
