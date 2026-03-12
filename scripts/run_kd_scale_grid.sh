#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

MODE="${1:-${KD_GRID_MODE:-full}}"
if [[ "${MODE}" != "smoke" && "${MODE}" != "full" ]]; then
  echo "[Grid] unsupported mode: ${MODE} (use: smoke|full)" >&2
  exit 1
fi

IFS=',' read -r -a TEACHER_PROFILES <<< "${KD_GRID_TEACHER_PROFILES:-base,large,xlarge}"
IFS=',' read -r -a STUDENT_PROFILES <<< "${KD_GRID_STUDENT_PROFILES:-base,large,xlarge}"
IFS=',' read -r -a VARIANTS <<< "${KD_GRID_VARIANTS:-embed_only,ce_only,ce_logits,ce_embed,ce_logits_embed}"

RUN_TAG="${KD_GRID_RUN_TAG:-$(date +%Y%m%d_%H%M%S)}"
BASE_MODEL_DIR="${KD_GRID_MODEL_DIR:-${ROOT_DIR}/saved_models/logmel_kd_grid_${MODE}_${RUN_TAG}}"
BASE_RESULT_DIR="${KD_GRID_RESULT_DIR:-${ROOT_DIR}/result/logmel_kd_grid_${MODE}_${RUN_TAG}}"

mkdir -p "${BASE_MODEL_DIR}" "${BASE_RESULT_DIR}"

if [[ "${MODE}" == "smoke" ]]; then
  TEACHER_EPOCHS="${KD_TEACHER_EPOCHS:-1}"
  STUDENT_EPOCHS="${KD_STUDENT_EPOCHS:-1}"
  TEACHER_STEPS="${KD_TEACHER_STEPS_PER_EPOCH:-${KD_SMOKE_TRAIN_STEPS:-2}}"
  STUDENT_STEPS="${KD_STUDENT_STEPS_PER_EPOCH:-${KD_SMOKE_TRAIN_STEPS:-2}}"
  TEACHER_VAL_STEPS="${KD_TEACHER_VAL_STEPS:-${KD_SMOKE_VAL_STEPS:-1}}"
  STUDENT_VAL_STEPS="${KD_STUDENT_VAL_STEPS:-${KD_SMOKE_VAL_STEPS:-1}}"
  EVAL_STEPS="${KD_EVAL_STEPS:-${KD_SMOKE_EVAL_STEPS:-1}}"
  SKIP_FINAL_EVAL="${KD_SKIP_FINAL_EVAL:-1}"
else
  TEACHER_EPOCHS="${KD_TEACHER_EPOCHS:-50}"
  STUDENT_EPOCHS="${KD_STUDENT_EPOCHS:-50}"
  TEACHER_STEPS="${KD_TEACHER_STEPS_PER_EPOCH:-0}"
  STUDENT_STEPS="${KD_STUDENT_STEPS_PER_EPOCH:-0}"
  TEACHER_VAL_STEPS="${KD_TEACHER_VAL_STEPS:-0}"
  STUDENT_VAL_STEPS="${KD_STUDENT_VAL_STEPS:-0}"
  EVAL_STEPS="${KD_EVAL_STEPS:-0}"
  SKIP_FINAL_EVAL="${KD_SKIP_FINAL_EVAL:-0}"
fi

echo "[Grid] root=${ROOT_DIR}"
echo "[Grid] mode=${MODE}"
echo "[Grid] run_tag=${RUN_TAG}"
echo "[Grid] model_dir=${BASE_MODEL_DIR}"
echo "[Grid] result_dir=${BASE_RESULT_DIR}"
echo "[Grid] teacher_profiles=${TEACHER_PROFILES[*]}"
echo "[Grid] student_profiles=${STUDENT_PROFILES[*]}"
echo "[Grid] variants=${VARIANTS[*]}"
echo "[Grid] teacher_epochs=${TEACHER_EPOCHS}, student_epochs=${STUDENT_EPOCHS}"
echo "[Grid] smoke_knobs: teacher_steps=${TEACHER_STEPS}, student_steps=${STUDENT_STEPS}, teacher_val_steps=${TEACHER_VAL_STEPS}, student_val_steps=${STUDENT_VAL_STEPS}, eval_steps=${EVAL_STEPS}, skip_eval=${SKIP_FINAL_EVAL}"

