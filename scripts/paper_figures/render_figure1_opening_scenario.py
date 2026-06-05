#!/usr/bin/env python3
"""Render Figure 1 opening scenario as editable SVG, PDF, and PNG preview."""

from __future__ import annotations

import math
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Circle, FancyArrowPatch, FancyBboxPatch, Rectangle


ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "docs" / "paper_sensys2027" / "figures"
SOURCE = FIG / "source"
SVG = SOURCE / "figure1_opening_scenario.svg"
PDF = FIG / "figure1.pdf"
PNG = FIG / "figure1.png"

INK = "#1F2933"
MUTED = "#66737D"
BLUE = "#2F80C9"
BLUE_LIGHT = "#EAF3FC"
TEAL = "#228A8D"
TEAL_LIGHT = "#E8F5F4"
PURPLE = "#7A4FB3"
PURPLE_LIGHT = "#F2ECF8"
ORANGE = "#D55E00"
GREEN = "#5F9B2E"
GRAY = "#D8DEE6"
GRAY_LIGHT = "#F6F8FA"


def clean(ax):
    ax.set_xlim(0, 1.035)
    ax.set_ylim(0, 0.64)
    ax.axis("off")


def rounded(ax, x, y, w, h, text, fc, ec, fs=7.2, lw=1.0, weight="normal"):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.010,rounding_size=0.025",
        facecolor=fc,
        edgecolor=ec,
        linewidth=lw,
    )
    ax.add_patch(patch)
    ax.text(
        x + w / 2,
        y + h / 2,
        text,
        ha="center",
        va="center",
        fontsize=fs,
        color=INK if ec != PURPLE else PURPLE,
        fontweight=weight,
        linespacing=1.05,
    )
    return patch


def arrow(ax, start, end, color, lw=1.25, dashed=False, rad=0.0):
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            connectionstyle=f"arc3,rad={rad}",
            mutation_scale=9,
            linewidth=lw,
            linestyle=(0, (3, 2.5)) if dashed else "solid",
            color=color,
            shrinkA=4,
            shrinkB=4,
        )
    )


def draw_person(ax):
    ax.add_patch(Circle((0.095, 0.405), 0.036, fill=False, ec=INK, lw=1.35))
    ax.plot([0.095, 0.095], [0.368, 0.245], color=INK, lw=1.35)
    ax.plot([0.095, 0.045], [0.325, 0.275], color=INK, lw=1.35)
    ax.plot([0.095, 0.145], [0.325, 0.275], color=INK, lw=1.35)
    ax.plot([0.095, 0.058], [0.245, 0.165], color=INK, lw=1.35)
    ax.plot([0.095, 0.132], [0.245, 0.165], color=INK, lw=1.35)
    ax.text(0.095, 0.095, "nearby\nspeech", ha="center", va="center", fontsize=7.0, color=INK)


def draw_speech(ax):
    base_x, base_y = 0.155, 0.405
    for i in range(42):
        x = base_x + i * 0.0062
        envelope = 0.012 + 0.025 * math.sin(i * 0.31) ** 2
        amp = envelope * (0.55 + 0.45 * abs(math.sin(i * 0.78)))
        ax.plot([x, x], [base_y - amp, base_y + amp], color=BLUE, lw=1.0, alpha=0.95)
    ax.text(0.255, 0.482, "speech", ha="center", va="center", fontsize=6.6, color=BLUE)


