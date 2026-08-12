#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "Usage: $0 EXPECTED_COMMIT MANIFEST_JSONL VALIDATION_RECEIPT_JSON AUDIO_ROOT" >&2
  exit 2
fi

EXPECTED_COMMIT=$1
MANIFEST_PATH=$2
VALIDATION_RECEIPT_PATH=$3
AUDIO_ROOT=$4
REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)

cd "$REPO_ROOT"
export MPLCONFIGDIR=${MPLCONFIGDIR:-/tmp/drone_w33_matplotlib}
export NUMBA_CACHE_DIR=${NUMBA_CACHE_DIR:-/tmp/drone_w33_numba}
export XDG_CACHE_HOME=${XDG_CACHE_HOME:-/tmp/drone_w33_cache}

if [[ $(git rev-parse HEAD) != "$EXPECTED_COMMIT" ]]; then
  echo "Refusing preflight: HEAD does not match EXPECTED_COMMIT" >&2
  exit 3
fi
if [[ -n $(git status --porcelain) ]]; then
  echo "Refusing preflight: worktree is not clean" >&2
  exit 4
fi

CONFIGS=(
  config/multilingual_2026w33/en_only_anchor_v0.json
  config/multilingual_2026w33/multilingual_naive_pooled_v0.json
  config/multilingual_2026w33/multilingual_balanced_main_v0.json
)

for config_path in "${CONFIGS[@]}"; do
  conda run -n drone python scripts/run_multilingual_retraining_2026w33.py \
    --mode preflight \
    --config "$config_path" \
    --manifest "$MANIFEST_PATH" \
    --manifest-validation-receipt "$VALIDATION_RECEIPT_PATH" \
    --audio-root "$AUDIO_ROOT" \
    --verify-audio
done

echo "Preflight passed for all W33 multilingual lanes at commit $EXPECTED_COMMIT"
