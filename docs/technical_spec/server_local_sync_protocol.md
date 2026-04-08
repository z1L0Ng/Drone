# Server/Local Sync Protocol (Drone Weekly)

## Scope
- Drone project only.
- Server: training with full dataset.
- Local: coding, evaluation, plotting, reporting.
- Do not run full training locally for weekly mainline updates.

## Fixed Contract
- `WEEKLY_TAG=drone_<year>w<week>` (example: `drone_2026w14`)
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

## Week-Specific Contract (Current)
- Weekly tag in use: `drone_2026w14`
- Meeting checkpoint: `2026-04-09` (pre-meeting summary must exist)

## Recommended Log Naming
- `logs/weekly_${WEEKLY_TAG}_${task}_${timestamp}.log`

## Post-Sync Local Standard Stage (Mandatory)
After weekly server outputs are synced locally:
1. Run local real-world inference on `testset/` for baseline + weekly candidates.
2. Run local finetune validation on the same `testset/` split cache.
3. Store outputs under weekly wrap-up folders and include delta metrics in meeting brief.
4. Use this stage as a gate before scaling multilingual experiments.

Reference:
- `docs/technical_spec/local_realworld_validation_standard.md`
