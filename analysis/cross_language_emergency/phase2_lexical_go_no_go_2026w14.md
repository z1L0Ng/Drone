# Phase2 Lexical Go/No-Go 2026W14

## Hard Rule Evaluation
- `go` requires strict semantic match + transcript/text available + lexical comparability in {strict, partial} + estimated sample gate pass.
- Current lexical-first batch result: all multilingual candidates are `hold` due transcript/text unavailability in staged assets.

## Candidate Decisions

| language | dataset_name | semantic_match_level | has_transcript_text | lexical_comparability | estimated_sample_gate | recommendation | blocker |
|---|---|---|---|---|---|---|---|
| Italian | EMOZIONALMENTE | strict | no | none | pass | hold | transcript_text_unavailable;lexical_comparability_none |
| German | EMO-DB | strict | no | none | pass | hold | transcript_text_unavailable;lexical_comparability_none |
| French | CaFE | strict | no | none | pass | hold | transcript_text_unavailable;lexical_comparability_none |
| Chinese (Mandarin) | ESD(ZH) | partial | no | none | pass | hold | semantic_match_not_strict;transcript_text_unavailable;lexical_comparability_none |
| Portuguese (Brazil) | EmoUERJ | partial | no | none | pass | hold | semantic_match_not_strict;transcript_text_unavailable;lexical_comparability_none |

## Immediate Action
1. Keep Tier-1 ingest priority: Italian -> German; Tier-2 fallback: French.
2. Unblock lexical path by staging transcript/text assets before any new lexical comparability claim.
3. Recompute this table once transcript rows are no longer `NA`.
