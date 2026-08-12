#!/usr/bin/env python3
"""CLI for manifest-only multilingual preflight, fixture dry-run, and guarded training."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.multilingual_retraining.config import load_config
from src.multilingual_retraining.runner import (
    build_context,
    preflight_summary,
    run_guarded_training,
    run_synthetic_dry_run,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Manifest-driven W33 multilingual retraining preparation entrypoint"
    )
    parser.add_argument("--mode", choices=("preflight", "dry-run", "train"), required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--manifest-validation-receipt", required=True)
    parser.add_argument("--audio-root", required=True)
    parser.add_argument("--seed-id", type=int, default=0)
    parser.add_argument("--output-dir")
    parser.add_argument("--verify-audio", action="store_true")
    parser.add_argument("--expected-git-commit")
    parser.add_argument("--allow-execution", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    loaded = load_config(args.config)
    output_dir = args.output_dir
    if args.mode == "train":
        if output_dir is not None:
            raise SystemExit("train mode derives output path from the versioned config; omit --output-dir")
        output_dir = str(
            REPO_ROOT
            / loaded.effective["paths"]["output_root"]
            / loaded.effective["lane"]["run_name"]
            / f"seed_{args.seed_id:02d}"
        )
    context = build_context(
        repo_root=REPO_ROOT,
        config_path=args.config,
        manifest_path=args.manifest,
        validation_receipt_path=args.manifest_validation_receipt,
        audio_root=args.audio_root,
        output_dir=output_dir,
        seed_id=args.seed_id,
    )
    if args.mode == "preflight":
        summary = preflight_summary(context, verify_audio=args.verify_audio)
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    if args.mode == "dry-run":
        completion = run_synthetic_dry_run(context)
        print(json.dumps(completion, indent=2, sort_keys=True))
        return 0
    if not args.expected_git_commit:
        raise SystemExit("train mode requires --expected-git-commit")
    completion = run_guarded_training(
        context,
        expected_git_commit=args.expected_git_commit,
        allow_execution=args.allow_execution,
    )
    print(json.dumps(completion, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
