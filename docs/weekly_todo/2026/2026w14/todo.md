# This Week TODO (CDT, Meeting before 2026-04-09)

## Weekly Goal (Drone, Balanced Delivery)
- Deliver meeting-ready conclusions before Thursday.
- Keep outputs reproducible and traceable under `drone_2026w14`.
- Enforce local/server split: local for code/eval/docs, server for training only.

## Hard Constraints
- Training: server only (full dataset).
- Coding/evaluation/plotting/reporting: local only.
- Every handoff must be logged in `docs/weekly_todo/handoff_log.md`.

## Daily Execution Checklist
- [ ] `git status` is clean/controlled before each handoff.
- [ ] Update this file with progress, blockers, and next action.
- [ ] Append one row in `docs/weekly_todo/handoff_log.md` with command + outputs + next owner.

## Multi-Agent Coordination Board
- [x] Assign acoustic analysis scope to acoustic agent.
- [x] Assign model/config scope to model agent.
- [x] Assign server execution protocol to server operator.
- [x] Collect acoustic agent phase-1 outputs (`dataset_options_2026w14.md`, `dataset_manifest_2026w14.csv`).
- [x] Collect acoustic agent phase-1.2 scanned-count refresh (`sample_count_table_2026w14.csv`; CREMA-D scanned non-zero, ESD pending license-gated import).
- [x] Collect model agent command pack for `preprocess_ext` and `branch_trial`.
- [ ] Receive server startup and completion receipts for both runs.
- [x] Receive server `preprocess_ext` startup receipt (PID/LOG/first 30 lines; GPU visible).
- [ ] Keep Notion checklist and repo docs synchronized after each receipt.
- [x] Coordination reference doc:
  - `docs/weekly_todo/2026/2026w14/agent_management_playbook.md`
- [x] Dispatch prompt pack prepared:
  - `docs/weekly_todo/2026/2026w14/dispatch_prompts.md`

## Branch / Model / Training Changes (This Week)
| Date | Branch | Type | Change | Paths | Status |
|---|---|---|---|---|---|
| 2026-04-07 | `main` | planning | Lock meeting-week execution plan and checkpoints/report paths | `docs/weekly_todo/2026/2026w14/`, `docs/weekly_todo/handoff_log.md` | done |
| 2026-04-07 | `main` | coordination | Multi-agent management playbook and handoff protocol activated | `docs/weekly_todo/2026/2026w14/agent_management_playbook.md` | done |
| 2026-04-07 | `exp/preprocess-ext` | training | Preprocessing extension trial planned for server run | `saved_models/weekly_drone_2026w14/preprocess_ext/`, `result/weekly_drone_2026w14/preprocess_ext/` | planned |
| 2026-04-08 | `exp/branch-trial` | training | New branch trial planned for server run | `saved_models/weekly_drone_2026w14/branch_trial/`, `result/weekly_drone_2026w14/branch_trial/` | planned |

## Tue 2026-04-07
### Local
- [ ] Validate emergency acoustic features:
  - alpha ratio
  - spectral centroid / bandwidth
  - energy distribution
  - pitch / energy envelope
- [ ] Output artifacts:
  - `analysis/cross_language_emergency/alpha_ratio.png`
  - `analysis/cross_language_emergency/spectral_centroid_bandwidth.png`
  - `analysis/cross_language_emergency/energy_distribution.png`
  - `analysis/cross_language_emergency/pitch_energy_envelope.png`
  - `analysis/cross_language_emergency/findings.md`

### Server
- [x] Freeze baseline and launch baseline training (`drone_2026w14`).
- [ ] Output artifacts:
  - `saved_models/weekly_drone_2026w14/baseline/`
  - `result/weekly_drone_2026w14/baseline/`
  - `logs/weekly_drone_2026w14_baseline_*.log`

## Wed 2026-04-08
### Local
- [ ] Complete cross-language analysis summary.
- [ ] Output artifacts:
  - `analysis/cross_language_emergency/cross_language_band_compare.png`
  - `analysis/cross_language_emergency/avg_energy_curves.png`
  - `analysis/cross_language_emergency/summary_2026w14.md`

### Server
- [x] Launch preprocessing extension run.
- [ ] Launch new branch trial run.
- [ ] Output artifacts:
  - `saved_models/weekly_drone_2026w14/preprocess_ext/`
  - `saved_models/weekly_drone_2026w14/branch_trial/`
  - `result/weekly_drone_2026w14/preprocess_ext/`
  - `result/weekly_drone_2026w14/branch_trial/`
  - `logs/weekly_drone_2026w14_preprocess_ext_*.log`
  - `logs/weekly_drone_2026w14_branch_trial_*.log`

## Thu 2026-04-09 (Before Meeting)
### Local
- [ ] Produce decision table for mainline inclusion (baseline vs preprocess_ext vs branch_trial).
- [ ] Prepare short meeting brief and minimal related work update.
- [ ] Output artifacts:
  - `result/weekly_wrapup_2026w14/comparison_main.csv`
  - `result/weekly_wrapup_2026w14/decision_table.md`
  - `result/weekly_wrapup_2026w14/meeting_brief_2026w14.md`
  - `result/weekly_wrapup_2026w14/related_work_delta.md`

## Status Log
- 2026-04-07:
  - Done: Notion checklist updated for `2026/4/9`.
  - Done: repo weekly TODO/runbook/handoff docs aligned to meeting-week delivery plan.
  - Done: baseline checkpoint confirmed in local workspace (`saved_models/weekly_drone_2026w14/baseline/best_embed_kd/student_kd_best.weights.h5`).
  - Done: multi-agent dispatch prompts prepared and handed to user.
  - Done: acoustic agent phase 1.1 receipt received on branch `codex/acoustic-2026w14-phase1` (`a1d79f2e`), with default `surprise_excluded`.
  - Done: model agent command/config pack received for `preprocess_ext` and `branch_trial`.
  - Done: acoustic agent phase 1.2 receipt received on `codex/acoustic-2026w14-phase1` (`b43c429c`); CREMA-D scanned counts now non-zero, ESD still pending license-gated import.
  - Done: server `preprocess_ext` startup receipt received (PID + LOG + first 30 lines; GPU visible).
  - Done: meeting wrap-up templates initialized under `result/weekly_wrapup_2026w14/`.
  - Next: wait for `preprocess_ext` completion receipt, then trigger/track `branch_trial` startup and completion receipts.
