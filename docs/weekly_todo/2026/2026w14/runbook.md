# Weekly Runbook (Drone 2026w14)

## 0) Coordination Rule

- Manager agent: planning, documentation, and acceptance only.
- Acoustic agent: dataset and acoustic feature analysis only.
- Model agent: model/config branch work only.
- Server operator: training execution only.
- Reference: `docs/weekly_todo/2026/2026w14/agent_management_playbook.md`

## 1) Server Training

```bash
# all default weekly stages
WEEKLY_TAG=drone_2026w14 bash scripts/run_weekly_server_train.sh all
```

Optional staged execution:

```bash
# baseline freeze run
WEEKLY_TAG=drone_2026w14 bash scripts/run_weekly_server_train.sh baseline

# existing ablation/prewarm/logits bundles
WEEKLY_TAG=drone_2026w14 bash scripts/run_weekly_server_train.sh ablation
WEEKLY_TAG=drone_2026w14 bash scripts/run_weekly_server_train.sh prewarm
WEEKLY_TAG=drone_2026w14 bash scripts/run_weekly_server_train.sh logits
```

## 2) Server Templates For This Week

Preprocessing extension template (`preprocess_ext`):

```bash
WEEKLY_TAG=drone_2026w14 \
KD_DISTILL_VARIANT=embed_only \
KD_STUDENT_ENABLE_PROSODY_AUG=1 \
KD_MODEL_DIR=saved_models/weekly_drone_2026w14/preprocess_ext \
KD_RESULT_DIR=result/weekly_drone_2026w14/preprocess_ext \
KD_HISTORY_DIR=result/weekly_drone_2026w14/preprocess_ext/history \
KD_TEACHER_CKPT=saved_models/weekly_drone_2026w14/baseline/teacher_clean_best.weights.h5 \
KD_STUDENT_CKPT=saved_models/weekly_drone_2026w14/preprocess_ext/student_kd_best.weights.h5 \
python src/train_logmel_kd.py | tee logs/weekly_drone_2026w14_preprocess_ext_$(date +"%Y%m%d_%H%M%S").log
```

Branch trial template (`branch_trial`):

```bash
WEEKLY_TAG=drone_2026w14 \
KD_DISTILL_VARIANT=ce_logits \
KD_ALPHA_CE=1.0 \
KD_LOGITS_BETA=1.0 \
KD_STUDENT_ENABLE_PROSODY_AUG=1 \
KD_MODEL_DIR=saved_models/weekly_drone_2026w14/branch_trial \
KD_RESULT_DIR=result/weekly_drone_2026w14/branch_trial \
KD_HISTORY_DIR=result/weekly_drone_2026w14/branch_trial/history \
KD_TEACHER_CKPT=saved_models/weekly_drone_2026w14/baseline/teacher_clean_best.weights.h5 \
KD_STUDENT_CKPT=saved_models/weekly_drone_2026w14/branch_trial/student_kd_best.weights.h5 \
python src/train_logmel_kd.py | tee logs/weekly_drone_2026w14_branch_trial_$(date +"%Y%m%d_%H%M%S").log
```

## 3) Server Execution Policy

1. Default orchestration is serial:
   - `preprocess_ext` first
   - `branch_trial` second
2. Parallel run is allowed only if server resource headroom is confirmed.
3. For each run, server operator must return:
   - startup receipt within 10 minutes: PID + LOG + first 30 lines
   - completion receipt: checkpoint path + result tree + last 50 lines

## 4) Local Evaluation + Summaries

```bash
WEEKLY_TAG=drone_2026w14 bash scripts/run_weekly_local_eval.sh
```

For custom experiment checkpoints:

```bash
WEEKLY_TAG=drone_2026w14 \
BASELINE_CKPT=saved_models/weekly_drone_2026w14/baseline/best_embed_kd/student_kd_best.weights.h5 \
bash scripts/run_weekly_local_eval.sh
```

## 5) Weekly Wrap-up (Local)

```bash
conda run -n drone python scripts/run_weekly_wrapup_local.py
```

## 6) Handoff Steps
1. Update `docs/weekly_todo/2026/2026w14/todo.md`.
2. Append a row to `docs/weekly_todo/handoff_log.md`.
3. Record exact command + output path + next owner/action.
