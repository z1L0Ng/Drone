#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${ROOT_DIR}/logs"
LOG_FILE="${LOG_DIR}/train.log"

mkdir -p "${LOG_DIR}"

export PYTHONUNBUFFERED=1

{
  echo "=== Run start ==="
  echo "Python: $(python --version 2>&1)"
  echo "Working dir: ${ROOT_DIR}"
  echo

  # 已有结果（注释掉）
  # echo "[1/6] train_fft.py"
  # python "${ROOT_DIR}/src/train_fft.py"
  # echo

  # echo "[2/6] train_logmel.py"
  # python "${ROOT_DIR}/src/train_logmel.py"
  # echo

  # echo "[3/6] train_logmel_wiener.py"
  # python "${ROOT_DIR}/src/train_logmel_wiener.py"
  # echo

  # echo "[4/6] train_mfcc.py"
  # python "${ROOT_DIR}/src/train_mfcc.py"
  # echo

  # echo "[5/6] train_pcen.py"
  # python "${ROOT_DIR}/src/train_pcen.py"
  # echo

  # echo "[6/6] train_pcen_wiener_real.py"
  # python "${ROOT_DIR}/src/train_pcen_wiener_real.py"
  # echo

  echo "[1/6] train_fft_specsub.py"
  python "${ROOT_DIR}/src/train_fft_specsub.py"
  echo

  echo "[2/6] train_logmel_specsub.py"
  python "${ROOT_DIR}/src/train_logmel_specsub.py"
  echo

  echo "[3/6] train_mfcc_specsub.py"
  python "${ROOT_DIR}/src/train_mfcc_specsub.py"
  echo

  echo "[4/6] train_pcen_specsub.py"
  python "${ROOT_DIR}/src/train_pcen_specsub.py"
  echo

  echo "[5/6] train_mfcc_wiener.py"
  python "${ROOT_DIR}/src/train_mfcc_wiener.py"
  echo

  echo "[6/6] train_fft_wiener.py"
  python "${ROOT_DIR}/src/train_fft_wiener.py"
  echo

  echo "=== Run end ==="
} 2>&1 | awk '{ if (length($0)==0) {print ""} else {print strftime("[%Y-%m-%d %H:%M:%S]"), $0} }' | tee -a "${LOG_FILE}"
