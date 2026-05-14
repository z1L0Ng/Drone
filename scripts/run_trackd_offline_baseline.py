#!/usr/bin/env python3
"""Track D offline baseline entrypoint."""

from __future__ import annotations

import json
import os
import sys

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from baselines.common.runner import build_arg_parser, load_config, run_training, smoke_check


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()
    config = load_config(args.config)

    if args.mode == "smoke":
        result = smoke_check(config, check_data=args.check_data_loader)
    elif args.mode == "tiny-train":
        result = run_training(
            config,
            run_mode="tiny-train",
            output_root=args.output_root,
            train_samples=args.tiny_train_samples,
            val_samples=args.tiny_val_samples,
            eval_samples=args.tiny_eval_samples,
            epochs=args.tiny_epochs,
            batch_size=args.tiny_batch_size,
        )
    elif args.mode == "train":
        if not args.allow_full_train:
            raise SystemExit(
                "Full training requires --allow-full-train and should only be "
                "used after manager approval from a committed server SHA."
            )
        result = run_training(config, run_mode="train", output_root=args.output_root)
    else:
        raise SystemExit(
            f"Unsupported mode: {args.mode}"
        )

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
