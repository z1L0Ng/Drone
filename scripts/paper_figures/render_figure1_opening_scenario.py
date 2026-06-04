#!/usr/bin/env python3
"""Render Figure 1 opening scenario as vector PDF plus PNG preview."""

from __future__ import annotations

import math
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib.pyplot as plt
from matplotlib.path import Path as MplPath
from matplotlib.patches import Arc, Circle, FancyArrowPatch, FancyBboxPatch, PathPatch, Rectangle


ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "docs" / "paper_sensys2027" / "figures"
PDF = FIG / "figure1.pdf"
PNG = FIG / "figure1.png"

INK = "#1B2A34"
MUTED = "#5F6F7A"
LIGHT = "#F7FAFC"
BLUE = "#2F80C9"
BLUE_LIGHT = "#DCEBFA"
TEAL = "#228A8D"
TEAL_LIGHT = "#EAF5F3"
PURPLE = "#7A4FB3"
PURPLE_LIGHT = "#F0EAF7"
ORANGE = "#D55E00"
ORANGE_LIGHT = "#FDECE6"
GREEN = "#66A61E"
GREEN_LIGHT = "#EEF6E8"
GRAY = "#D8DEE6"
GRAY_LIGHT = "#F3F5F7"


def clean(ax):
    ax.set_xlim(0.02, 1.025)
    ax.set_ylim(0.03, 0.86)
    ax.axis("off")


def rounded(ax, x, y, w, h, text, fc, ec, fs=8.3, lw=1.15, weight="normal"):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.012,rounding_size=0.024",
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
        color=INK,
        fontweight=weight,
        linespacing=1.08,
    )
    return patch


def arrow(ax, start, end, color, lw=1.5, dashed=False, rad=0.0):
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            connectionstyle=f"arc3,rad={rad}",
            mutation_scale=10,
            linewidth=lw,
            linestyle=(0, (4, 3)) if dashed else "solid",
            color=color,
            shrinkA=4,
            shrinkB=4,
        )
    )


def draw_profile(ax):
    verts = [
        (0.095, 0.67),
        (0.074, 0.66),
        (0.060, 0.62),
        (0.058, 0.56),
        (0.057, 0.49),
        (0.071, 0.43),
        (0.089, 0.40),
        (0.090, 0.35),
        (0.080, 0.30),
        (0.073, 0.25),
        (0.145, 0.25),
        (0.139, 0.32),
        (0.128, 0.37),
        (0.116, 0.40),
        (0.134, 0.40),
        (0.151, 0.42),
        (0.159, 0.46),
        (0.144, 0.49),
        (0.156, 0.51),
        (0.143, 0.54),
        (0.151, 0.58),
        (0.137, 0.61),
        (0.151, 0.64),
        (0.145, 0.67),
        (0.112, 0.69),
        (0.095, 0.67),
    ]
    codes = [MplPath.MOVETO] + [MplPath.CURVE3] * (len(verts) - 2) + [MplPath.LINETO]
    ax.add_patch(PathPatch(MplPath(verts, codes), fill=False, lw=1.7, ec=INK, capstyle="round"))
    ax.text(0.105, 0.18, "nearby\nspeech", ha="center", va="center", fontsize=7.8, color=INK)


def draw_wave(ax):
    xs = [0.165 + i * 0.0046 for i in range(70)]
    for i, x in enumerate(xs):
        amp = 0.012 + 0.033 * abs(math.sin(i * 0.72)) * (0.35 + 0.65 * math.sin(i * 0.11) ** 2)
        y0 = 0.505 - amp / 2
        y1 = 0.505 + amp / 2
        ax.plot([x, x], [y0, y1], color=BLUE, lw=1.1, alpha=0.95)
    curve_x = [0.46 + i * 0.004 for i in range(28)]
    curve_y = [0.505 + 0.022 * math.sin(i * 0.42) for i in range(28)]
    ax.plot(curve_x, curve_y, color=BLUE, lw=1.5)
    for i in range(48):
        x = 0.33 + i * 0.0055
        y = 0.50 + 0.07 * math.sin(i * 1.31) * math.cos(i * 0.39)
        ax.add_patch(Circle((x, y), 0.0018, color=BLUE, alpha=0.45, lw=0))
    ax.text(0.295, 0.62, "speech waveform", ha="center", va="center", fontsize=6.9, color=BLUE)


