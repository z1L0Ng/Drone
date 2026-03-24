#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

WEEKLY_TAG="${WEEKLY_TAG:-drone_2026w13}"
RUN_ID="${RUN_ID:-${WEEKLY_TAG}_local_eval}"
TESTSET_DIR="${TESTSET_DIR:-testset}"
ENCODER_PATH="${ENCODER_PATH:-saved_models/label_encoder.joblib}"
MODEL_PROFILE="${MODEL_PROFILE:-base}"

MODEL_ROOT="${WEEKLY_MODEL_ROOT:-${ROOT_DIR}/saved_models/weekly_${WEEKLY_TAG}}"
RESULT_ROOT="${WEEKLY_RESULT_ROOT:-${ROOT_DIR}/result/weekly_${WEEKLY_TAG}}"

mkdir -p \
  experiments/best_embed_kd \
  experiments/ablation_embed_vs_aug/exp_A \
  experiments/ablation_embed_vs_aug/exp_B \
  experiments/ablation_embed_vs_aug/exp_C \
  experiments/ablation_embed_vs_aug/exp_D \
  experiments/prewarm_curriculum/direct_noisy \
  experiments/prewarm_curriculum/prewarm_clean_then_noisy \
  experiments/prewarm_curriculum/noise_fadein_optional \
  experiments/logits_kd_recheck/logits_only \
  experiments/logits_kd_recheck/ce_plus_logits \
  experiments/logits_kd_recheck/embed_only_reference

run_eval() {
  local ckpt="$1"
  local out_dir="$2"
  local exp_id="$3"
  local kd_variant="$4"
  local aug_flag="$5"
  local prewarm_flag="$6"

  if [[ ! -f "${ckpt}" ]]; then
    echo "[WARN] missing checkpoint: ${ckpt}"
    return 1
  fi

  python scripts/eval_logmel_kd_checkpoint.py \
    --weights "${ckpt}" \
    --encoder "${ENCODER_PATH}" \
    --testset "${TESTSET_DIR}" \
    --output-dir "${out_dir}" \
    --model-profile "${MODEL_PROFILE}" \
    --run-id "${RUN_ID}" \
    --exp-id "${exp_id}" \
    --kd-variant "${kd_variant}" \
    --aug-flag "${aug_flag}" \
    --prewarm-flag "${prewarm_flag}" \
    --link-best-model
}

# ----------------------------
# Priority 1: baseline
# ----------------------------
BASELINE_CKPT="${BASELINE_CKPT:-${MODEL_ROOT}/baseline/best_embed_kd/student_kd_best.weights.h5}"
cat > experiments/best_embed_kd/config.yaml <<CFG
weekly_tag: ${WEEKLY_TAG}
run_id: ${RUN_ID}
model_profile: ${MODEL_PROFILE}
checkpoint: ${BASELINE_CKPT}
teacher_student: clean_teacher_noisy_student
distillation: embed_only
augmentation: emergency_pitch_volume_on
selection_rule: overall_acc_then_emergency_metrics
CFG
if [[ -f "${BASELINE_CKPT}" ]]; then
  ln -snf "$(cd "$(dirname "${BASELINE_CKPT}")" && pwd)/$(basename "${BASELINE_CKPT}")" experiments/best_embed_kd/best_model.ckpt
fi
if run_eval "${BASELINE_CKPT}" "experiments/best_embed_kd" "best_embed_kd" "embed_only" "true" "false"; then
  :
else
  cat > experiments/best_embed_kd/summary.md <<EOF
# best_embed_kd Summary (pending)

