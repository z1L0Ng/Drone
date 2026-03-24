#!/usr/bin/env python3

import argparse
import csv
import json
import os


def load_metrics(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def metric_row(exp_name: str, m: dict) -> dict:
    return {
        "exp": exp_name,
        "run_id": m.get("run_id", ""),
        "exp_id": m.get("exp_id", ""),
        "kd_variant": m.get("kd_variant", ""),
        "aug_flag": int(bool(m.get("aug_flag", False))),
        "prewarm_flag": int(bool(m.get("prewarm_flag", False))),
        "overall_acc": float(m.get("overall_acc", 0.0)),
        "emergency_recall": float(m.get("emergency_recall", 0.0)),
        "emergency_f1": float(m.get("emergency_f1", 0.0)),
        "movement_recall": float(m.get("movement_recall", 0.0)),
        "cm_path": m.get("cm_path", ""),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp-a", required=True, help="metrics.json path for A(no KD, no aug)")
    parser.add_argument("--exp-b", required=True, help="metrics.json path for B(embed KD only)")
    parser.add_argument("--exp-c", required=True, help="metrics.json path for C(augmentation only)")
    parser.add_argument("--exp-d", required=True, help="metrics.json path for D(embed KD + augmentation)")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    A = metric_row("A", load_metrics(args.exp_a))
    B = metric_row("B", load_metrics(args.exp_b))
    C = metric_row("C", load_metrics(args.exp_c))
    D = metric_row("D", load_metrics(args.exp_d))
    rows = [A, B, C, D]

    csv_path = os.path.join(args.output_dir, "comparison_table.csv")
    fieldnames = [
        "exp",
        "run_id",
        "exp_id",
        "kd_variant",
        "aug_flag",
        "prewarm_flag",
        "overall_acc",
        "emergency_recall",
        "emergency_f1",
        "movement_recall",
        "cm_path",
    ]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    kd_gain = B["overall_acc"] - A["overall_acc"]
    aug_gain = C["overall_acc"] - A["overall_acc"]
    joint_gain = D["overall_acc"] - A["overall_acc"]
    interaction = D["overall_acc"] - B["overall_acc"] - C["overall_acc"] + A["overall_acc"]

    summary_path = os.path.join(args.output_dir, "ablation_summary.md")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("# Ablation Summary: Embedding KD vs Emergency Augmentation\n\n")
        f.write("## Metrics Table\n\n")
        f.write("| Exp | overall_acc | emergency_recall | emergency_f1 | movement_recall |\n")
        f.write("|---|---:|---:|---:|---:|\n")
        for r in rows:
            f.write(
                f"| {r['exp']} | {r['overall_acc']:.4f} | {r['emergency_recall']:.4f} | "
                f"{r['emergency_f1']:.4f} | {r['movement_recall']:.4f} |\n"
            )

        f.write("\n## Effect Decomposition (overall_acc)\n\n")
        f.write(f"- KD effect (B - A): `{kd_gain:+.4f}`\n")
        f.write(f"- Aug effect (C - A): `{aug_gain:+.4f}`\n")
        f.write(f"- Joint effect (D - A): `{joint_gain:+.4f}`\n")
        f.write(f"- Interaction (D - B - C + A): `{interaction:+.4f}`\n")

        f.write("\n## Interpretation Template\n\n")
        f.write("- If `KD effect` is clearly positive and stable on emergency metrics, embedding KD is a primary driver.\n")
        f.write("- If `Aug effect` is positive mainly on emergency recall/F1 but not movement, augmentation is class-targeted.\n")
        f.write("- Positive `Interaction` suggests KD and augmentation reinforce each other; near-zero suggests additive effects.\n")

    print(f"Saved: {csv_path}")
    print(f"Saved: {summary_path}")


if __name__ == "__main__":
    main()
