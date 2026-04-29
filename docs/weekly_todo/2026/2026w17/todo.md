# Weekly TODO (CDT, Thursday-cycle 2026w17)

Meeting checkpoint: Thursday 2026-04-30 noon CDT.

Planning cycle: Thursday 2026-04-23 noon -> Thursday 2026-04-30 noon.

Project target: SenSys 2027 first-round submission.

## Weekly Goal
- Close W17 around a reproducible deployment candidate, not a new model-search loop.
- Treat `w14 preprocess_ext` as the mainline model anchor.
- Treat `xiao_bottleneck256_tflm / B_small_teacher_student` as the deployment candidate to hand to the deployment agent.
- Prepare the transition from deployment validation to SenSys 2027 writing.

## Hard Constraints
- Manager agent scope: planning, dispatch, acceptance, documentation, and reporting only.
- Default training policy remains server-only, but W17 has one documented local-training exception because server resources were occupied.
- Local scope: code checks, evaluation, artifact audit, deployment handoff, and writing docs.
- Server scope: future full-dataset training only when explicitly approved and dispatched with commit SHA + tmux + `weeklyresult/`.
- Do not claim deployability until the XIAO gate passes: full-int export, op-list check, `AllocateTensors()`, `Invoke()`, and `top_label`.
- Do not replace the mainline `w14 preprocess_ext` conclusion with the compressed candidate without a documented comparison.

## Current Evidence Snapshot
- Git audit at update time:
  - branch: `main`
  - HEAD: `6698cd389f5d4849ba8c456152927f3f39dc70ff`
  - status: clean except `main` is ahead of `origin/main` by 1 commit
- Local training exception:
  - reason: server resources occupied
  - run: `weekly_drone_2026w17/B_small_teacher_student`
  - log: `logs/weekly_drone_2026w17_B_small_teacher_student_resume_20260429_030603.log`
  - teacher profile: `xiao_bottleneck256_tflm`
  - student profile: `xiao_bottleneck256_tflm`
  - params: teacher `712,067`, student `712,067`
  - stats branches: disabled for teacher and student
  - best visible validation accuracy in resume log: `0.8635`
  - clean test accuracy: `0.8862`
  - noisy test accuracy at SNR `-10 dB`: `0.8728`
- Local testset gate evidence:
  - `result/weekly_wrapup_2026w17/B_small_teacher_student_testset_eval/summary.md`
  - original local testset: overall acc `0.6990`, emergency recall `0.6319`, emergency F1 `0.5698`
  - `result/weekly_wrapup_2026w17/B_small_teacher_student_finetuned_testset_eval/summary.md`
  - finetuned local testset: overall acc `0.7201`, emergency recall `0.6482`, emergency F1 `0.5940`
- Mainline anchor comparison:
  - `w14 preprocess_ext` original local testset: overall acc `0.6934`, emergency recall `0.3127`, emergency F1 `0.4111`
  - `w14 preprocess_ext` finetuned local testset: overall acc `0.8382`, emergency recall `0.7394`, emergency F1 `0.7394`
- Artifact integrity note:
  - The resume log reports saved outputs under `saved_models/weekly_drone_2026w17/B_small_teacher_student/` and `weeklyresult/weekly_drone_2026w17/B_small_teacher_student/`.
  - At manager audit time on 2026-04-29, those two expected directories were not present in this working tree.
  - Commit `6698cd389f5d4849ba8c456152927f3f39dc70ff` is local `HEAD` and contains the required training-script callback-mode fix plus paper draft updates, but it does not contain the `B_small_teacher_student` checkpoint/result tree.
  - Deployment handoff is blocked until checkpoint and `weeklyresult` files are restored or explicitly regenerated.

