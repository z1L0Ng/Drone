#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC="$ROOT/docs/paper_sensys2027/figures/source/system_architecture.puml"
OUT_DIR="$ROOT/docs/paper_sensys2027/figures"
PLANTUML_JAR="${PLANTUML_JAR:-/private/tmp/plantuml.jar}"

if [[ ! -f "$PLANTUML_JAR" ]]; then
  echo "PlantUML jar not found: $PLANTUML_JAR" >&2
  echo "Set PLANTUML_JAR or download plantuml.jar before rendering." >&2
  exit 1
fi

if ! command -v rsvg-convert >/dev/null 2>&1; then
  echo "rsvg-convert is required to convert PlantUML SVG to PDF." >&2
  exit 1
fi

java -Djava.awt.headless=true -jar "$PLANTUML_JAR" -tsvg -o .. "$SRC"
rsvg-convert -f pdf -o "$OUT_DIR/system_architecture.pdf" "$OUT_DIR/system_architecture.svg"
java -Djava.awt.headless=true -jar "$PLANTUML_JAR" -tpng -o .. "$SRC"
rm -f "$OUT_DIR/system_architecture.svg"

echo "$OUT_DIR/system_architecture.pdf"
echo "$OUT_DIR/system_architecture.png"
