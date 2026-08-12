#!/usr/bin/env python3
"""Run a local, metadata-only three-class split feasibility proposal.

The command has no downloader and never reads or writes audio.  Dry-run is the
default.  Writing a non-canonical metadata proposal requires --write-proposal.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.multilingual_three_class_intake import ContractError, run_feasibility


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--metadata-index", required=True, type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Receipt directory; used only with --write-proposal.",
    )
    parser.add_argument(
        "--write-proposal",
        action="store_true",
        help="Write a non-canonical metadata proposal and feasibility report.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output_dir is not None and not args.write_proposal:
        raise ContractError("--output-dir has no effect without --write-proposal")
    report = run_feasibility(
        config_path=args.config,
        metadata_index_path=args.metadata_index,
        output_dir=args.output_dir,
        write_proposal=args.write_proposal,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContractError as exc:
        print(f"NO-GO: {exc}", file=sys.stderr)
        raise SystemExit(2)
