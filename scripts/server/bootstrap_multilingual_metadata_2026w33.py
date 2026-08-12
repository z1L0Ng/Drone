#!/usr/bin/env python3
"""Default-dry-run GSC/MSWC metadata bootstrap for DATA-20260812-03."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.multilingual_audio_bridge.metadata_bootstrap import bootstrap_metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plan",
        default="config/multilingual_three_class/server_audio_bridge_v0.json",
    )
    parser.add_argument(
        "--intake-config",
        default="config/multilingual_three_class/es_de_v1.yaml",
    )
    parser.add_argument("--acquisition-receipt", required=True)
    parser.add_argument("--root", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    result = bootstrap_metadata(
        args.plan,
        args.intake_config,
        args.acquisition_receipt,
        args.root,
        execute=args.execute,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
