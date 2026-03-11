#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

mkdir -p "${ROOT_DIR}/logs"
timestamp="$(date +%Y%m%d_%H%M%S)"
log_file="${ROOT_DIR}/logs/log_${timestamp}.log"

echo "[launch] root=${ROOT_DIR}"
echo "[launch] log=${log_file}"

if [[ ! -f "/files1/Zilong/miniconda3/etc/profile.d/conda.sh" ]]; then
  echo "[launch] missing conda init script: /files1/Zilong/miniconda3/etc/profile.d/conda.sh" >&2
  exit 1
fi

nohup /bin/bash -lc "
  set -euo pipefail
  cd '${ROOT_DIR}'
  source /files1/Zilong/miniconda3/etc/profile.d/conda.sh
  conda activate drone
  export CUDA_VISIBLE_DEVICES=0
  export NUMBA_CACHE_DIR=/tmp/numba_cache
  export PYTHONUNBUFFERED=1
  mkdir -p /tmp/numba_cache
  bash '${ROOT_DIR}/scripts/run_kd_ablation_all.sh'
" >"${log_file}" 2>&1 &

pid=$!
echo "[launch] pid=${pid}"
echo "[launch] started"
