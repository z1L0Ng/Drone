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
- [x] Collect acoustic agent phase-1.3 feature evidence package on `origin/codex/acoustic-2026w14-phase1` (`2bd80e50`).
- [x] Collect acoustic agent phase-1.4 meeting evidence package (`6310b365`) with evidence table + surprise-zero diagnosis + onepager.
- [x] Collect acoustic agent phase-1.5 refresh (`46f9b06e`): English gate pass confirmed, multilingual candidate matrix delivered.
- [x] Collect acoustic agent phase-1.6 decision-support docs (`25deca41`): multilingual priority scorecard + mapping contract.
- [x] Lock expansion policy: English gate first, then multilingual expansion with open datasets (not limited to Chinese/Japanese; French etc. allowed if sample size and semantic mapping are sufficient).
- [x] Collect model agent command pack for `preprocess_ext` and `branch_trial`.
- [ ] Receive server startup and completion receipts for both runs.
- [x] Receive server `preprocess_ext` startup receipt (PID/LOG/first 30 lines; GPU visible).
- [x] Receive server model checkpoints for both runs (partial server sync, no `result/log` evidence yet).
- [x] Keep Notion checklist and repo docs synchronized after each receipt.
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
- [x] Validate emergency acoustic features (delivered on acoustic branch `2bd80e50`, pending merge to `main`):
  - alpha ratio
  - spectral centroid / bandwidth
  - energy distribution
  - pitch / energy envelope
- [x] Output artifacts (on `origin/codex/acoustic-2026w14-phase1`):
  - `analysis/cross_language_emergency/alpha_ratio.png`
  - `analysis/cross_language_emergency/spectral_centroid_bandwidth.png`
  - `analysis/cross_language_emergency/energy_distribution.png`
  - `analysis/cross_language_emergency/pitch_energy_envelope.png`
  - `analysis/cross_language_emergency/findings_phase1_cremad.md`
  - `analysis/cross_language_emergency/findings_phase1_sensitivity.md`
  - `analysis/cross_language_emergency/summary_2026w14_phase1.md`

### Server
- [x] Freeze baseline and launch baseline training (`drone_2026w14`).
- [ ] Output artifacts:
  - `saved_models/weekly_drone_2026w14/baseline/`
  - `result/weekly_drone_2026w14/baseline/`
  - `logs/weekly_drone_2026w14_baseline_*.log`

## Wed 2026-04-08
### Local
- [ ] Complete cross-language analysis summary.
- [x] Complete phase1 English meeting-ready summary package on acoustic branch (`6310b365`): evidence table + onepager + surprise-zero diagnosis.
- [x] Dispatch phase2 multilingual candidate-matrix task to acoustic agent (license/sample-size/semantic-alignment gated).
- [x] Freeze acoustic dispatch scope after phase1.6; no further acoustic tasks until server training receipts arrive.
- [ ] Output artifacts:
  - `analysis/cross_language_emergency/cross_language_band_compare.png`
  - `analysis/cross_language_emergency/avg_energy_curves.png`
  - `analysis/cross_language_emergency/summary_2026w14.md`
  - `analysis/cross_language_emergency/multilingual_candidate_matrix_2026w14.md` (delivered on acoustic branch `46f9b06e`)
  - `analysis/cross_language_emergency/multilingual_priority_scorecard_2026w14.md` (delivered on acoustic branch `25deca41`)
  - `analysis/cross_language_emergency/multilingual_mapping_contract_2026w14.md` (delivered on acoustic branch `25deca41`)

### Server
- [x] Launch preprocessing extension run.
- [x] Launch new branch trial run.
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
  - Done: acoustic agent phase 1.3 receipt received on `codex/acoustic-2026w14-phase1` (`2bd80e50`) with CREMA-D feature figures, findings, and ESD ingestion/rescan SOP.
  - Done: acoustic agent phase 1.4 receipt received on `codex/acoustic-2026w14-phase1` (`6310b365`) with meeting evidence table and surprise-zero diagnosis.
  - Done: acoustic agent phase 1.5 receipt received on `codex/acoustic-2026w14-phase1` (`46f9b06e`): English gate remains positive (`6/6` features `|d|>=0.35`), refreshed sample counts (`emergency=2539`, `normal=1086`), multilingual candidate matrix added with priority `Italian/German`, then `French`.
  - Done: acoustic agent phase 1.6 receipt received on `codex/acoustic-2026w14-phase1` (`25deca41`) with multilingual priority scorecard + mapping contract, enabling direct post-server language-selection decisions.
  - Done: phase2 language policy locked by PI: after English gate, expand multilingual set beyond Chinese/Japanese when open datasets have enough samples and emergency/normal semantics can align to English reference.
  - Done: server `preprocess_ext` startup receipt received (PID + LOG + first 30 lines; GPU visible).
  - Done: meeting wrap-up templates initialized under `result/weekly_wrapup_2026w14/`.
  - Next: wait for `preprocess_ext` completion receipt, then track `branch_trial` startup/completion receipts; no additional acoustic dispatch before server-side evidence lands.
- 2026-04-08:
  - Done: local sync includes server checkpoints for `preprocess_ext` and `branch_trial` under `saved_models/weekly_drone_2026w14/*`.
  - Blocker: `result/weekly_drone_2026w14/*` and `logs/weekly_drone_2026w14_*.log` are still absent in current local repo path.
  - Next: request server-side completion evidence pack (result tree + key files + log tails) before finalizing `decision_table.md` adopt/defer.
