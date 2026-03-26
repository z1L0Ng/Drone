# Drone Handoff Log (WEEKLY_TAG=drone_2026w13)

## Purpose
- Keep local coding/evaluation and server training synchronized.
- Every handoff must have one row below.

## Required Fields
| Time | Side | Commit | Command | Outputs | Next | Risk |
|---|---|---|---|---|---|---|

## Handoff Checklist
1. Run `git status` and confirm only expected files are changed.
2. Update `TODO_THIS_WEEK.md` with the day status.
3. Append one row in this file with exact commands and output paths.
4. If training is running, include PID/log path.
5. If blocked, include explicit blocker and owner.

## Entries
| Time | Side | Commit | Command | Outputs | Next | Risk |
|---|---|---|---|---|---|---|
| 2026-03-23 15:00 PDT | local | pending | bootstrap weekly workflow scripts and docs | `docs/`, `scripts/`, `experiments/` scaffolding | run server weekly training script | none |
| 2026-03-23 21:05 PDT | local | working-tree (uncommitted) | `bash scripts/run_weekly_local_eval.sh`; `python scripts/standardize_cross_language_audio.py`; `python scripts/analyze_cross_language_emergency.py` | `experiments/*` pending summaries + `analysis/cross_language_emergency/*` plots/findings | run server training then rerun local eval with real checkpoints | local env lacks TensorFlow for checkpoint eval |
| 2026-03-26 09:15 CDT | server | working-tree (docs update pending commit) | stop weekly run (`kill -TERM/-KILL 2504537 2504551 2996289`) after progress review | completed: `baseline`, `ablation exp_A/B/C/D`, `prewarm direct_noisy/prewarm_clean_then_noisy`, `logits_recheck logits_only`; in-progress interrupted: `logits_recheck ce_plus_logits` around epoch 22/50; log: `logs/weekly_drone_2026w13_20260325_122600.log` | commit docs freeze-point; then either resume remaining logits jobs or proceed local eval/report | partial logits suite; no final weekly aggregate yet |
