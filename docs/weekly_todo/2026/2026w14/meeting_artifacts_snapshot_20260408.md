# Meeting Artifacts Snapshot (2026-04-08)

Purpose:
- Keep a tracked mirror of final pre-meeting conclusions under `docs/`.
- Avoid losing meeting-critical evidence because `result/` is git-ignored.

## Final model decision (2026w14)
- `preprocess_ext`: adopt
- `branch_trial`: defer
- `baseline`: keep_reference

## Server-side metrics snapshot
Source:
- `weeklyresult/weekly_drone_2026w14/{baseline,preprocess_ext,branch_trial}/classification_report_noisy.txt`

| Candidate | Accuracy | Emergency F1 | Decision |
|---|---:|---:|---|
| baseline | 0.85 | 0.81 | keep_reference |
| preprocess_ext | 0.88 | 0.87 | adopt |
| branch_trial | 0.84 | 0.79 | defer |

## Local real-world gate snapshot (`testset/`)
Inference-only source:
- `result/weekly_wrapup_2026w14/local_realworld_eval/*/classification_report.txt`

Finetune source:
- `result/weekly_wrapup_2026w14/local_realworld_finetune/*/summary.csv`

| Candidate | Local Inference Acc | Finetune Original Acc | Finetune Acc | Delta |
|---|---:|---:|---:|---:|
| baseline | 0.6586 | 0.672507 | 0.785714 | +0.113208 |
| preprocess_ext | 0.6934 | 0.691375 | 0.776280 | +0.084906 |
| branch_trial | 0.6675 | 0.681941 | 0.777628 | +0.095687 |

## Acoustic evidence status
Branch reference:
- `origin/codex/acoustic-2026w14-phase1@25deca41`

Meeting-ready package:
- `analysis/cross_language_emergency/meeting_evidence_table_2026w14.md`
- `analysis/cross_language_emergency/onepager_2026w14_phase1.md`
- `analysis/cross_language_emergency/multilingual_priority_scorecard_2026w14.md`
- `analysis/cross_language_emergency/multilingual_mapping_contract_2026w14.md`

## Post-meeting next action
- Launch phase2 multilingual scouting with strict mapping contract.
- Priority languages: Italian/German first, French second.
