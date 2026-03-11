#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

VARIANTS=(embed_only ce_only ce_logits ce_embed ce_logits_embed)

if [[ -z "${KD_ABLATION_MODEL_DIR:-}" ]]; then
  echo "[Finetune] KD_ABLATION_MODEL_DIR is required." >&2
  echo "[Finetune] Example: KD_ABLATION_MODEL_DIR=${ROOT_DIR}/saved_models/logmel_kd_ablation_20260310_010203 bash scripts/run_kd_finetune_all.sh" >&2
  exit 1
fi

BASE_MODEL_DIR="${KD_ABLATION_MODEL_DIR}"
BASE_FINETUNE_DIR="${KD_ABLATION_FINETUNE_DIR:-${ROOT_DIR}/result/finetune/$(basename "${BASE_MODEL_DIR}")}"
SPLIT_CACHE="${KD_FINETUNE_SPLIT_CACHE:-${ROOT_DIR}/result/finetune/logmel_kd_split_indices.npz}"
TESTSET_DIR="${KD_FINETUNE_TESTSET_DIR:-testset}"
ENCODER_PATH="${KD_FINETUNE_ENCODER_PATH:-${ROOT_DIR}/saved_models/label_encoder.joblib}"

FINETUNE_RATIO="${KD_FINETUNE_RATIO:-0.3}"
VAL_RATIO="${KD_FINETUNE_VAL_RATIO:-0.1}"
EPOCHS="${KD_FINETUNE_EPOCHS:-10}"
BATCH_SIZE="${KD_FINETUNE_BATCH_SIZE:-32}"
LR="${KD_FINETUNE_LR:-1e-5}"
SEED="${KD_FINETUNE_SEED:-42}"

mkdir -p "${BASE_FINETUNE_DIR}"

echo "[Finetune] root=${ROOT_DIR}"
echo "[Finetune] model_dir=${BASE_MODEL_DIR}"
echo "[Finetune] testset_dir=${TESTSET_DIR}"
echo "[Finetune] encoder=${ENCODER_PATH}"
echo "[Finetune] output_dir=${BASE_FINETUNE_DIR}"
echo "[Finetune] split_cache=${SPLIT_CACHE}"
echo "[Finetune] epochs=${EPOCHS}, batch_size=${BATCH_SIZE}, lr=${LR}"

for variant in "${VARIANTS[@]}"; do
  model_dir="${BASE_MODEL_DIR}/${variant}"
  student_ckpt="${model_dir}/student_kd_best.weights.h5"
  finetuned_ckpt="${model_dir}/finetuned_best.weights.h5"
  output_dir="${BASE_FINETUNE_DIR}/${variant}"

  if [[ ! -f "${student_ckpt}" ]]; then
    echo "[Finetune] skip variant=${variant} (missing ${student_ckpt})"
    continue
  fi

  mkdir -p "${output_dir}"
  echo "============================================================"
  echo "[Finetune] variant=${variant}"
  echo "============================================================"

  python "${ROOT_DIR}/scripts/run_finetune_logmel_kd.py" \
    --testset "${TESTSET_DIR}" \
    --encoder "${ENCODER_PATH}" \
    --weights "${student_ckpt}" \
    --finetuned-weights "${finetuned_ckpt}" \
    --output "${output_dir}" \
    --split-cache "${SPLIT_CACHE}" \
    --finetune-ratio "${FINETUNE_RATIO}" \
    --val-ratio "${VAL_RATIO}" \
    --epochs "${EPOCHS}" \
    --batch-size "${BATCH_SIZE}" \
    --lr "${LR}" \
    --seed "${SEED}"
done

echo "[Finetune] all variants completed"