- run_id: \`${RUN_ID}\`
- status: pending checkpoint from server
- expected checkpoint: \`${BASELINE_CKPT}\`
EOF
  cat > experiments/best_embed_kd/metrics.json <<EOF
{
  "run_id": "${RUN_ID}",
  "exp_id": "best_embed_kd",
  "status": "pending",
  "reason": "local TensorFlow unavailable or server baseline checkpoint not evaluated yet",
  "checkpoint": "${BASELINE_CKPT}"
}
EOF
  python - <<'PY'
import os
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(7, 4))
ax.axis("off")
ax.set_title("best_embed_kd confusion matrix (pending)")
ax.text(0.5, 0.5, "Pending local evaluation\n(TensorFlow not available)", ha="center", va="center")
fig.tight_layout()
fig.savefig("experiments/best_embed_kd/confusion_matrix.png", dpi=160, bbox_inches="tight")
plt.close(fig)
PY
fi

# ----------------------------
# Priority 2: ablation A/B/C/D
# ----------------------------
A_CKPT="${ABLAT_A_CKPT:-${MODEL_ROOT}/ablation/exp_A/student_kd_best.weights.h5}"
B_CKPT="${ABLAT_B_CKPT:-${MODEL_ROOT}/ablation/exp_B/student_kd_best.weights.h5}"
C_CKPT="${ABLAT_C_CKPT:-${MODEL_ROOT}/ablation/exp_C/student_kd_best.weights.h5}"
D_CKPT="${ABLAT_D_CKPT:-${MODEL_ROOT}/ablation/exp_D/student_kd_best.weights.h5}"

ok_ablation=1
run_eval "${A_CKPT}" "experiments/ablation_embed_vs_aug/exp_A" "ablation_exp_A" "ce_only" "false" "false" || ok_ablation=0
run_eval "${B_CKPT}" "experiments/ablation_embed_vs_aug/exp_B" "ablation_exp_B" "embed_only" "false" "false" || ok_ablation=0
run_eval "${C_CKPT}" "experiments/ablation_embed_vs_aug/exp_C" "ablation_exp_C" "ce_only" "true" "false" || ok_ablation=0
run_eval "${D_CKPT}" "experiments/ablation_embed_vs_aug/exp_D" "ablation_exp_D" "embed_only" "true" "false" || ok_ablation=0

if [[ "${ok_ablation}" == "1" ]]; then
  python scripts/build_ablation_report.py \
    --exp-a experiments/ablation_embed_vs_aug/exp_A/metrics.json \
    --exp-b experiments/ablation_embed_vs_aug/exp_B/metrics.json \
    --exp-c experiments/ablation_embed_vs_aug/exp_C/metrics.json \
    --exp-d experiments/ablation_embed_vs_aug/exp_D/metrics.json \
    --output-dir experiments/ablation_embed_vs_aug
else
  cat > experiments/ablation_embed_vs_aug/comparison_table.csv <<EOF
exp,run_id,exp_id,kd_variant,aug_flag,prewarm_flag,overall_acc,emergency_recall,emergency_f1,movement_recall,cm_path
EOF
  cat > experiments/ablation_embed_vs_aug/ablation_summary.md <<EOF
# Ablation Summary (pending)

- run_id: \`${RUN_ID}\`
- status: pending one or more checkpoints from server
- expected: A/B/C/D checkpoints under \`${MODEL_ROOT}/ablation/\`
EOF
fi

# ----------------------------
# Priority 3: prewarm
# ----------------------------
DIRECT_CKPT="${PREWARM_DIRECT_CKPT:-${MODEL_ROOT}/prewarm/direct_noisy/student_kd_best.weights.h5}"
PREWARM_CKPT="${PREWARM_CKPT:-${MODEL_ROOT}/prewarm/prewarm_clean_then_noisy/student_kd_best.weights.h5}"

ok_prewarm=1
run_eval "${DIRECT_CKPT}" "experiments/prewarm_curriculum/direct_noisy" "prewarm_direct_noisy" "embed_only" "true" "false" || ok_prewarm=0
run_eval "${PREWARM_CKPT}" "experiments/prewarm_curriculum/prewarm_clean_then_noisy" "prewarm_clean_then_noisy" "embed_only" "true" "true" || ok_prewarm=0

if [[ "${ok_prewarm}" == "1" ]]; then
  python scripts/build_metrics_table.py \
    --item direct_noisy=experiments/prewarm_curriculum/direct_noisy/metrics.json \
    --item prewarm_clean_then_noisy=experiments/prewarm_curriculum/prewarm_clean_then_noisy/metrics.json \
    --output-csv experiments/prewarm_curriculum/comparison_table.csv \
    --output-md experiments/prewarm_curriculum/prewarm_summary.md \
    --title "Prewarm Curriculum Comparison"
else
  cat > experiments/prewarm_curriculum/comparison_table.csv <<EOF
label,run_id,exp_id,kd_variant,aug_flag,prewarm_flag,overall_acc,emergency_recall,emergency_f1,movement_recall,cm_path
EOF
  cat > experiments/prewarm_curriculum/prewarm_summary.md <<EOF
# Prewarm Summary (pending)

- run_id: \`${RUN_ID}\`
- status: pending direct/prewarm checkpoints from server
- expected: \`${MODEL_ROOT}/prewarm/\`
EOF
fi

DIRECT_HISTORY="${DIRECT_HISTORY:-${RESULT_ROOT}/prewarm/direct_noisy/history/student_history.csv}"
PREWARM_HISTORY="${PREWARM_HISTORY:-${RESULT_ROOT}/prewarm/prewarm_clean_then_noisy/history/student_history.csv}"
if [[ -f "${DIRECT_HISTORY}" && -f "${PREWARM_HISTORY}" ]]; then
  python scripts/plot_kd_histories.py \
    --direct-history "${DIRECT_HISTORY}" \
    --prewarm-history "${PREWARM_HISTORY}" \
    --max-epoch 10 \
    --output-png experiments/prewarm_curriculum/learning_curves.png \
    --output-csv experiments/prewarm_curriculum/learning_curves.csv
fi

# ----------------------------
# Priority 4: logits recheck
# ----------------------------
LOGITS_ONLY_CKPT="${LOGITS_ONLY_CKPT:-${MODEL_ROOT}/logits_recheck/logits_only/student_kd_best.weights.h5}"
CE_LOGITS_CKPT="${CE_LOGITS_CKPT:-${MODEL_ROOT}/logits_recheck/ce_plus_logits/student_kd_best.weights.h5}"
EMBED_REF_CKPT="${EMBED_REF_CKPT:-${MODEL_ROOT}/logits_recheck/embed_only_reference/student_kd_best.weights.h5}"

ok_logits=1
run_eval "${LOGITS_ONLY_CKPT}" "experiments/logits_kd_recheck/logits_only" "logits_only" "ce_logits(alpha=0)" "true" "false" || ok_logits=0
run_eval "${CE_LOGITS_CKPT}" "experiments/logits_kd_recheck/ce_plus_logits" "ce_plus_logits" "ce_logits" "true" "false" || ok_logits=0
run_eval "${EMBED_REF_CKPT}" "experiments/logits_kd_recheck/embed_only_reference" "embed_only_reference" "embed_only" "true" "false" || ok_logits=0

if [[ "${ok_logits}" == "1" ]]; then
  python scripts/build_metrics_table.py \
    --item logits_only=experiments/logits_kd_recheck/logits_only/metrics.json \
    --item ce_plus_logits=experiments/logits_kd_recheck/ce_plus_logits/metrics.json \
    --item embed_only_reference=experiments/logits_kd_recheck/embed_only_reference/metrics.json \
    --output-csv experiments/logits_kd_recheck/comparison_table.csv \
    --output-md experiments/logits_kd_recheck/kd_failure_analysis.md \
    --title "Logits KD Recheck"
else
  cat > experiments/logits_kd_recheck/comparison_table.csv <<EOF
label,run_id,exp_id,kd_variant,aug_flag,prewarm_flag,overall_acc,emergency_recall,emergency_f1,movement_recall,cm_path
EOF
  cat > experiments/logits_kd_recheck/kd_failure_analysis.md <<EOF
# Logits KD Failure Analysis (pending)

- run_id: \`${RUN_ID}\`
- status: pending logits recheck checkpoints from server
- expected: \`${MODEL_ROOT}/logits_recheck/\`
- analysis focus:
  - early-epoch instability
  - soft-target mismatch under low SNR
  - representation transfer stability vs logits transfer
EOF
fi

echo "[LocalEval] done"