def draw_drone(ax):
    cx, cy = 0.455, 0.405
    rotors = [(0.355, 0.505), (0.555, 0.505), (0.355, 0.305), (0.555, 0.305)]
    for rx, ry in rotors:
        ax.plot([cx, rx], [cy, ry], color=INK, lw=1.15)
        ax.add_patch(Circle((rx, ry), 0.030, fill=False, ec=INK, lw=1.15))
        ax.add_patch(Circle((rx, ry), 0.010, fc="white", ec=INK, lw=0.8))
        ax.plot([rx - 0.023, rx + 0.023], [ry, ry], color=MUTED, lw=0.8, alpha=0.75)
        for j, radius in enumerate([0.047, 0.063, 0.079]):
            ax.add_patch(
                Arc(
                    (rx, ry),
                    radius,
                    radius * 0.68,
                    theta1=20,
                    theta2=160,
                    color=BLUE if j == 0 else MUTED,
                    lw=0.7,
                    linestyle=(0, (2, 3)),
                    alpha=0.55,
                )
            )

    ax.add_patch(
        FancyBboxPatch(
            (cx - 0.052, cy - 0.035),
            0.104,
            0.070,
            boxstyle="round,pad=0.010,rounding_size=0.020",
            fc="white",
            ec=INK,
            lw=1.35,
        )
    )
    ax.add_patch(Rectangle((cx - 0.027, cy - 0.019), 0.054, 0.038, fc=TEAL_LIGHT, ec=TEAL, lw=1.0))
    ax.add_patch(Rectangle((cx - 0.008, cy - 0.007), 0.016, 0.014, fc=INK, ec=INK, lw=0.6))
    ax.text(cx, cy - 0.094, "Akouo\nevent source", ha="center", va="center", fontsize=6.0, color=TEAL)
    ax.text(cx + 0.030, 0.585, "rotor noise", ha="center", va="center", fontsize=6.6, color=MUTED)
    return cx, cy


def chip(ax, x, y, w, text, ec):
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            0.024,
            boxstyle="round,pad=0.004,rounding_size=0.012",
            fc="white",
            ec=ec,
            lw=0.75,
        )
    )
    ax.text(x + w / 2, y + 0.012, text, ha="center", va="center", fontsize=4.7, color=INK)


def draw_events_and_boundary(ax):
    rounded(ax, 0.610, 0.294, 0.225, 0.108, "", GRAY_LIGHT, MUTED, fs=7.0, lw=1.0)
    ax.text(0.722, 0.365, "intent event", ha="center", va="center", fontsize=7.2, color=INK, fontweight="bold")
    chip(ax, 0.628, 0.313, 0.060, "emergency", ORANGE)
    chip(ax, 0.700, 0.313, 0.060, "movement", GREEN)
    chip(ax, 0.772, 0.313, 0.055, "unknown", MUTED)

    ax.add_patch(
        FancyBboxPatch(
            (0.855, 0.245),
            0.040,
            0.185,
            boxstyle="round,pad=0.007,rounding_size=0.020",
            fc=PURPLE_LIGHT,
            ec=PURPLE,
            lw=1.35,
        )
    )
    ax.plot([0.875, 0.875], [0.265, 0.410], color=PURPLE, lw=2.3, solid_capstyle="round")
    ax.text(0.875, 0.475, "safety\nboundary", ha="center", va="center", fontsize=6.2, color=PURPLE, fontweight="bold")
    rounded(ax, 0.916, 0.306, 0.080, 0.064, "mediated\nresponse", "white", MUTED, fs=5.6, lw=0.95)


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    SOURCE.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7.10, 2.62))
    clean(ax)

    draw_person(ax)
    draw_speech(ax)
    cx, cy = draw_drone(ax)
    arrow(ax, (0.415, 0.405), (cx - 0.030, cy), BLUE, lw=1.2)
    arrow(ax, (cx + 0.030, cy - 0.030), (0.610, 0.352), TEAL, lw=1.2, rad=-0.10)
    draw_events_and_boundary(ax)
    arrow(ax, (0.835, 0.352), (0.855, 0.352), PURPLE, lw=1.2)
    arrow(ax, (0.895, 0.352), (0.916, 0.338), MUTED, lw=1.05, dashed=True)

    fig.savefig(SVG, bbox_inches="tight", pad_inches=0.035)
    fig.savefig(PDF, bbox_inches="tight", pad_inches=0.035)
    fig.savefig(PNG, bbox_inches="tight", pad_inches=0.035, dpi=300)
    plt.close(fig)
    print(SVG)
    print(PDF)
    print(PNG)


if __name__ == "__main__":
    main()
