#!/usr/bin/env python3
"""Dry-run by default; attest an authorized four-split metadata proposal."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.multilingual_audio_bridge.materialize import freeze_metadata_proposal


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--proposal", required=True)
    parser.add_argument("--feasibility-report", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    result = freeze_metadata_proposal(
        args.config,
        args.proposal,
        args.feasibility_report,
        args.output,
        execute=args.execute,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
