# This Week TODO (PDT, Week of 2026-03-23)

## Weekly Goal (Drone Only)
- Lock the current best embedding-KD baseline.
- Separate gains from embedding KD vs emergency-only pitch/volume augmentation.
- Validate pre-warm curriculum for noisy student training.
- Recheck why logits KD underperforms.
- Start cross-language emergency acoustic analysis.
- Prepare next-round data collection protocol.

## Hard Constraints
- Training: server (full dataset).
- Coding/evaluation/plotting: local.
- Every handoff must be logged in `docs/handoff_log.md`.
- Ignore CDC-related work.
- Priority 6 (real-recording cleanup) is removed this week.

## Daily Execution Checklist
- [ ] `git status` clean/controlled before each handoff.
- [ ] Update this TODO with progress and blockers.
- [ ] Append one row in `docs/handoff_log.md` with command + outputs + next action.

## Priority 1 — Best Embedding KD Baseline
- [ ] Run server training for `best_embed_kd`.
- [ ] Run local eval to generate:
  - `experiments/best_embed_kd/config.yaml`
  - `experiments/best_embed_kd/best_model.ckpt` (symlink)
  - `experiments/best_embed_kd/metrics.json`
  - `experiments/best_embed_kd/confusion_matrix.png`
  - `experiments/best_embed_kd/summary.md`

## Priority 2 — Ablation (A/B/C/D)
- [ ] A: no KD + no emergency augmentation
- [ ] B: embedding KD only
- [ ] C: augmentation only
- [ ] D: embedding KD + augmentation
- [ ] Generate:
  - `experiments/ablation_embed_vs_aug/comparison_table.csv`
  - `experiments/ablation_embed_vs_aug/ablation_summary.md`

## Priority 3 — Prewarm / Curriculum
- [ ] Direct noisy training
- [ ] Clean prewarm -> noisy training
- [ ] (Optional) noise fade-in
- [ ] Export first-10-epoch curves:
  - `experiments/prewarm_curriculum/learning_curves.png`
  - `experiments/prewarm_curriculum/learning_curves.csv`
- [ ] Write:
  - `experiments/prewarm_curriculum/prewarm_summary.md`

## Priority 4 — Logits KD Recheck
- [ ] logits_only
- [ ] ce_plus_logits
- [ ] embed_only_reference
- [ ] Write:
  - `experiments/logits_kd_recheck/comparison_table.csv`
  - `experiments/logits_kd_recheck/kd_failure_analysis.md`

## Priority 5 — Cross-language Analysis
- [ ] Standardize local data from:
  - `local_data/cross_language/<lang>/<style>/*.wav`
- [ ] Generate:
  - `analysis/cross_language_emergency/english_emergency_vs_normal.png`
  - `analysis/cross_language_emergency/chinese_emergency_vs_normal.png`
  - `analysis/cross_language_emergency/cross_language_band_compare.png`
  - `analysis/cross_language_emergency/avg_energy_curves.png`
  - `analysis/cross_language_emergency/findings.md`

## Priority 7 — Data Collection Plan
- [x] `data_collection_plan/protocol.md`
- [x] `data_collection_plan/target_counts.csv`

## Status Log
- 2026-03-23:
  - Done: weekly workflow scripts scaffolded under `scripts/`.
  - Done: train script now exports run config + history CSV.
  - Done: handoff protocol/log docs created under `docs/`.
  - Next: execute server training and run local evaluation pipeline.
