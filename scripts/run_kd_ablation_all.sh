#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

VARIANTS=(ce_only ce_logits ce_embed ce_logits_embed)

BASE_MODEL_DIR="${ROOT_DIR}/saved_models/logmel_kd_ablation"
BASE_RESULT_DIR="${ROOT_DIR}/result/logmel_kd_ablation"
BASE_FINETUNE_DIR="${ROOT_DIR}/result/finetune/logmel_kd_ablation"

SHARED_TEACHER_CKPT="${BASE_MODEL_DIR}/teacher_clean_best.weights.h5"
SPLIT_CACHE="${ROOT_DIR}/result/finetune/logmel_kd_split_indices.npz"

mkdir -p "${BASE_MODEL_DIR}" "${BASE_RESULT_DIR}" "${BASE_FINETUNE_DIR}"

echo "[Ablation] root=${ROOT_DIR}"
echo "[Ablation] shared_teacher=${SHARED_TEACHER_CKPT}"
echo "[Ablation] split_cache=${SPLIT_CACHE}"

for idx in "${!VARIANTS[@]}"; do
  variant="${VARIANTS[$idx]}"
  model_dir="${BASE_MODEL_DIR}/${variant}"
  result_dir="${BASE_RESULT_DIR}/${variant}"
  finetune_dir="${BASE_FINETUNE_DIR}/${variant}"

  mkdir -p "${model_dir}" "${result_dir}" "${finetune_dir}"

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
  python "${ROOT_DIR}/src/train_logmel_kd.py"

  python "${ROOT_DIR}/scripts/run_finetune_logmel_kd.py" \
    --weights "${model_dir}/student_kd_best.weights.h5" \
    --finetuned-weights "${model_dir}/finetuned_best.weights.h5" \
    --output "${finetune_dir}" \
    --split-cache "${SPLIT_CACHE}"
done

echo "[Ablation] all variants completed"
