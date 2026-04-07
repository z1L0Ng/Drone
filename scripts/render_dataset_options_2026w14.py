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


def pick_rows(rows: List[Dict[str, str]], datasets: List[str], mapping_variant: str, count_source: str) -> List[Dict[str, str]]:
    return [
        r
        for r in rows
        if r["dataset_name"] in datasets and r["mapping_variant"] == mapping_variant and r.get("count_source", "estimated") == count_source
    ]


def sum_counts(rows: List[Dict[str, str]]) -> Dict[str, int]:
    em = sum(to_int(r.get("emergency_count", "0")) for r in rows)
    no = sum(to_int(r.get("normal_count", "0")) for r in rows)
    return {"emergency": em, "normal": no, "total": em + no}


def main() -> None:
    args = parse_args()
    in_dir = Path(args.input_dir)

    manifest = read_csv(in_dir / "dataset_manifest_2026w14.csv")
    samples = read_csv(in_dir / "sample_count_table_2026w14.csv")

    combo_defs = [
        {
            "name": "Plan A: ESD + CREMA-D",
            "datasets": ["ESD", "CREMA-D"],
            "reason": "Best English coverage and best resilience if one source is delayed.",
            "effort": "medium",
            "meeting_deliverability": "high",
        },
        {
            "name": "Plan B: ESD only",
            "datasets": ["ESD"],
            "reason": "Largest single-source sample pool; simplest preprocessing path.",
            "effort": "low",
            "meeting_deliverability": "high",
        },
        {
            "name": "Plan C: CREMA-D only",
            "datasets": ["CREMA-D"],
            "reason": "Commercial-friendly baseline but smaller speaker/style diversity.",
            "effort": "low",
            "meeting_deliverability": "medium",
        },
    ]

    lines: List[str] = []
    lines.append("# Dataset Options 2026W14 (Phase1 English, Revision 1.1)")
    lines.append("")
    lines.append("## 0) Default Analysis Policy")
    lines.append("")
    lines.append("- Default main analysis mapping: `surprise_excluded`.")
    lines.append("- Surprise handling: `surprise_included` is used only in sensitivity appendix.")
    lines.append("- Reported counts include both `estimated` and `scanned` sources.")
    lines.append("")

    lines.append("## 1) Candidate Dataset Table")
    lines.append("")
    lines.append("| dataset | license | emergency_mapping(default) | normal_mapping(default) | est_default_em | est_default_normal | key_risks |")
    lines.append("|---|---|---|---|---:|---:|---|")

    for r in manifest:
        lines.append(
            f"| {r['dataset_name']} | {r['license_type']} | {r['label_mapping_emergency']} | {r['label_mapping_normal']} | {r['estimated_samples_emergency']} | {r['estimated_samples_normal']} | {r['risks']} |"
        )

    lines.append("")
    lines.append("## 2) Top 3 Recommended Plans")
    lines.append("")
    lines.append("| plan | reason | default(no-surprise, estimated em/normal/total) | sensitivity(with-surprise, estimated em/normal/total) | scanned(no-surprise em/normal/total) | effort | meeting_deliverability |")
    lines.append("|---|---|---|---|---|---|---|")

    for plan in combo_defs:
        est_default = sum_counts(pick_rows(samples, plan["datasets"], "surprise_excluded", "estimated"))
        est_sens = sum_counts(pick_rows(samples, plan["datasets"], "surprise_included", "estimated"))
        scan_default = sum_counts(pick_rows(samples, plan["datasets"], "surprise_excluded", "scanned"))

        lines.append(
            f"| {plan['name']} | {plan['reason']} | {est_default['emergency']}/{est_default['normal']}/{est_default['total']} | {est_sens['emergency']}/{est_sens['normal']}/{est_sens['total']} | {scan_default['emergency']}/{scan_default['normal']}/{scan_default['total']} | {plan['effort']} | {plan['meeting_deliverability']} |"
        )

    lines.append("")
    lines.append("## 3) Single Recommendation")
    lines.append("")
    lines.append("- Recommended: **Plan A: ESD + CREMA-D**.")
    lines.append("- Use `surprise_excluded` as mainline and treat `surprise_included` as appendix sensitivity check.")
    lines.append("")
    lines.append("## 4) Missing Information That Can Change Selection")
    lines.append("")
    lines.append("- Exact ESD and CREMA-D counts after copying downloaded audio into isolated root.")
    lines.append("- Whether deployment target requires strictly commercial-compatible datasets.")
    lines.append("")
    lines.append("## 5) Risks And Limitations")
    lines.append("")
    lines.append("- See: `risk_and_limitations_2026w14.md` (speaker, license, domain shift).")

    out_path = Path(args.output_md)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
