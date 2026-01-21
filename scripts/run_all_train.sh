#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${ROOT_DIR}/logs"
LOG_FILE="${LOG_DIR}/aligned_train.log"

mkdir -p "${LOG_DIR}"

export PYTHONUNBUFFERED=1

{
  echo "=== Run start: $(date) ==="
  echo "Python: $(python --version 2>&1)"
  echo "Working dir: ${ROOT_DIR}"
  echo

  echo "[1/4] train.py"
  python "${ROOT_DIR}/src/train.py"
  echo

  echo "[2/4] train_pcen.py"
  python "${ROOT_DIR}/src/train_pcen.py"
  echo

  echo "[3/4] train_logmel_wiener.py"
  python "${ROOT_DIR}/src/train_logmel_wiener.py"
  echo

  echo "[4/4] train_pcen_wiener_real.py"
  python "${ROOT_DIR}/src/train_pcen_wiener_real.py"
  echo

  echo "=== Run end: $(date) ==="
} 2>&1 | tee -a "${LOG_FILE}"