def draw_drone(ax):
    cx, cy = 0.56, 0.56
    rotors = [(0.43, 0.70), (0.70, 0.70), (0.43, 0.40), (0.70, 0.40)]
    for rx, ry in rotors:
        ax.plot([cx, rx], [cy, ry], color=INK, lw=1.3)
        ax.add_patch(Circle((rx, ry), 0.035, fill=False, ec=INK, lw=1.3))
        ax.add_patch(Circle((rx, ry), 0.012, fc=LIGHT, ec=INK, lw=1.0))
        ax.plot([rx - 0.028, rx + 0.028], [ry, ry], color=MUTED, lw=1.0, alpha=0.7)
        ax.plot([rx, rx], [ry - 0.022, ry + 0.022], color=MUTED, lw=0.8, alpha=0.45)
        for j, radius in enumerate([0.055, 0.073, 0.091]):
            ax.add_patch(
                Arc(
                    (rx, ry),
                    radius,
                    radius * 0.72,
                    theta1=25,
                    theta2=155,
                    color=BLUE if j == 0 else MUTED,
                    lw=0.85,
                    linestyle=(0, (2, 3)),
                    alpha=0.65,
                )
            )
    ax.add_patch(FancyBboxPatch((cx - 0.055, cy - 0.045), 0.11, 0.09,
                                boxstyle="round,pad=0.010,rounding_size=0.025",
                                fc=LIGHT, ec=INK, lw=1.5))
    ax.add_patch(Rectangle((cx - 0.032, cy - 0.030), 0.064, 0.058, fc=TEAL_LIGHT, ec=TEAL, lw=1.25))
    ax.add_patch(Rectangle((cx - 0.011, cy - 0.010), 0.022, 0.020, fc=INK, ec=INK, lw=0.7))
    for k in range(6):
        ax.plot([cx - 0.026 + k * 0.010, cx - 0.026 + k * 0.010], [cy + 0.024, cy + 0.016], color=TEAL, lw=0.8)
        ax.plot([cx - 0.026 + k * 0.010, cx - 0.026 + k * 0.010], [cy - 0.024, cy - 0.016], color=TEAL, lw=0.8)
    ax.add_patch(Circle((cx + 0.045, cy - 0.058), 0.012, fc=LIGHT, ec=INK, lw=1.0))
    rounded(ax, cx - 0.052, cy - 0.128, 0.104, 0.056, "onboard\nAkouo layer", TEAL_LIGHT, TEAL, fs=5.85, lw=1.0)
    ax.text(0.61, 0.80, "rotor noise", ha="center", va="center", fontsize=7.4, color=MUTED)
    return cx, cy


def draw_events_and_boundary(ax):
    ax.text(0.47, 0.315, "intent events", ha="left", va="center", fontsize=7.8, color=INK, fontweight="bold")
    chips = [
        (0.47, "emergency", ORANGE_LIGHT, ORANGE),
        (0.585, "movement", GREEN_LIGHT, GREEN),
        (0.700, "unknown", GRAY_LIGHT, MUTED),
    ]
    for x, label, fc, ec in chips:
        rounded(ax, x, 0.205, 0.095, 0.075, label, fc, ec, fs=7.5, lw=1.1)
        ax.add_patch(Circle((x + 0.018, 0.242), 0.006, fc=ec, ec=ec, lw=0))
    arrow(ax, (0.56, 0.49), (0.52, 0.31), TEAL, lw=1.4, rad=-0.15)
    arrow(ax, (0.796, 0.242), (0.845, 0.242), PURPLE, lw=1.4)

    ax.add_patch(FancyBboxPatch((0.846, 0.145), 0.036, 0.22,
                                boxstyle="round,pad=0.006,rounding_size=0.018",
                                fc=PURPLE_LIGHT, ec=PURPLE, lw=1.5))
    ax.plot([0.864, 0.864], [0.165, 0.345], color=PURPLE, lw=3.0, solid_capstyle="round")
    ax.text(0.864, 0.425, "conservative\nsafety boundary", ha="center", va="center", fontsize=6.9, color=PURPLE, fontweight="bold")
    rounded(ax, 0.902, 0.198, 0.074, 0.088, "response\nmediated", "#F8F8F8", MUTED, fs=6.45, lw=1.0)
    arrow(ax, (0.882, 0.242), (0.902, 0.242), MUTED, lw=1.2, dashed=True)


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7.35, 3.45))
    clean(ax)
    draw_profile(ax)
    draw_wave(ax)
    cx, cy = draw_drone(ax)
    arrow(ax, (0.445, 0.505), (cx - 0.035, cy - 0.005), BLUE, lw=1.45, rad=-0.04)
    draw_events_and_boundary(ax)
    ax.text(
        0.03,
        0.06,
        "Speech is represented as intent events; UAV response is mediated by the boundary.",
        ha="left",
        va="center",
        fontsize=6.7,
        color=MUTED,
    )
    fig.savefig(PDF, bbox_inches="tight", pad_inches=0.04)
    fig.savefig(PNG, bbox_inches="tight", pad_inches=0.04, dpi=300)
    plt.close(fig)
    print(PDF)
    print(PNG)


if __name__ == "__main__":
    main()
