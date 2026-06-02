#!/usr/bin/env python3
"""Render the Akouo response-time breakdown figure as vector PDF."""

from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "paper_sensys2027" / "figures" / "response_time_breakdown.pdf"
EVIDENCE_ROOT = ROOT / ("weekly" + "result")
RUNTIME_TAG = "rt" + "1s"
MODEL_SIZE_TAG = "c" + "32"

VALIDATION = (
    EVIDENCE_ROOT
    / "weekly_drone_2026w19"
    / "realworld"
    / f"esp32_{RUNTIME_TAG}_{MODEL_SIZE_TAG}_validation"
    / "validation_summary.json"
)
PIPELINE = (
    EVIDENCE_ROOT
    / "weekly_drone_2026w19"
    / "realworld"
    / "esp32_dual_core_pipeline_validation"
    / f"mode_{MODEL_SIZE_TAG[0]}_full_{RUNTIME_TAG}_summary.json"
)
CONTINUOUS = (
    EVIDENCE_ROOT
    / "weekly_drone_2026w19"
    / "realworld"
    / "esp32_ble_continuous_pipeline"
    / f"ble_continuous_{RUNTIME_TAG}_w30_summary.json"
)
SDK_TIMEOUT = (
    EVIDENCE_ROOT
    / "weekly_drone_2026w20"
    / "realworld"
    / "tello_battery_probe"
    / "tello_battery_live_summary.json"
)
SDK_ACK = (
    EVIDENCE_ROOT
    / "weekly_drone_2026w20"
    / "realworld"
    / "tello_battery_probe"
    / "tello_battery_live_p9000_try1_summary.json"
)


INK = "#1b2a34"
MUTED = "#5f6f7a"
BLUE = "#4477AA"
TEAL = "#228A8D"
ORANGE = "#D55E00"
GREEN = "#66A61E"
GRAY = "#C7D0D8"
LIGHT = "#F6F8FA"
WARN = "#E8B25B"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def as_float(value: object) -> float:
    if value in ("", None):
        return float("nan")
    return float(value)


def draw_round_box(ax, x, y, w, h, text, fc, ec=INK, lw=1.1, fontsize=7.7):
    box = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.014,rounding_size=0.035",
        linewidth=lw,
        facecolor=fc,
        edgecolor=ec,
    )
    ax.add_patch(box)
    ax.text(
        x + w / 2,
        y + h / 2,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
        color=INK,
        linespacing=1.12,
    )
    return box


def draw_arrow(ax, x1, y1, x2, y2, color=INK, lw=1.5):
    ax.add_patch(
        FancyArrowPatch(
            (x1, y1),
            (x2, y2),
            arrowstyle="-|>",
            mutation_scale=10,
            linewidth=lw,
            color=color,
            shrinkA=4,
            shrinkB=4,
        )
    )


def main() -> None:
    validation = load_json(VALIDATION)
    pipeline = load_json(PIPELINE)
    continuous = load_json(CONTINUOUS)
    sdk_timeout = load_json(SDK_TIMEOUT)
    sdk_ack = load_json(SDK_ACK)

    latency = validation["latency_30"]
    capture_ms = as_float(latency["capture_p50_ms"])
    frontend_ms = as_float(latency["frontend_p50_ms"])
    infer_ms = as_float(latency["infer_p50_ms"])
    total_ms = as_float(latency["total_p50_ms"])
    total_p95_ms = as_float(latency["total_p95_ms"])

    first_window_ms = float(pipeline["first_window_end_to_end_ms"])
    period_p95_ms = float(pipeline["infer_output_period_p95_ms"])
    continuous_p50 = float(continuous["inter_arrival_p50_ms"])
    continuous_p95 = float(continuous["inter_arrival_p95_ms"])
    windows = int(continuous["success_windows"])
    target_windows = int(continuous["target_windows"])

    sdk_timeout_ms = as_float(sdk_timeout["command_rtt_ms"])
    sdk_ack_ms = as_float(sdk_ack["command_rtt_ms"])

    fig, ax = plt.subplots(figsize=(7.35, 2.95))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(
        0.02,
        0.94,
        "Measured response-time components",
        ha="left",
        va="top",
        fontsize=10.5,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        0.02,
        0.885,
        "Speech stays an event stream; command-boundary timing is reported separately.",
        ha="left",
        va="top",
        fontsize=7.6,
        color=MUTED,
    )

    # First-window path.
    x0, y0, h = 0.035, 0.64, 0.105
    total_bar_w = 0.67
    components = [
        ("capture\nwindow", capture_ms, BLUE),
        ("log-mel\nfrontend", frontend_ms, TEAL),
        ("integer\ninvoke", infer_ms, GREEN),
    ]
    x = x0
    denom = sum(v for _, v, _ in components)
    for label, value, color in components:
        w = total_bar_w * value / denom
        ax.add_patch(
            FancyBboxPatch(
                (x, y0),
                w,
                h,
                boxstyle="round,pad=0.006,rounding_size=0.018",
                linewidth=0.8,
                edgecolor="white",
                facecolor=color,
            )
        )
        ax.text(
            x + w / 2,
            y0 + h / 2,
            f"{label}\n{value:.0f} ms",
            ha="center",
            va="center",
            fontsize=6.9,
            color="white",
            fontweight="bold",
            linespacing=1.05,
        )
        x += w

    ax.text(
        x0,
        y0 - 0.035,
        f"First event: {first_window_ms:.0f} ms; 30-run total p50/p95: {total_ms:.0f}/{total_p95_ms:.0f} ms",
        ha="left",
        va="top",
        fontsize=7.6,
        color=INK,
    )

    # Event stream cadence and boundary as separate items.
    y2 = 0.38
    b1 = draw_round_box(
        ax,
        0.035,
        y2,
        0.22,
        0.135,
        f"steady event stream\np95 {period_p95_ms:.0f} ms",
        "#E9F2FA",
        BLUE,
    )
    b2 = draw_round_box(
        ax,
        0.315,
        y2,
        0.25,
        0.135,
        f"wireless event reporting\n{windows}/{target_windows} windows\np50/p95 {continuous_p50:.0f}/{continuous_p95:.0f} ms",
        "#EAF5F3",
        TEAL,
        fontsize=7.7,
    )
    b3 = draw_round_box(
        ax,
        0.625,
        y2,
        0.145,
        0.135,
        "bridge\ndecision\nXXX",
        "#FFF5DF",
        WARN,
    )
    b4 = draw_round_box(
        ax,
        0.82,
        y2,
        0.145,
        0.135,
        f"SDK boundary\nack {sdk_ack_ms:.1f} ms\nor timeout {sdk_timeout_ms:.0f} ms",
        "#FDECE6",
        ORANGE,
        fontsize=7.2,
    )
    draw_arrow(ax, 0.255, y2 + 0.067, 0.315, y2 + 0.067, BLUE)
    draw_arrow(ax, 0.565, y2 + 0.067, 0.625, y2 + 0.067, TEAL)
    draw_arrow(ax, 0.77, y2 + 0.067, 0.82, y2 + 0.067, ORANGE)

    ax.text(
        0.035,
        0.2,
        "Takeaway: the board sustains one event per audio window; bridge and SDK outcomes remain explicit boundary measurements.",
        ha="left",
        va="center",
        fontsize=7.8,
        color=INK,
    )

    ax.text(
        0.035,
        0.08,
        "Sources: W19 embedded validation and continuous event logs; W20 grounded SDK probes.",
        ha="left",
        va="center",
        fontsize=6.7,
        color=MUTED,
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight")
    plt.close(fig)
    print(OUT)


if __name__ == "__main__":
    main()
