#!/usr/bin/env bash
set -u

cd /files1/Zilong/Drone || exit 1
source /files1/Zilong/miniconda3/etc/profile.d/conda.sh || exit 1
conda activate drone || exit 1

export WEEKLY_TAG=drone_2026w14
export PYTHONUNBUFFERED=1
export NUMBA_CACHE_DIR=/tmp/numba_cache
mkdir -p /tmp/numba_cache

mkdir -p logs \
  saved_models/weekly_drone_2026w14/preprocess_ext \
  saved_models/weekly_drone_2026w14/branch_trial \
  result/weekly_drone_2026w14/preprocess_ext/history \
  result/weekly_drone_2026w14/branch_trial/history

test -f saved_models/weekly_drone_2026w14/baseline/teacher_clean_best.weights.h5 || { echo "[error] missing teacher ckpt"; exit 2; }
test -f saved_models/weekly_drone_2026w14/baseline/best_embed_kd/student_kd_best.weights.h5 || { echo "[error] missing baseline student ckpt"; exit 2; }

echo "[prep] ok"

run_and_report() {
  local run_name="$1"
  local model_dir="$2"
  local result_dir="$3"
  local history_dir="$4"
  local student_ckpt="$5"
  shift 5

  local ts log pid rc
  ts=$(date +"%Y%m%d_%H%M%S")
  log="logs/weekly_drone_2026w14_${run_name}_${ts}.log"

  (
    env \
      WEEKLY_TAG=drone_2026w14 \
      KD_SEED=42 \
      KD_TEACHER_MODEL_PROFILE=base \
      KD_STUDENT_MODEL_PROFILE=base \
      KD_TEACHER_ENABLE_PROSODY_AUG=0 \
      KD_ENABLE_CLASS_PROSODY_AUG=1 \
      KD_EMERGENCY_CLASS_NAME=emergency \
      KD_SKIP_FINAL_EVAL=0 \
      KD_REUSE_TEACHER=1 \
      KD_STUDENT_ENABLE_PROSODY_AUG=1 \
      KD_MODEL_DIR="$model_dir" \
      KD_RESULT_DIR="$result_dir" \
      KD_HISTORY_DIR="$history_dir" \
      KD_TEACHER_CKPT=saved_models/weekly_drone_2026w14/baseline/teacher_clean_best.weights.h5 \
      KD_STUDENT_CKPT="$student_ckpt" \
      "$@" \
      python src/train_logmel_kd.py
  ) > "$log" 2>&1 &

  pid=$!
  echo "[${run_name}_start] PID=${pid} LOG=${log}"

  for _ in $(seq 1 120); do
    if [ -s "$log" ]; then
      break
    fi
    if ! ps -p "$pid" >/dev/null 2>&1; then
      break
    fi
    sleep 5
  done

  echo "[${run_name}_head30]"
  head -n 30 "$log" 2>/dev/null || true

  wait "$pid"
  rc=$?
  echo "[${run_name}_exit] RC=${rc}"

  if [ -f "$student_ckpt" ]; then
    echo "[${run_name}_ckpt] ${student_ckpt}"
  else
    echo "[${run_name}_ckpt] MISSING:${student_ckpt}"
  fi

  echo "[${run_name}_result_tree]"
  find "$result_dir" -maxdepth 4 -print | sort

  echo "[${run_name}_tail50]"
  tail -n 50 "$log" 2>/dev/null || true

  echo "[${run_name}_summary] LOG=${log} RC=${rc}"
}

run_and_report preprocess_ext \
  saved_models/weekly_drone_2026w14/preprocess_ext \
  result/weekly_drone_2026w14/preprocess_ext \
  result/weekly_drone_2026w14/preprocess_ext/history \
  saved_models/weekly_drone_2026w14/preprocess_ext/student_kd_best.weights.h5 \
  KD_DISTILL_VARIANT=embed_only

run_and_report branch_trial \
  saved_models/weekly_drone_2026w14/branch_trial \
  result/weekly_drone_2026w14/branch_trial \
  result/weekly_drone_2026w14/branch_trial/history \
  saved_models/weekly_drone_2026w14/branch_trial/student_kd_best.weights.h5 \
  KD_DISTILL_VARIANT=ce_logits \
  KD_ALPHA_CE=1.0 \
  KD_LOGITS_BETA=1.0

echo "[all_done]"
