#!/usr/bin/env python3

import argparse
import csv
import os
from typing import Dict, List

import matplotlib.pyplot as plt


def read_history_csv(path: str) -> List[Dict[str, float]]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            out = {"epoch": int(row["epoch"])}
            for k, v in row.items():
                if k == "epoch":
                    continue
                if v == "":
                    continue
                out[k] = float(v)
            rows.append(out)
    return rows


def trim_epochs(rows: List[Dict[str, float]], max_epoch: int) -> List[Dict[str, float]]:
    return [r for r in rows if r.get("epoch", 0) <= max_epoch]


def series(rows: List[Dict[str, float]], key: str):
    x, y = [], []
    for r in rows:
        if key in r:
            x.append(r["epoch"])
            y.append(r[key])
    return x, y


def write_merged_csv(path: str, tagged_rows: Dict[str, List[Dict[str, float]]]) -> None:
    fields = ["strategy", "epoch", "accuracy", "val_accuracy", "loss", "val_loss"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for strategy, rows in tagged_rows.items():
            for r in rows:
                w.writerow(
                    {
                        "strategy": strategy,
                        "epoch": r.get("epoch", ""),
                        "accuracy": r.get("accuracy", ""),
                        "val_accuracy": r.get("val_accuracy", ""),
                        "loss": r.get("loss", ""),
                        "val_loss": r.get("val_loss", ""),
                    }
                )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--direct-history", required=True)
    parser.add_argument("--prewarm-history", required=True)
    parser.add_argument("--max-epoch", type=int, default=10)
    parser.add_argument("--output-png", required=True)
    parser.add_argument("--output-csv", required=True)
    args = parser.parse_args()

    direct_rows = trim_epochs(read_history_csv(args.direct_history), args.max_epoch)
    prewarm_rows = trim_epochs(read_history_csv(args.prewarm_history), args.max_epoch)

    os.makedirs(os.path.dirname(args.output_png), exist_ok=True)
    os.makedirs(os.path.dirname(args.output_csv), exist_ok=True)

    write_merged_csv(
        args.output_csv,
        {
            "direct_noisy": direct_rows,
            "prewarm_clean_then_noisy": prewarm_rows,
        },
    )

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))

    for label, rows in [("direct_noisy", direct_rows), ("prewarm_clean_then_noisy", prewarm_rows)]:
        x, y = series(rows, "accuracy")
        axes[0].plot(x, y, marker="o", label=f"{label} train")
        x, y = series(rows, "val_accuracy")
        axes[0].plot(x, y, marker="x", linestyle="--", label=f"{label} val")

    axes[0].set_title("Accuracy (first epochs)")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Accuracy")
    axes[0].grid(alpha=0.25)
    axes[0].legend(fontsize=8)

    for label, rows in [("direct_noisy", direct_rows), ("prewarm_clean_then_noisy", prewarm_rows)]:
        x, y = series(rows, "loss")
        axes[1].plot(x, y, marker="o", label=f"{label} train")
        x, y = series(rows, "val_loss")
        axes[1].plot(x, y, marker="x", linestyle="--", label=f"{label} val")

    axes[1].set_title("Loss (first epochs)")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Loss")
    axes[1].grid(alpha=0.25)
    axes[1].legend(fontsize=8)

    fig.tight_layout()
    fig.savefig(args.output_png, dpi=180, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {args.output_csv}")
    print(f"Saved: {args.output_png}")


if __name__ == "__main__":
    main()