for teacher_profile in "${TEACHER_PROFILES[@]}"; do
  teacher_root_dir="${BASE_MODEL_DIR}/teacher_${teacher_profile}"
  teacher_ckpt="${teacher_root_dir}/teacher_clean_best.weights.h5"
  mkdir -p "${teacher_root_dir}"

  first_combo_for_teacher=1
  for student_profile in "${STUDENT_PROFILES[@]}"; do
    combo_model_dir="${BASE_MODEL_DIR}/teacher_${teacher_profile}/student_${student_profile}"
    combo_result_dir="${BASE_RESULT_DIR}/teacher_${teacher_profile}/student_${student_profile}"
    mkdir -p "${combo_model_dir}" "${combo_result_dir}"

    for variant in "${VARIANTS[@]}"; do
      model_dir="${combo_model_dir}/${variant}"
      result_dir="${combo_result_dir}/${variant}"
      mkdir -p "${model_dir}" "${result_dir}"

      reuse_teacher="1"
      if [[ "${first_combo_for_teacher}" -eq 1 ]]; then
        reuse_teacher="0"
        first_combo_for_teacher=0
      fi

      echo "============================================================"
      echo "[Grid] teacher=${teacher_profile} student=${student_profile} variant=${variant} reuse_teacher=${reuse_teacher}"
      echo "============================================================"

      env_args=(
        "KD_DISTILL_VARIANT=${variant}"
        "KD_TEACHER_MODEL_PROFILE=${teacher_profile}"
        "KD_STUDENT_MODEL_PROFILE=${student_profile}"
        "KD_MODEL_DIR=${model_dir}"
        "KD_RESULT_DIR=${result_dir}"
        "KD_TEACHER_CKPT=${teacher_ckpt}"
        "KD_STUDENT_CKPT=${model_dir}/student_kd_best.weights.h5"
        "KD_REUSE_TEACHER=${reuse_teacher}"
        "KD_TEACHER_EPOCHS=${TEACHER_EPOCHS}"
        "KD_STUDENT_EPOCHS=${STUDENT_EPOCHS}"
        "KD_TEACHER_ENABLE_PROSODY_AUG=0"
        "KD_STUDENT_ENABLE_PROSODY_AUG=1"
        "KD_SKIP_FINAL_EVAL=${SKIP_FINAL_EVAL}"
      )

      if [[ "${TEACHER_STEPS}" != "0" ]]; then
        env_args+=("KD_TEACHER_STEPS_PER_EPOCH=${TEACHER_STEPS}")
      fi
      if [[ "${STUDENT_STEPS}" != "0" ]]; then
        env_args+=("KD_STUDENT_STEPS_PER_EPOCH=${STUDENT_STEPS}")
      fi
      if [[ "${TEACHER_VAL_STEPS}" != "0" ]]; then
        env_args+=("KD_TEACHER_VAL_STEPS=${TEACHER_VAL_STEPS}")
      fi
      if [[ "${STUDENT_VAL_STEPS}" != "0" ]]; then
        env_args+=("KD_STUDENT_VAL_STEPS=${STUDENT_VAL_STEPS}")
      fi
      if [[ "${EVAL_STEPS}" != "0" ]]; then
        env_args+=("KD_EVAL_STEPS=${EVAL_STEPS}")
      fi

      env "${env_args[@]}" python "${ROOT_DIR}/src/train_logmel_kd.py"
    done
  done
done

echo "[Grid] mode=${MODE} completed"
