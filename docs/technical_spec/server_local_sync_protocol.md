# Server/Local Sync Protocol (Drone Week 2026w13)

## Scope
- Drone project only.
- Server: training with full dataset.
- Local: coding, evaluation, plotting, reporting.

## Fixed Contract
- `WEEKLY_TAG=drone_2026w13`
- Evaluation schema fields:
  - `run_id, exp_id, kd_variant, aug_flag, prewarm_flag, overall_acc, emergency_recall, emergency_f1, movement_recall`
- Handoff log table schema:
  - `Time | Side | Commit | Command | Outputs | Next | Risk`

## Before Local -> Server Handoff
1. `git fetch --prune origin`
2. `git status`
3. Commit only scripts/docs/summaries (avoid large checkpoints)
4. Append handoff row in `docs/weekly_todo/handoff_log.md`
5. Push branch and include commit SHA in handoff row

## Before Server -> Local Handoff
1. Record active training commands and log path
2. Record finished artifacts (model/result dirs)
3. Append handoff row in `docs/weekly_todo/handoff_log.md`
4. Push result summaries only (no large checkpoints)

## Recommended Log Naming
- `logs/weekly_${WEEKLY_TAG}_${task}_${timestamp}.log`
