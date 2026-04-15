# Server/Local Sync Protocol (Drone Weekly)

## Scope
- Drone project only.
- Server: training with full dataset.
- Local: coding, evaluation, plotting, reporting.
- Do not run full training locally for weekly mainline updates.

## Global Server Execution Rules (Effective 2026-04-15)
1. Server result root must use `weeklyresult/` (not `result/`) for weekly training artifacts.
   - Required pattern:
     - `weeklyresult/weekly_drone_<year>w<week>/<run_name>/run_config.json`
     - `weeklyresult/weekly_drone_<year>w<week>/<run_name>/classification_report_noisy.txt`
     - `weeklyresult/weekly_drone_<year>w<week>/<run_name>/history/*`
2. Server training must be launched and managed via `tmux`.
   - Session naming pattern:
     - `weekly_<WEEKLY_TAG>_<task>`
   - Do not use one-shot background launch as default for weekly training orchestration.
3. Before dispatching any new server training command from local:
   - local changes for this dispatch must be committed first,
   - commit SHA must be included in handoff message,
   - then server runs that exact commit.

## Fixed Contract
- `WEEKLY_TAG=drone_<year>w<week>` (example: `drone_2026w14`)
- Evaluation schema fields:
  - `run_id, exp_id, kd_variant, aug_flag, prewarm_flag, overall_acc, emergency_recall, emergency_f1, movement_recall`
- Handoff log table schema:
  - `Time | Side | Commit | Command | Outputs | Next | Risk`

## Before Local -> Server Handoff
1. `git fetch --prune origin`
2. `git status`
3. Commit local changes for this dispatch first (avoid large checkpoints)
4. Record commit SHA in handoff content
5. Append handoff row in `docs/weekly_todo/handoff_log.md`
6. Push branch and include commit SHA in handoff row

## Before Server -> Local Handoff
1. Record active training commands and log path
2. Record finished artifacts (`saved_models/` + `weeklyresult/` dirs)
3. Append handoff row in `docs/weekly_todo/handoff_log.md`
4. Push result summaries only (no large checkpoints)

## Week-Specific Contract (Current)
- Weekly tag in use: `drone_2026w15`
- Meeting checkpoint: `2026-04-16` (pre-meeting summary must exist)

## Recommended Log Naming
- `logs/weekly_${WEEKLY_TAG}_${task}_${timestamp}.log`

## Recommended Server Launch Pattern (tmux)
- Start:
  - `tmux new -d -s weekly_${WEEKLY_TAG}_${task} '<train_command>'`
- Inspect:
  - `tmux ls`
  - `tmux capture-pane -pt weekly_${WEEKLY_TAG}_${task} | tail -n 50`
- Keep artifact pointers in `weeklyresult/weekly_${WEEKLY_TAG}/<run_name>/`.

## Post-Sync Local Standard Stage (Mandatory)
After weekly server outputs are synced locally:
1. Run local real-world inference on `testset/` for baseline + weekly candidates.
2. Run local finetune validation on the same `testset/` split cache.
3. Store outputs under weekly wrap-up folders and include delta metrics in meeting brief.
4. Use this stage as a gate before scaling multilingual experiments.

Reference:
- `docs/technical_spec/local_realworld_validation_standard.md`
