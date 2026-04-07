#!/usr/bin/env python3

import argparse
import csv
from pathlib import Path
from typing import Dict, List


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--input-dir", required=True)
    p.add_argument("--output-md", required=True)
    return p.parse_args()


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def to_int(v: str) -> int:
    try:
        return int(v)
    except Exception:
        return 0


def build_combo_row(name: str, rows: List[Dict[str, str]], dataset_keys: List[str], variant: str) -> Dict[str, int]:
    selected = [r for r in rows if r["mapping_variant"] == variant and r["dataset_name"] in dataset_keys]
    em = sum(to_int(r["emergency_count"]) for r in selected)
    no = sum(to_int(r["normal_count"]) for r in selected)
    return {"name": name, "emergency": em, "normal": no, "total": em + no}


def main() -> None:
    args = parse_args()
    in_dir = Path(args.input_dir)

    manifest = read_csv(in_dir / "dataset_manifest_2026w14.csv")
    samples = read_csv(in_dir / "sample_count_table_2026w14.csv")

    combo_defs = [
        {
            "name": "Plan A: ESD + CREMA-D",
            "datasets": ["ESD", "CREMA-D"],
            "reason": "Best English coverage with complementary licensing profile.",
            "effort": "medium",
            "meeting_deliverability": "high",
        },
        {
            "name": "Plan B: ESD only",
            "datasets": ["ESD"],
            "reason": "Largest single-source sample pool with direct emotional labels.",
            "effort": "low",
            "meeting_deliverability": "high",
        },
        {
            "name": "Plan C: CREMA-D only",
            "datasets": ["CREMA-D"],
            "reason": "Commercial-friendly baseline with clean and simple structure.",
            "effort": "low",
            "meeting_deliverability": "medium",
        },
    ]

    lines: List[str] = []
    lines.append("# Dataset Options 2026W14 (Phase1 English)")
    lines.append("")
    lines.append("## 1) Candidate Dataset Table")
    lines.append("")
    lines.append("| dataset | official_url | license | academic_usable | commercial_usable | languages | emergency_mapping | normal_mapping | est_emergency | est_normal | sampling_rate | duration_sec | key_risks |")
    lines.append("|---|---|---|---|---|---|---|---|---:|---:|---|---|---|")

    for r in manifest:
        lines.append(
            "| {dataset_name} | {official_url} | {license_type} | {academic_usable} | {commercial_usable} | {languages} | {label_mapping_emergency} | {label_mapping_normal} | {estimated_samples_emergency} | {estimated_samples_normal} | {sampling_rate} | {duration_range_sec} | {risks} |".format(
                **r
            )
        )

    lines.append("")
    lines.append("## 2) Top 3 Recommended Plans")
    lines.append("")
    lines.append("| plan | reason | surprise_included (em/normal/total) | surprise_excluded (em/normal/total) | effort | meeting_deliverability |")
    lines.append("|---|---|---|---|---|---|")

    for plan in combo_defs:
        inc = build_combo_row(plan["name"], samples, plan["datasets"], "surprise_included")
        exc = build_combo_row(plan["name"], samples, plan["datasets"], "surprise_excluded")
        lines.append(
            f"| {plan['name']} | {plan['reason']} | {inc['emergency']}/{inc['normal']}/{inc['total']} | {exc['emergency']}/{exc['normal']}/{exc['total']} | {plan['effort']} | {plan['meeting_deliverability']} |"
        )

    lines.append("")
    lines.append("## 3) Single Recommendation")
    lines.append("")
    lines.append("- Recommended: **Plan A: ESD + CREMA-D**.")
    lines.append("- Why: highest usable English sample count for emergency/normal while preserving a commercial-usable anchor dataset.")
    lines.append("")
    lines.append("## 4) Missing Information That Can Change Selection")
    lines.append("")
    lines.append("- ESD exact per-emotion English file counts after actual licensed download.")
    lines.append("- CREMA-D exact per-emotion distribution (current emergency/normal counts are estimated).")
    lines.append("- Final downstream usage boundary (internal research only vs commercial deployment).")
    lines.append("")
    lines.append("## 5) Risks And Limitations")
    lines.append("")
    lines.append("- See: `risk_and_limitations_2026w14.md` (speaker bias, license constraints, domain shift).")

    out_path = Path(args.output_md)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
