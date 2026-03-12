#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

MODE="${1:-full}"
if [[ "${MODE}" != "smoke" && "${MODE}" != "full" ]]; then
  echo "[launch] unsupported mode: ${MODE} (use: smoke|full)" >&2
  exit 1
fi

mkdir -p "${ROOT_DIR}/logs"
timestamp="$(date +%Y%m%d_%H%M%S)"
log_file="${ROOT_DIR}/logs/log_kd_grid_${MODE}_${timestamp}.log"

echo "[launch] root=${ROOT_DIR}"
echo "[launch] mode=${MODE}"
echo "[launch] log=${log_file}"

if [[ ! -f "/files1/Zilong/miniconda3/etc/profile.d/conda.sh" ]]; then
  echo "[launch] missing conda init script: /files1/Zilong/miniconda3/etc/profile.d/conda.sh" >&2
  exit 1
fi

nohup setsid /bin/bash -lc "
  set -euo pipefail
  cd '${ROOT_DIR}'
  source /files1/Zilong/miniconda3/etc/profile.d/conda.sh
  conda activate drone
  export CUDA_VISIBLE_DEVICES=\${CUDA_VISIBLE_DEVICES:-0}
  export NUMBA_CACHE_DIR=/tmp/numba_cache
  export PYTHONUNBUFFERED=1
  mkdir -p /tmp/numba_cache
  bash '${ROOT_DIR}/scripts/run_kd_scale_grid.sh' '${MODE}'
" >"${log_file}" 2>&1 < /dev/null &

pid=$!
echo "[launch] pid=${pid}"
echo "[launch] started"
