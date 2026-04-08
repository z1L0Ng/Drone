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

## 7) Local Real-World Validation (Standardized)

Purpose:
- Validate weekly selected models on local manually collected `testset/`.
- Run both "inference-only" and "finetune+inference" to estimate real-world transfer.

### 7.1 Inference-only on local testset

```bash
# Baseline
python scripts/eval_logmel_kd_checkpoint.py \
  --weights saved_models/weekly_drone_2026w14/baseline/best_embed_kd/student_kd_best.weights.h5 \
  --encoder saved_models/label_encoder.joblib \
  --testset testset \
  --output-dir result/weekly_wrapup_2026w14/local_realworld_eval/baseline \
  --model-profile base \
  --run-id drone_2026w14_local_realworld_eval \
  --exp-id baseline_realworld \
  --kd-variant embed_only \
  --aug-flag true \
  --prewarm-flag false \
  --link-best-model

# preprocess_ext
python scripts/eval_logmel_kd_checkpoint.py \
  --weights saved_models/weekly_drone_2026w14/preprocess_ext/student_kd_best.weights.h5 \
  --encoder saved_models/label_encoder.joblib \
  --testset testset \
  --output-dir result/weekly_wrapup_2026w14/local_realworld_eval/preprocess_ext \
  --model-profile base \
  --run-id drone_2026w14_local_realworld_eval \
  --exp-id preprocess_ext_realworld \
  --kd-variant embed_only \
  --aug-flag true \
  --prewarm-flag false \
  --link-best-model

# branch_trial
python scripts/eval_logmel_kd_checkpoint.py \
  --weights saved_models/weekly_drone_2026w14/branch_trial/student_kd_best.weights.h5 \
  --encoder saved_models/label_encoder.joblib \
  --testset testset \
  --output-dir result/weekly_wrapup_2026w14/local_realworld_eval/branch_trial \
  --model-profile base \
  --run-id drone_2026w14_local_realworld_eval \
  --exp-id branch_trial_realworld \
  --kd-variant ce_logits \
  --aug-flag true \
  --prewarm-flag false \
  --link-best-model
```

### 7.2 Finetune+inference on local testset

Use the same split cache across models for fair comparison:

```bash
SPLIT_CACHE=result/weekly_wrapup_2026w14/local_realworld_finetune/split_indices_testset.npz

# Baseline
python scripts/run_finetune_logmel_kd.py \
  --testset testset \
  --encoder saved_models/label_encoder.joblib \
  --weights saved_models/weekly_drone_2026w14/baseline/best_embed_kd/student_kd_best.weights.h5 \
  --finetuned-weights saved_models/weekly_drone_2026w14/baseline/best_embed_kd/finetuned_local_testset_best.weights.h5 \
  --output result/weekly_wrapup_2026w14/local_realworld_finetune/baseline \
  --split-cache "${SPLIT_CACHE}" \
  --finetune-ratio 0.3 \
  --val-ratio 0.1 \
  --epochs 10 \
  --batch-size 32 \
  --lr 1e-5 \
  --seed 42

# preprocess_ext
python scripts/run_finetune_logmel_kd.py \
  --testset testset \
  --encoder saved_models/label_encoder.joblib \
  --weights saved_models/weekly_drone_2026w14/preprocess_ext/student_kd_best.weights.h5 \
  --finetuned-weights saved_models/weekly_drone_2026w14/preprocess_ext/finetuned_local_testset_best.weights.h5 \
  --output result/weekly_wrapup_2026w14/local_realworld_finetune/preprocess_ext \
  --split-cache "${SPLIT_CACHE}" \
  --finetune-ratio 0.3 \
  --val-ratio 0.1 \
  --epochs 10 \
  --batch-size 32 \
  --lr 1e-5 \
  --seed 42

# branch_trial
python scripts/run_finetune_logmel_kd.py \
  --testset testset \
  --encoder saved_models/label_encoder.joblib \
  --weights saved_models/weekly_drone_2026w14/branch_trial/student_kd_best.weights.h5 \
  --finetuned-weights saved_models/weekly_drone_2026w14/branch_trial/finetuned_local_testset_best.weights.h5 \
  --output result/weekly_wrapup_2026w14/local_realworld_finetune/branch_trial \
  --split-cache "${SPLIT_CACHE}" \
  --finetune-ratio 0.3 \
  --val-ratio 0.1 \
  --epochs 10 \
  --batch-size 32 \
  --lr 1e-5 \
  --seed 42
```

### 7.3 Required outputs
- `result/weekly_wrapup_2026w14/local_realworld_eval/*/metrics.json`
- `result/weekly_wrapup_2026w14/local_realworld_eval/*/classification_report.txt`
- `result/weekly_wrapup_2026w14/local_realworld_finetune/*/summary.csv`
- `result/weekly_wrapup_2026w14/local_realworld_finetune/*/finetuned/classification_report.txt`

### 7.4 Decision usage
- Compare "inference-only" vs "finetuned" deltas on real-world testset.
- Keep this stage as default weekly post-server validation before next-language expansion.
