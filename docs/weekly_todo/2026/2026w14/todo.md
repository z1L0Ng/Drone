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
- [x] Collect acoustic agent phase2 first-batch outputs (`b1eed215`): `phase2_multilingual_plan_2026w14.md`, `phase2_multilingual_dataset_manifest_2026w14.csv`, `phase2_mapping_audit_2026w14.md`.
- [x] Collect acoustic agent lexical A4 outputs (`7b6b25c3`): `phase2_lexical_inventory_2026w14.csv`, `phase2_lexical_alignment_2026w14.md`, `phase2_lexical_coverage_summary_2026w14.md`.
- [x] Collect acoustic agent lexical-first A5 outputs (`af904615`): `phase2_lexical_first_dataset_pool_2026w14.csv`, `phase2_lexical_go_no_go_2026w14.md`, `phase2_lexical_target_top2_2026w14.md`.
- [x] Collect acoustic agent transcript-unblock A6 outputs (`a1d686de`): `phase2_transcript_capable_candidates_2026w14.csv`, `phase2_transcript_access_plan_2026w14.md`, `phase2_lexical_unblock_top2_2026w14.md`.
- [x] Lock expansion policy: English gate first, then multilingual expansion with open datasets (not limited to Chinese/Japanese; French etc. allowed if sample size and semantic mapping are sufficient).
- [x] Collect model agent command pack for `preprocess_ext` and `branch_trial`.
- [x] Receive server startup and completion receipts for both runs (evidenced by synced `weeklyresult` package).
- [x] Receive server `preprocess_ext` startup receipt (PID/LOG/first 30 lines; GPU visible).
- [x] Receive server model checkpoints for both runs (partial server sync, no `result/log` evidence yet).
- [x] Receive server-side result reports for all three candidates under `weeklyresult/weekly_drone_2026w14/*`.
- [x] Keep Notion checklist and repo docs synchronized after each receipt.
- [x] Coordination reference doc:
  - `docs/weekly_todo/2026/2026w14/agent_management_playbook.md`
- [x] Dispatch prompt pack prepared:
  - `docs/weekly_todo/2026/2026w14/dispatch_prompts.md`
- [x] Post-meeting phase2 acoustic prompt prepared (`Prompt A3`):
  - `docs/weekly_todo/2026/2026w14/dispatch_prompts.md`
- [x] Lexical inventory/alignment acoustic prompt prepared (`Prompt A4`):
  - `docs/weekly_todo/2026/2026w14/dispatch_prompts.md`
- [x] Lexical-first expansion acoustic prompt prepared (`Prompt A5`):
  - `docs/weekly_todo/2026/2026w14/dispatch_prompts.md`
- [x] Transcript-unblock sourcing prompt prepared (`Prompt A6`):
  - `docs/weekly_todo/2026/2026w14/dispatch_prompts.md`
- [x] Top2 lexical-ready execution prompt prepared (`Prompt A7`):
  - `docs/weekly_todo/2026/2026w14/dispatch_prompts.md`
- [x] Meeting evidence tracked snapshot created under docs (git-tracked mirror):
  - `docs/weekly_todo/2026/2026w14/meeting_artifacts_snapshot_20260408.md`

## Branch / Model / Training Changes (This Week)
| Date | Branch | Type | Change | Paths | Status |
|---|---|---|---|---|---|
| 2026-04-07 | `main` | planning | Lock meeting-week execution plan and checkpoints/report paths | `docs/weekly_todo/2026/2026w14/`, `docs/weekly_todo/handoff_log.md` | done |
| 2026-04-07 | `main` | coordination | Multi-agent management playbook and handoff protocol activated | `docs/weekly_todo/2026/2026w14/agent_management_playbook.md` | done |
| 2026-04-07 | `exp/preprocess-ext` | training | Preprocessing extension trial completed on server and synced locally | `saved_models/weekly_drone_2026w14/preprocess_ext/`, `weeklyresult/weekly_drone_2026w14/preprocess_ext/` | done |
| 2026-04-08 | `exp/branch-trial` | training | New branch trial completed on server and synced locally | `saved_models/weekly_drone_2026w14/branch_trial/`, `weeklyresult/weekly_drone_2026w14/branch_trial/` | done |

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
- [x] Output artifacts:
  - `saved_models/weekly_drone_2026w14/baseline/`
  - `weeklyresult/weekly_drone_2026w14/baseline/`
  - `logs/weekly_drone_2026w14_baseline_*.log` (log backfill waived this week; `weeklyresult` accepted as evidence)

