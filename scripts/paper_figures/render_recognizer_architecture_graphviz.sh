#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC="$ROOT/docs/paper_sensys2027/figures/source/recognizer_architecture.dot"
OUT_DIR="$ROOT/docs/paper_sensys2027/figures"

if ! command -v neato >/dev/null 2>&1; then
  echo "Graphviz neato is required to render recognizer_architecture.dot." >&2
  exit 1
fi

TMP_DOT="$(mktemp "${TMPDIR:-/tmp}/recognizer_architecture.XXXXXX.dot")"
trap 'rm -f "$TMP_DOT" "${TMP_SVG:-}"' EXIT

perl -0pe 's/pos="([0-9.]+),([0-9.]+)!"/sprintf("pos=\"%.1f,%.1f!\"", $1 * 72, $2 * 72)/ge' "$SRC" > "$TMP_DOT"

neato -n2 -Tpdf "$TMP_DOT" -o "$OUT_DIR/recognizer_architecture.pdf"

if command -v rsvg-convert >/dev/null 2>&1; then
  TMP_SVG="$(mktemp "${TMPDIR:-/tmp}/recognizer_architecture.XXXXXX.svg")"
  neato -n2 -Tsvg "$TMP_DOT" -o "$TMP_SVG"
  rsvg-convert -f png -w 2400 -b white -o "$OUT_DIR/recognizer_architecture.png" "$TMP_SVG"
else
  neato -n2 -Tpng -Gsize=9,3.8\! -Gdpi=260 "$TMP_DOT" -o "$OUT_DIR/recognizer_architecture.png"
fi

echo "$OUT_DIR/recognizer_architecture.pdf"
echo "$OUT_DIR/recognizer_architecture.png"
