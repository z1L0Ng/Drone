#!/usr/bin/env python3

import argparse
import csv
import json
import os


def load(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--item", action="append", required=True, help="format: label=metrics.json")
    parser.add_argument("--output-csv", required=True)
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--title", default="Metrics Summary")
    args = parser.parse_args()

    rows = []
    for item in args.item:
        if "=" not in item:
            raise ValueError(f"Invalid item: {item}")
        label, path = item.split("=", 1)
        m = load(path)
        rows.append(
            {
                "label": label,
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
        )

    rows.sort(key=lambda r: r["overall_acc"], reverse=True)

    os.makedirs(os.path.dirname(args.output_csv), exist_ok=True)
    os.makedirs(os.path.dirname(args.output_md), exist_ok=True)

    fields = [
        "label",
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

    with open(args.output_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    with open(args.output_md, "w", encoding="utf-8") as f:
        f.write(f"# {args.title}\n\n")
        f.write("| label | overall_acc | emergency_recall | emergency_f1 | movement_recall |\n")
        f.write("|---|---:|---:|---:|---:|\n")
        for r in rows:
            f.write(
                f"| {r['label']} | {r['overall_acc']:.4f} | {r['emergency_recall']:.4f} | "
                f"{r['emergency_f1']:.4f} | {r['movement_recall']:.4f} |\n"
            )

    print(f"Saved: {args.output_csv}")
    print(f"Saved: {args.output_md}")


if __name__ == "__main__":
    main()
