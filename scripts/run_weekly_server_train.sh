#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

MODE="${1:-all}"   # all | baseline | ablation | prewarm | logits
WEEKLY_TAG="${WEEKLY_TAG:-drone_2026w13}"

if [[ "${MODE}" != "all" && "${MODE}" != "baseline" && "${MODE}" != "ablation" && "${MODE}" != "prewarm" && "${MODE}" != "logits" ]]; then
  echo "[WeeklyTrain] unsupported mode: ${MODE} (use: all|baseline|ablation|prewarm|logits)" >&2
  exit 1
fi

BASE_MODEL_ROOT="${WEEKLY_MODEL_ROOT:-${ROOT_DIR}/saved_models/weekly_${WEEKLY_TAG}}"
BASE_RESULT_ROOT="${WEEKLY_RESULT_ROOT:-${ROOT_DIR}/result/weekly_${WEEKLY_TAG}}"

COMMON_ENV=(
  "KD_SEED=${KD_SEED:-42}"
  "KD_TEACHER_MODEL_PROFILE=${KD_TEACHER_MODEL_PROFILE:-base}"
  "KD_STUDENT_MODEL_PROFILE=${KD_STUDENT_MODEL_PROFILE:-base}"
  "KD_TEACHER_ENABLE_PROSODY_AUG=0"
  "KD_ENABLE_CLASS_PROSODY_AUG=1"
  "KD_EMERGENCY_CLASS_NAME=emergency"
  "KD_SKIP_FINAL_EVAL=${KD_SKIP_FINAL_EVAL:-0}"
)

mkdir -p "${BASE_MODEL_ROOT}" "${BASE_RESULT_ROOT}"

echo "[WeeklyTrain] mode=${MODE}"
echo "[WeeklyTrain] tag=${WEEKLY_TAG}"
echo "[WeeklyTrain] model_root=${BASE_MODEL_ROOT}"
echo "[WeeklyTrain] result_root=${BASE_RESULT_ROOT}"

run_one() {
  local group="$1"
  local exp_name="$2"
  local variant="$3"
  local aug_flag="$4"
  local prewarm_epochs="$5"
  local prewarm_use_logits="$6"
  local alpha_ce="$7"
  local logits_beta="$8"
  local reuse_teacher="$9"

  local group_model_dir="${BASE_MODEL_ROOT}/${group}"
  local group_result_dir="${BASE_RESULT_ROOT}/${group}"
  local model_dir="${group_model_dir}/${exp_name}"
  local result_dir="${group_result_dir}/${exp_name}"
  local history_dir="${result_dir}/history"
  local teacher_ckpt="${group_model_dir}/teacher_clean_best.weights.h5"

  mkdir -p "${model_dir}" "${result_dir}" "${history_dir}"

  echo "============================================================"
  echo "[WeeklyTrain] group=${group} exp=${exp_name} variant=${variant} aug=${aug_flag} prewarm=${prewarm_epochs}"
  echo "============================================================"

  env \
    "KD_DISTILL_VARIANT=${variant}" \
    "KD_MODEL_DIR=${model_dir}" \
    "KD_RESULT_DIR=${result_dir}" \
    "KD_HISTORY_DIR=${history_dir}" \
    "KD_TEACHER_CKPT=${teacher_ckpt}" \
    "KD_STUDENT_CKPT=${model_dir}/student_kd_best.weights.h5" \
    "KD_REUSE_TEACHER=${reuse_teacher}" \
    "KD_STUDENT_ENABLE_PROSODY_AUG=${aug_flag}" \
    "KD_PREWARM_EPOCHS=${prewarm_epochs}" \
    "KD_PREWARM_USE_LOGITS=${prewarm_use_logits}" \
    "KD_ALPHA_CE=${alpha_ce}" \
    "KD_LOGITS_BETA=${logits_beta}" \
    "${COMMON_ENV[@]}" \
    python "${ROOT_DIR}/src/train_logmel_kd.py"
}

if [[ "${MODE}" == "all" || "${MODE}" == "baseline" ]]; then
  run_one "baseline" "best_embed_kd" "embed_only" "1" "0" "1" "1.0" "1.0" "0"
fi

if [[ "${MODE}" == "all" || "${MODE}" == "ablation" ]]; then
  run_one "ablation" "exp_A" "ce_only" "0" "0" "1" "1.0" "1.0" "0"
  run_one "ablation" "exp_B" "embed_only" "0" "0" "1" "1.0" "1.0" "1"
  run_one "ablation" "exp_C" "ce_only" "1" "0" "1" "1.0" "1.0" "1"
  run_one "ablation" "exp_D" "embed_only" "1" "0" "1" "1.0" "1.0" "1"
fi

if [[ "${MODE}" == "all" || "${MODE}" == "prewarm" ]]; then
  run_one "prewarm" "direct_noisy" "embed_only" "1" "0" "1" "1.0" "1.0" "0"
  run_one "prewarm" "prewarm_clean_then_noisy" "embed_only" "1" "5" "1" "1.0" "1.0" "1"
fi

if [[ "${MODE}" == "all" || "${MODE}" == "logits" ]]; then
  run_one "logits_recheck" "logits_only" "ce_logits" "1" "0" "1" "0.0" "1.0" "0"
  run_one "logits_recheck" "ce_plus_logits" "ce_logits" "1" "0" "1" "1.0" "1.0" "1"
  run_one "logits_recheck" "embed_only_reference" "embed_only" "1" "0" "1" "1.0" "1.0" "1"
fi

echo "[WeeklyTrain] done"
