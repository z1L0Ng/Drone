# Phase2 Lexical Alignment 2026W14

## Inputs
- `phase2_multilingual_dataset_manifest_2026w14.csv`
- `phase2_mapping_audit_2026w14.md`
- `multilingual_mapping_contract_2026w14.md`

## Mapping vs Lexical Separation
- Emotion mapping contract remains unchanged: mainline `emergency=anger+fear`, `normal=neutral(+calm)`, `surprise` sensitivity-only.
- Lexical comparability is evaluated independently from emotion labels and requires usable utterance text or validated gloss clusters.

## Per-Language Lexical Availability

| language | rows_total | rows_with_text | rows_without_text | strict | partial | none | status |
|---|---:|---:|---:|---:|---:|---:|---|
| Chinese (Mandarin) | 6 | 0 | 6 | 0 | 0 | 6 | no local transcript/text staged |
| English | 36 | 36 | 0 | 0 | 36 | 0 | template IDs available (no full transcript text in current artifacts) |
| French | 8 | 0 | 8 | 0 | 0 | 8 | no local transcript/text staged |
| German | 8 | 0 | 8 | 0 | 0 | 8 | no local transcript/text staged |
| Italian | 10 | 0 | 10 | 0 | 0 | 10 | no local transcript/text staged |
| Portuguese (Brazil) | 6 | 0 | 6 | 0 | 0 | 6 | no local transcript/text staged |

## Top Comparable Gloss Clusters
- None in current batch.
- Reason: multilingual rows currently have no staged utterance text/transcript, so no validated English-target gloss clusters can be formed.

## Mismatch Reasons
1. Tier-1/Tier-2 multilingual datasets in phase2 manifest are currently label-level planned entries; lexical transcripts are not staged in local assets.
2. English reference (CREMA-D) contributes template sentence IDs, but current artifacts do not include verified full sentence text mapping.
3. Therefore lexical comparability cannot be upgraded from `none` to `strict` for non-English languages in this batch.