## Daily Execution Checklist
- [x] Audit git branch, HEAD, and status before updating management docs.
- [x] Audit latest `weeklyresult/` week and W17 local logs.
- [x] Update W17 weekly TODO and runbook.
- [x] Append W17 row to `docs/weekly_todo/handoff_log.md`.
- [ ] Restore or confirm `B_small_teacher_student` checkpoint and `weeklyresult` artifact tree.
- [x] Sync Notion weekly page with W17 status and next-stage owners.
- [ ] Dispatch deployment agent after artifact integrity gate is satisfied.
- [ ] Dispatch writing plan after deployment gate has a first result or a clearly documented blocker.

## Branch / Model / Training Changes
| Date | Branch | Type | Change | Paths | Status |
|---|---|---|---|---|---|
| 2026-04-29 | `main` | management | Create W17 Thursday-cycle management log and SenSys 2027 first-round target | `docs/weekly_todo/2026/2026w17/`, `docs/technical_spec/server_local_sync_protocol.md` | done |
| 2026-04-29 | `main` | training receipt | Record local-training exception for `B_small_teacher_student` after server resource conflict | `logs/weekly_drone_2026w17_B_small_teacher_student_resume_20260429_030603.log`, `result/weekly_wrapup_2026w17/B_small_teacher_student_*` | done |
| 2026-04-29 | `main` | deployment handoff | Promote `xiao_bottleneck256_tflm / B_small_teacher_student` to deployment-agent candidate, with artifact integrity gate | `docs/realworld_esp32_tflm_profile_handoff.md` | in-progress |
| 2026-04-29 | `main` | writing handoff | Prepare SenSys 2027 first-round writing pivot after deployment gate | `docs/paper_sensys2027/` | planned |

## Priority Items
### Priority 1: Deployment Candidate Integrity
- [ ] Confirm the expected checkpoint exists:
  - `saved_models/weekly_drone_2026w17/B_small_teacher_student/student_kd_best.weights.h5`
  - `saved_models/weekly_drone_2026w17/B_small_teacher_student/teacher_clean_best.weights.h5`
- [ ] Confirm the expected result tree exists:
  - `weeklyresult/weekly_drone_2026w17/B_small_teacher_student/run_config.json`
  - `weeklyresult/weekly_drone_2026w17/B_small_teacher_student/classification_report_noisy.txt`
  - `weeklyresult/weekly_drone_2026w17/B_small_teacher_student/history/student_history.csv`
- [ ] If artifacts are missing, recover them before deployment. Do not dispatch board work from metric summaries alone.

### Priority 2: Deployment Agent Handoff
- [ ] Hand deployment agent the recovered `B_small_teacher_student` checkpoint.
- [ ] Required deployment outputs:
  - full-integer TFLite export path
  - op list proving `DEPTHWISE_CONV_2D=1`
  - XIAO log for `AllocateTensors()`
  - XIAO log for `Invoke()`
  - printed `top_label`
- [ ] Stop if the export op mix regresses to grouped `CONV_2D`.

### Priority 3: Writing Pivot
- [ ] Update SenSys 2027 first-round writing plan after deployment result is known.
- [ ] Use conservative language: `w14 preprocess_ext` remains the reproducible mainline result; the TFLM candidate is a deployment path until board evidence lands.
- [ ] Keep writing in `docs/paper_sensys2027/`; Overleaf sync is later.

## Status Log
- 2026-04-29:
  - Done: audited W17 local logs and results.
  - Done: documented that `B_small_teacher_student` was completed locally due to server resource contention.
  - Done: recorded `xiao_bottleneck256_tflm` same-profile teacher/student metrics from the resume log.
  - Done: recorded local testset summaries for original and finetuned `B_small_teacher_student`.
  - Done: corrected Notion mapping so W17 content is on the `2026/4/30` meeting page, not `2026/4/23`.
  - Done: confirmed `6698cd389f5d4849ba8c456152927f3f39dc70ff` is present as local `HEAD`; its necessary code/paper contents are already in the working tree.
  - Blocker: expected checkpoint/result directories for `B_small_teacher_student` are not present in the current working tree despite being referenced by logs and eval summaries.
  - Next: recover artifacts, then dispatch deployment agent; after first deployment evidence, pivot writing toward SenSys 2027 first-round narrative.
