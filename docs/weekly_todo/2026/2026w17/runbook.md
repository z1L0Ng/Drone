# Weekly Runbook (Drone 2026w17)

Project target: SenSys 2027 first-round submission.

Cadence: Thursday noon planning/meeting cycle.

## 0) Role Boundaries
- Manager agent: planning, dispatch, acceptance, documentation, and reporting only.
- Deployment agent: export, ESP32/XIAO flashing, board logs, and deployability verdict.
- Writing agent: local `docs/paper_sensys2027/` drafting after deployment evidence is available.
- Training: server by default. W17 local training was an exception because server resources were occupied.

## 1) Current Anchors
- Mainline model anchor: `w14 preprocess_ext`
- Deployment candidate: `xiao_bottleneck256_tflm / B_small_teacher_student`
- Candidate evidence log:
  - `logs/weekly_drone_2026w17_B_small_teacher_student_resume_20260429_030603.log`
- Local testset summaries:
  - `result/weekly_wrapup_2026w17/B_small_teacher_student_testset_eval/summary.md`
  - `result/weekly_wrapup_2026w17/B_small_teacher_student_finetuned_testset_eval/summary.md`

## 2) Artifact Integrity Gate
Commit/code status:

- Local `HEAD`: `6698cd389f5d4849ba8c456152927f3f39dc70ff`
- This commit contains the necessary `src/train_logmel_kd.py` callback-mode fix
  for Keras monitor handling and the current SenSys draft updates.
- This commit does not contain the `B_small_teacher_student` checkpoint/result
  tree. Those runtime artifacts still need to be restored or regenerated before
  deployment.

Run before deployment dispatch:

```bash
ls -la saved_models/weekly_drone_2026w17/B_small_teacher_student
ls -la weeklyresult/weekly_drone_2026w17/B_small_teacher_student
tail -n 50 logs/weekly_drone_2026w17_B_small_teacher_student_resume_20260429_030603.log
```

Required files:
- `saved_models/weekly_drone_2026w17/B_small_teacher_student/student_kd_best.weights.h5`
- `saved_models/weekly_drone_2026w17/B_small_teacher_student/teacher_clean_best.weights.h5`
- `weeklyresult/weekly_drone_2026w17/B_small_teacher_student/run_config.json`
- `weeklyresult/weekly_drone_2026w17/B_small_teacher_student/classification_report_noisy.txt`
- `weeklyresult/weekly_drone_2026w17/B_small_teacher_student/history/student_history.csv`

If any required file is missing, recover artifacts before deployment. Do not
start board work from summary files alone.

## 3) Deployment Agent Dispatch
Use this once the artifact integrity gate passes:

```text
You are the Drone deployment agent.

Scope:
- Do not retrain models.
- Use the W17 deployment candidate:
  saved_models/weekly_drone_2026w17/B_small_teacher_student/student_kd_best.weights.h5
- Profile is xiao_bottleneck256_tflm. The required TFLite op mix must include DEPTHWISE_CONV_2D=1 and must not reintroduce grouped temporal CONV_2D.

Inputs:
- Training log: logs/weekly_drone_2026w17_B_small_teacher_student_resume_20260429_030603.log
- Result root: weeklyresult/weekly_drone_2026w17/B_small_teacher_student/
- Handoff doc: docs/realworld_esp32_tflm_profile_handoff.md

Required outputs:
- full-int TFLite export path
- op-list report
- esp32_tflm_candidate_test package path
- XIAO boot/serial log showing AllocateTensors() result
- XIAO Invoke() result
- top_label output
- concise go/no-go note with blocker if failed

Acceptance:
- Export must prove DEPTHWISE_CONV_2D=1.
- Board must pass AllocateTensors() and Invoke().
- No deployability claim until top_label is printed.
```

## 4) Writing Agent Dispatch
Use this after the first deployment verdict or blocker:

```text
You are the Drone writing agent for the SenSys 2027 first-round target.

Scope:
- Work in docs/paper_sensys2027/ only.
- Do not edit model code or deployment firmware.
- Keep the drone/UAV voice safety layer as the core story.

Evidence rules:
- w14 preprocess_ext remains the reproducible mainline anchor.
- xiao_bottleneck256_tflm / B_small_teacher_student is a deployment candidate, not a proven deployed system unless the XIAO gate passes.
- Do not overclaim; write deployment as measured evidence plus remaining blocker if the board gate is incomplete.

First task:
- Update the writing outline and evaluation/deployment story so the paper target is explicitly SenSys 2027 first round and the next milestone is deployability evidence.
```

## 5) Notion Sync Checklist
- Add W17 status to the `2026/4/30` Thursday weekly page.
- Do not put W17 content on `2026/4/23`; that page belongs to the previous Thursday-cycle meeting.
- Mark local training exception as done, with log path.
- Add artifact integrity as a blocker.
- Add deployment agent as next owner after artifact recovery.
- Add writing pivot as next stage after deployment evidence.
