#!/usr/bin/env python3
"""Default-dry-run server entrypoint for DATA-20260812-03 stages S0-S3."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.multilingual_audio_bridge.orchestrator import run_orchestrator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plan/acquire/materialize/freeze multilingual W33 audio with stage receipts"
    )
    parser.add_argument(
        "--plan",
        default="config/multilingual_three_class/server_audio_bridge_v0.json",
    )
    parser.add_argument(
        "--intake-config",
        default="config/multilingual_three_class/es_de_v1.yaml",
    )
    parser.add_argument("--root", required=True)
    parser.add_argument("--manifest-version", default="multilingual-es-de-w33-v0")
    parser.add_argument("--stage", choices=("S0", "S1", "S2", "S3", "all"), default="all")
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_orchestrator(
        plan_path=args.plan,
        intake_config_path=args.intake_config,
        root=args.root,
        manifest_version=args.manifest_version,
        stage=args.stage,
        execute=args.execute,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
