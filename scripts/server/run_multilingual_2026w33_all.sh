#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "Usage: $0 EXPECTED_COMMIT MANIFEST_JSONL VALIDATION_RECEIPT_JSON AUDIO_ROOT" >&2
  exit 2
fi
if [[ ${DRONE_W33_MULTILINGUAL_EXECUTION_APPROVED:-} != "YES" ]]; then
  echo "Refusing execution: DRONE_W33_MULTILINGUAL_EXECUTION_APPROVED=YES is required" >&2
  exit 3
fi

EXPECTED_COMMIT=$1
MANIFEST_PATH=$2
VALIDATION_RECEIPT_PATH=$3
AUDIO_ROOT=$4
REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$REPO_ROOT"

bash scripts/server/preflight_multilingual_2026w33.sh \
  "$EXPECTED_COMMIT" "$MANIFEST_PATH" "$VALIDATION_RECEIPT_PATH" "$AUDIO_ROOT"

CONFIGS=(
  config/multilingual_2026w33/en_only_anchor_v0.json
  config/multilingual_2026w33/multilingual_naive_pooled_v0.json
  config/multilingual_2026w33/multilingual_balanced_main_v0.json
)
SEEDS=(0 1 2)

for config_path in "${CONFIGS[@]}"; do
  for seed_id in "${SEEDS[@]}"; do
    conda run -n drone python scripts/run_multilingual_retraining_2026w33.py \
      --mode train \
      --config "$config_path" \
      --manifest "$MANIFEST_PATH" \
      --manifest-validation-receipt "$VALIDATION_RECEIPT_PATH" \
      --audio-root "$AUDIO_ROOT" \
      --seed-id "$seed_id" \
      --expected-git-commit "$EXPECTED_COMMIT" \
      --allow-execution
  done
done