## Wed 2026-04-08
### Local
- [x] Complete cross-language analysis summary (delivered on `origin/codex/acoustic-2026w14-phase1` up to `25deca41`).
- [x] Complete phase1 English meeting-ready summary package on acoustic branch (`6310b365`): evidence table + onepager + surprise-zero diagnosis.
- [x] Dispatch phase2 multilingual candidate-matrix task to acoustic agent (license/sample-size/semantic-alignment gated).
- [x] Freeze acoustic dispatch scope after phase1.6; no further acoustic tasks until server training receipts arrive.
- [x] Run local real-world inference on `testset/` for baseline/preprocess_ext/branch_trial.
- [x] Run local real-world finetune validation on `testset/` with unified split cache.
- [x] Output artifacts:
  - `analysis/cross_language_emergency/summary_2026w14_phase1.md` (acoustic branch)
  - `analysis/cross_language_emergency/multilingual_candidate_matrix_2026w14.md` (acoustic branch `46f9b06e`)
  - `analysis/cross_language_emergency/multilingual_priority_scorecard_2026w14.md` (acoustic branch `25deca41`)
  - `analysis/cross_language_emergency/multilingual_mapping_contract_2026w14.md` (acoustic branch `25deca41`)
  - `result/weekly_wrapup_2026w14/local_realworld_eval/*`
  - `result/weekly_wrapup_2026w14/local_realworld_finetune/*`

### Server
- [x] Launch preprocessing extension run.
- [x] Launch new branch trial run.
- [x] Output artifacts (synced under `weeklyresult/weekly_drone_2026w14/*`):
  - `saved_models/weekly_drone_2026w14/preprocess_ext/`
  - `saved_models/weekly_drone_2026w14/branch_trial/`
  - `weeklyresult/weekly_drone_2026w14/preprocess_ext/`
  - `weeklyresult/weekly_drone_2026w14/branch_trial/`
- [x] Log copy waiver accepted by PI: reports/history in `weeklyresult` are used as completion evidence; no extra log backfill required.

## Thu 2026-04-09 (Before Meeting)
### Local
- [x] Produce decision table for mainline inclusion (baseline vs preprocess_ext vs branch_trial).
- [x] Prepare short meeting brief and minimal related work update.
- [x] Output artifacts:
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
  - Done: weekly results synced under `weeklyresult/weekly_drone_2026w14/*` with `run_config.json`, `classification_report_noisy.txt`, and `student_history.csv` for baseline/preprocess_ext/branch_trial.
  - Done: model comparison updated (`preprocess_ext` best, `branch_trial` regression).
  - Done: PI confirmed no extra log backfill needed when `weeklyresult` evidence is complete.
  - Done: meeting recommendation finalized as `preprocess_ext=adopt`, `branch_trial=defer`.
  - Done: local real-world gate executed on `testset/` (inference + finetune with shared split cache) and written to `result/weekly_wrapup_2026w14/local_realworld_*`.
  - Done: meeting wrap-up artifacts finalized with local gate metrics (`comparison_main.csv`, `decision_table.md`, `meeting_brief_2026w14.md`, `related_work_delta.md`).
  - Done: post-meeting phase2 dispatch prompt (`Prompt A3`) added for acoustic agent with language priority and mapping constraints.
  - Done: acoustic agent returned phase2 first-batch outputs on `codex/acoustic-2026w14-phase1` (`b1eed215`), with strict pool `Italian/German/French` and bridge pool `Chinese/Portuguese`.
  - Done: lexical inventory dispatch prompt (`Prompt A4`) added to require explicit word/utterance-level corpus visibility and cross-lingual gloss alignment.
  - Done: acoustic agent returned lexical A4 outputs on `codex/acoustic-2026w14-phase1` (`7b6b25c3`), confirming lexical-level claim is currently blocked by multilingual transcript coverage.
  - Done: lexical-first expansion prompt (`Prompt A5`) added to prioritize transcript-capable datasets before further multilingual comparison.
  - Done: acoustic agent returned lexical-first A5 outputs on `codex/acoustic-2026w14-phase1` (`af904615`): current pool remains all `hold`; top2 target order preserved as Italian/German with French fallback.
  - Done: acoustic agent returned transcript-unblock A6 outputs on `codex/acoustic-2026w14-phase1` (`a1d686de`): lexical-ready `go` languages identified as Quechua + Polish; fallback Italian.
  - Done: pushed acoustic branch to remote (`origin/codex/acoustic-2026w14-phase1`) for traceability.
  - Done: transcript-unblock sourcing prompt (`Prompt A6`) added to find transcript-capable multilingual datasets.
  - Done: top2 lexical-ready execution prompt (`Prompt A7`) added for Quechua/Polish execution pack.
  - Done: created git-tracked meeting artifact snapshot under `docs/weekly_todo/2026/2026w14/meeting_artifacts_snapshot_20260408.md`.
  - Next: dispatch `Prompt A7` and collect top2 lexical manifest + gloss clusters + evaluation runbook.
