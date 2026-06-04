#!/usr/bin/env python3
"""Render the Akouo dual-core response-time schedule as vector PDF."""

from __future__ import annotations

import csv
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
FIG_DIR = ROOT / "docs" / "paper_sensys2027" / "figures"
OUT_PDF = FIG_DIR / "response_time_breakdown.pdf"
OUT_PNG = FIG_DIR / "response_time_breakdown.png"

EVIDENCE_ROOT = ROOT / ("weekly" + "result")
PIPELINE_DIR = (
    EVIDENCE_ROOT
    / "weekly_drone_2026w19"
    / "realworld"
    / "esp32_dual_core_pipeline_validation"
)
PIPELINE_SUMMARY = PIPELINE_DIR / "dual_core_pipeline_validation_summary.csv"


INK = "#1F2933"
MUTED = "#66737D"
GRID = "#D8DEE5"
CAPTURE = "#D8DDE3"
FRONTEND = "#EEF1F4"
INFERENCE = "#D8DDE3"


def as_float(value: object) -> float:
    if value in ("", None):
        return float("nan")
    return float(value)


def load_full_pipeline_row(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("pipeline_mode") == "full_tflm":
                return row
    raise ValueError(f"full pipeline row not found in {path}")


def add_bar(
    ax,
    y: float,
    start: float,
    width: float,
    color: str,
    hatch: str,
) -> None:
    ax.barh(
        y,
        width,
        left=start,
        height=0.32,
        color=color,
        edgecolor=INK,
        linewidth=0.75,
        hatch=hatch,
    )


def main() -> None:
    row = load_full_pipeline_row(PIPELINE_SUMMARY)
    capture_ms = as_float(row["capture_ms_p50"])
    frontend_ms = as_float(row["frontend_ms_p50"])
    infer_ms = as_float(row["infer_ms_p50"])

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.linewidth": 0.8,
        }
    )

    fig, ax = plt.subplots(figsize=(3.35, 1.35))

    add_bar(ax, 1.0, 0, capture_ms, CAPTURE, "////")
    add_bar(ax, 0.0, 0, frontend_ms, FRONTEND, "")
    add_bar(ax, 0.0, frontend_ms, infer_ms, INFERENCE, "\\\\\\\\")

    ax.set_xlim(0, 1200)
    ax.set_ylim(-0.45, 1.45)
    ax.set_yticks([1.0, 0.0])
    ax.set_yticklabels(["core0", "core1"], fontsize=6.8, color=INK)
    ax.set_xlabel("")
    ax.set_xticks([0, 300, 600, 900, 1200])
    ax.tick_params(axis="x", labelsize=6.8, colors=MUTED, length=2.6, pad=1.5)
    ax.tick_params(axis="y", length=0, pad=4)
    ax.grid(axis="x", color=GRID, linewidth=0.55, alpha=0.85)
    ax.set_axisbelow(True)

    for side in ("left", "right", "top"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PDF, bbox_inches="tight")
    fig.savefig(OUT_PNG, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(OUT_PDF)
    print(OUT_PNG)


if __name__ == "__main__":
    main()
