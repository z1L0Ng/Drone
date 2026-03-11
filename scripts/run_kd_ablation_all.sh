#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

VARIANTS=(embed_only ce_only ce_logits ce_embed ce_logits_embed)

export TF_CPP_MIN_LOG_LEVEL="${TF_CPP_MIN_LOG_LEVEL:-3}"
export KD_FIT_VERBOSE="${KD_FIT_VERBOSE:-2}"
export KD_PROSODY_LOG_SAMPLES="${KD_PROSODY_LOG_SAMPLES:-0}"
export KD_GAMMA_LOG_VERBOSE="${KD_GAMMA_LOG_VERBOSE:-0}"

RUN_TAG="${KD_ABLATION_RUN_TAG:-$(date +%Y%m%d_%H%M%S)}"
BASE_MODEL_DIR="${KD_ABLATION_MODEL_DIR:-${ROOT_DIR}/saved_models/logmel_kd_ablation_${RUN_TAG}}"
BASE_RESULT_DIR="${KD_ABLATION_RESULT_DIR:-${ROOT_DIR}/result/logmel_kd_ablation_${RUN_TAG}}"

SHARED_TEACHER_CKPT="${BASE_MODEL_DIR}/teacher_clean_best.weights.h5"

mkdir -p "${BASE_MODEL_DIR}" "${BASE_RESULT_DIR}"

echo "[Ablation] root=${ROOT_DIR}"
echo "[Ablation] run_tag=${RUN_TAG}"
echo "[Ablation] shared_teacher=${SHARED_TEACHER_CKPT}"
echo "[Ablation] model_dir=${BASE_MODEL_DIR}"
echo "[Ablation] result_dir=${BASE_RESULT_DIR}"

for idx in "${!VARIANTS[@]}"; do
  variant="${VARIANTS[$idx]}"
  model_dir="${BASE_MODEL_DIR}/${variant}"
  result_dir="${BASE_RESULT_DIR}/${variant}"

  mkdir -p "${model_dir}" "${result_dir}"

  reuse_teacher="1"
  if [[ "${idx}" -eq 0 ]]; then
    reuse_teacher="0"
  fi

  echo "============================================================"
  echo "[Ablation] variant=${variant} (reuse_teacher=${reuse_teacher})"
  echo "============================================================"

  KD_DISTILL_VARIANT="${variant}" \
  KD_MODEL_DIR="${model_dir}" \
  KD_RESULT_DIR="${result_dir}" \
  KD_TEACHER_CKPT="${SHARED_TEACHER_CKPT}" \
  KD_STUDENT_CKPT="${model_dir}/student_kd_best.weights.h5" \
  KD_REUSE_TEACHER="${reuse_teacher}" \
  KD_TEACHER_ENABLE_PROSODY_AUG="0" \
  KD_STUDENT_ENABLE_PROSODY_AUG="1" \
  python "${ROOT_DIR}/src/train_logmel_kd.py"
done

echo "[Ablation] training-only run completed"
