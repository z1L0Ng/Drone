# Weekly Report Draft (2026w14)

## 1. Executive Summary
- Weekly mainline decision:
  - `preprocess_ext`: adopt
  - `branch_trial`: defer
  - `baseline`: keep as reference
- Evidence priority rule:
  - server weekly metrics decide weekly mainline promotion;
  - local real-world and phase2 lexical gates provide deployment transfer checks.

## 2. Model Training Outcomes (Server Evidence)
Source: `weeklyresult/weekly_drone_2026w14/*`

| Model | Accuracy | Emergency F1 | Weighted F1 | Weekly Decision |
|---|---:|---:|---:|---|
| baseline | 0.85 | 0.81 | 0.84 | reference |
| preprocess_ext | 0.88 | 0.87 | 0.88 | adopt |
| branch_trial | 0.84 | 0.79 | 0.83 | defer |

Key takeaway:
- `preprocess_ext` is the strongest weekly candidate by both overall and emergency metrics.

## 3. Local Real-World Gate (`testset/`)
Source: `result/weekly_wrapup_2026w14/local_realworld_*`

Inference-only accuracy:
- baseline: `0.6586`
- preprocess_ext: `0.6934`
- branch_trial: `0.6675`

Finetune (same split cache):
- baseline: `0.6725 -> 0.7857` (`+0.1132`)
- preprocess_ext: `0.6914 -> 0.7763` (`+0.0849`)
- branch_trial: `0.6819 -> 0.7776` (`+0.0957`)

Interpretation:
- deployment-side no-finetune behavior favors `preprocess_ext`;
- adaptation headroom is largest for `baseline`.

## 4. Acoustic Evidence and Multilingual Progress
English phase1:
- emergency vs normal separation remains stable (feature-level consistency).
- domain-shift risk remains: acted-clean speech vs real emergency audio.

Phase2 lexical pipeline:
- top2 languages locked: `Quechua`, `Polish`.
- strict gloss-unblock complete:
  - strict cluster count: `8`
  - strict-covered rows: `4424/7805`

Top2 strict benchmark gate:
- benchmark usable rows (`use_for_eval=1`): `7805`
  - Quechua: `5511`
  - Polish: `2294`
- local gate recommendation:
  - default: `baseline`
  - emergency-first fallback: `branch_trial`

## 5. Decision Reconciliation (No Conflict Rule)
- Weekly mainline keeps `preprocess_ext` (server-priority rule).
- Phase2 lexical local gate selects `baseline` as multilingual deployment-default on strict benchmark.
- Emergency-first scenario may use `branch_trial`, with explicit threshold calibration follow-up.

## 6. Risks and Controls
- Risk: server winner and local lexical winner differ.
  - Control: maintain two-level decision scope (weekly mainline vs multilingual deployment tuning).
- Risk: lexical benchmark composition drift across refreshes.
  - Control: lock `use_for_eval=1` filter and shared split cache for all model comparisons.

## 7. Next Week Action Items
1. Run threshold calibration sweep for emergency-first fallback (`branch_trial`) on strict benchmark.
2. Keep weekly local gate mandatory (inference + finetune, shared split cache).
3. Expand lexical multilingual pool only under the same mapping contract and transcript/gloss quality rules.

## 8. Materials for Overleaf Sync
- `result/weekly_wrapup_2026w14/meeting_brief_2026w14.md`
- `result/weekly_wrapup_2026w14/decision_table.md`
- `result/weekly_wrapup_2026w14/related_work_delta.md`
- `result/weekly_wrapup_2026w14/phase2_top2_local_eval/phase2_top2_recommendation.md`
