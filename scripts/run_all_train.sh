#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${ROOT_DIR}/logs"
LOG_FILE="${LOG_DIR}/train_$(date +"%Y%m%d_%H%M%S").log"

mkdir -p "${LOG_DIR}"

export PYTHONUNBUFFERED=1
export CUDA_VISIBLE_DEVICES=0

{
  echo "=== Run start ==="
  echo "Python: $(python3 --version 2>&1)"
  echo "Working dir: ${ROOT_DIR}"
  echo

  echo "[1/12] train_fft.py"
  python3 "${ROOT_DIR}/src/train_fft.py"
  echo

  echo "[2/12] train_logmel.py"
  python3 "${ROOT_DIR}/src/train_logmel.py"
  echo

  echo "[3/12] train_pcen.py"
  python3 "${ROOT_DIR}/src/train_pcen.py"
  echo

  echo "[4/12] train_mfcc.py"
  python3 "${ROOT_DIR}/src/train_mfcc.py"
  echo

  echo "[5/12] train_logmel_wiener.py"
  python3 "${ROOT_DIR}/src/train_logmel_wiener.py"
  echo

  echo "[6/12] train_pcen_wiener_real.py"
  python3 "${ROOT_DIR}/src/train_pcen_wiener_real.py"
  echo

  echo "[7/12] train_mfcc_wiener.py"
  python3 "${ROOT_DIR}/src/train_mfcc_wiener.py"
  echo

  echo "[8/12] train_fft_specsub.py"
  python3 "${ROOT_DIR}/src/train_fft_specsub.py"
  echo

  echo "[9/12] train_logmel_specsub.py"
  python3 "${ROOT_DIR}/src/train_logmel_specsub.py"
  echo

  echo "[10/12] train_pcen_specsub.py"
  python3 "${ROOT_DIR}/src/train_pcen_specsub.py"
  echo

  echo "[11/12] train_mfcc_specsub.py"
  python3 "${ROOT_DIR}/src/train_mfcc_specsub.py"
  echo

  echo "[12/12] train_fft_wiener.py"
  python3 "${ROOT_DIR}/src/train_fft_wiener.py"
  echo

  echo "=== Run end ==="
} 2>&1 | awk '{ if (length($0)==0) {print ""} else {print strftime("[%Y-%m-%d %H:%M:%S]"), $0} }' | tee -a "${LOG_FILE}"
