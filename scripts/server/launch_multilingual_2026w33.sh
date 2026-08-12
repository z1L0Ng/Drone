#!/usr/bin/env bash
set -euo pipefail

MODE=print-only
if [[ ${1:-} == "--execute" ]]; then
  MODE=execute
  shift
elif [[ ${1:-} == "--print-only" ]]; then
  shift
fi

if [[ $# -ne 4 ]]; then
  echo "Usage: $0 [--print-only|--execute] EXPECTED_COMMIT MANIFEST_JSONL VALIDATION_RECEIPT_JSON AUDIO_ROOT" >&2
  exit 2
fi

EXPECTED_COMMIT=$1
MANIFEST_PATH=$2
VALIDATION_RECEIPT_PATH=$3
AUDIO_ROOT=$4
SESSION_NAME=weekly_drone_2026w33_multilingual_es_de
REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$REPO_ROOT"

if [[ ! $EXPECTED_COMMIT =~ ^[0-9a-f]{40}$ ]]; then
  echo "EXPECTED_COMMIT must be a full 40-character lowercase SHA" >&2
  exit 3
fi

RUN_COMMAND=(
  env DRONE_W33_MULTILINGUAL_EXECUTION_APPROVED=YES
  bash scripts/server/run_multilingual_2026w33_all.sh
  "$EXPECTED_COMMIT" "$MANIFEST_PATH" "$VALIDATION_RECEIPT_PATH" "$AUDIO_ROOT"
)
printf -v SHELL_COMMAND '%q ' "${RUN_COMMAND[@]}"
TMUX_COMMAND=(tmux new-session -d -s "$SESSION_NAME" "$SHELL_COMMAND")

if [[ $MODE == print-only ]]; then
  printf 'Prepared launch command (not executed):\n'
  printf '%q ' "${TMUX_COMMAND[@]}"
  printf '\n'
  exit 0
fi

if [[ ${DRONE_W33_SERVER_DISPATCH_APPROVED:-} != "YES" ]]; then
  echo "Refusing tmux creation: DRONE_W33_SERVER_DISPATCH_APPROVED=YES is required" >&2
  exit 4
fi
if [[ $(git rev-parse HEAD) != "$EXPECTED_COMMIT" ]]; then
  echo "Refusing tmux creation: HEAD does not match EXPECTED_COMMIT" >&2
  exit 5
fi
if [[ -n $(git status --porcelain) ]]; then
  echo "Refusing tmux creation: worktree is not clean" >&2
  exit 6
fi
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  echo "Refusing tmux creation: session already exists: $SESSION_NAME" >&2
  exit 7
fi

bash scripts/server/preflight_multilingual_2026w33.sh \
  "$EXPECTED_COMMIT" "$MANIFEST_PATH" "$VALIDATION_RECEIPT_PATH" "$AUDIO_ROOT"
"${TMUX_COMMAND[@]}"
echo "Started tmux session: $SESSION_NAME"
