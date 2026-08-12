#!/usr/bin/env python3
"""Validate the frozen intake config and optional feasibility report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.multilingual_three_class_intake import (
    ContractError,
    canonical_json_sha256,
    load_json_yaml,
    sha256_file,
    validate_config,
    validate_config_artifacts,
    validate_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_json_yaml(args.config)
    unresolved = validate_config(config)
    inventory_receipt = validate_config_artifacts(args.config, config)
    result = {
        "status": "VALID",
        "config_file_sha256": sha256_file(args.config),
        "config_canonical_sha256": canonical_json_sha256(config),
        "unresolved_config_receipts": unresolved,
        "approved_unknown_inventory_receipt": inventory_receipt,
        "report_validated": False,
    }
    if args.report is not None:
        report = load_json_yaml(args.report)
        validate_report(report, config)
        result["report_validated"] = True
        result["report_file_sha256"] = sha256_file(args.report)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContractError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        raise SystemExit(2)
