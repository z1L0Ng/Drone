#!/usr/bin/env python3
"""Render static paper diagram exports from the external-asset layouts."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle


ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "docs" / "paper_sensys2027" / "figures"

INK = "#1b2a34"
MUTED = "#5f6f7a"
BLUE = "#4477AA"
TEAL = "#228A8D"
ORANGE = "#D55E00"
GREEN = "#66A61E"
YELLOW = "#E8B25B"
LIGHT_BLUE = "#EAF2F8"
LIGHT_TEAL = "#EAF5F3"
LIGHT_ORANGE = "#FDECE6"
LIGHT_GREEN = "#EEF6E8"
PAPER = "#FBFBF7"
GRAY = "#D8DEE6"


def clean_ax(ax):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")


def box(ax, x, y, w, h, text, fc, ec=INK, fs=8.2, weight="normal", lw=1.1):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.012,rounding_size=0.024",
        linewidth=lw,
        facecolor=fc,
        edgecolor=ec,
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
        linespacing=1.12,
    )
    return patch


def arrow(ax, x1, y1, x2, y2, color=INK, lw=1.4, style="-|>"):
    ax.add_patch(
        FancyArrowPatch(
            (x1, y1),
            (x2, y2),
            arrowstyle=style,
            mutation_scale=10,
            linewidth=lw,
            color=color,
            shrinkA=5,
            shrinkB=5,
        )
    )


def title(ax, text, sub=None):
    ax.text(0.025, 0.965, text, ha="left", va="top", fontsize=11.4, fontweight="bold", color=INK)
    if sub:
        ax.text(0.025, 0.915, sub, ha="left", va="top", fontsize=7.6, color=MUTED)


def draw_uav(ax, cx, cy, s=1.0):
    ax.add_patch(FancyBboxPatch((cx - 0.035*s, cy - 0.018*s), 0.07*s, 0.036*s,
                                boxstyle="round,pad=0.005,rounding_size=0.012",
                                facecolor="#F7FAFC", edgecolor=INK, linewidth=1.0))
    for dx, dy in [(-0.075, 0.04), (0.075, 0.04), (-0.075, -0.04), (0.075, -0.04)]:
        ax.plot([cx, cx + dx*s], [cy, cy + dy*s], color=INK, lw=1.0)
        ax.add_patch(Circle((cx + dx*s, cy + dy*s), 0.026*s, fill=False, ec=INK, lw=1.0))
        ax.plot([cx + (dx - 0.02)*s, cx + (dx + 0.02)*s],
                [cy + dy*s, cy + dy*s], color=GRAY, lw=1.1)
    ax.add_patch(Rectangle((cx - 0.018*s, cy - 0.008*s), 0.036*s, 0.016*s,
                           facecolor=TEAL, edgecolor=INK, linewidth=0.8))


def system_architecture():
    fig, ax = plt.subplots(figsize=(7.65, 3.25))
    clean_ax(ax)
    title(
        ax,
        "Akouo voice safety-interaction architecture",
        "Speech is reported as an intent event, then mediated by a conservative boundary.",
    )

    # Physical context.
    ax.add_patch(Circle((0.09, 0.58), 0.03, fill=False, ec=INK, lw=1.2))
    ax.plot([0.09, 0.09], [0.55, 0.43], color=INK, lw=1.2)
    ax.plot([0.09, 0.055], [0.51, 0.46], color=INK, lw=1.2)
    ax.plot([0.09, 0.125], [0.51, 0.46], color=INK, lw=1.2)
    ax.text(0.09, 0.39, "nearby\nspeech", ha="center", va="top", fontsize=7.8, color=INK)
    draw_uav(ax, 0.23, 0.58, 0.9)
    for i, amp in enumerate([0.01, 0.018, 0.026]):
        ax.add_patch(Circle((0.16 + i * 0.025, 0.58), amp, fill=False, ec=BLUE, lw=1.0, alpha=0.7))
    ax.text(0.23, 0.39, "embedded board\nnear UAV", ha="center", va="top", fontsize=7.8, color=INK)

    stages = [
        (0.33, "onboard\ncapture", LIGHT_BLUE, BLUE),
        (0.465, "log-mel\ninteger inference", LIGHT_TEAL, TEAL),
        (0.60, "intent event\nlabel/conf./time", "#F6F2E8", YELLOW),
        (0.745, "host-side\nsafety-state bridge", LIGHT_GREEN, GREEN),
        (0.89, "Tello SDK\nboundary", LIGHT_ORANGE, ORANGE),
    ]
    prev_x = 0.27
    for x, text, fc, ec in stages:
        box(ax, x - 0.052, 0.55, 0.104, 0.135, text, fc, ec, fs=6.65)
        arrow(ax, prev_x, 0.617, x - 0.052, 0.617, ec, lw=1.4)
        prev_x = x + 0.052

    box(
        ax,
        0.52,
        0.205,
        0.29,
        0.135,
        "existing safety inputs\nobstacle / geofence /\nfailsafe / manual authority",
        "#F3F5F7",
        MUTED,
        fs=6.55,
    )
    arrow(ax, 0.665, 0.34, 0.745, 0.55, MUTED, lw=1.1)
    box(ax, 0.845, 0.205, 0.125, 0.135, "outcome\nrecord", "#F3F5F7", MUTED, fs=6.7)
    arrow(ax, 0.89, 0.55, 0.905, 0.34, ORANGE, lw=1.1)

    ax.text(
        0.025,
        0.1,
        "Takeaway: the recognizer is an event source; physical action remains behind a logged safety-state boundary.",
        ha="left",
        va="center",
        fontsize=8.0,
        color=INK,
    )
    fig.savefig(FIG / "system_architecture.pdf", bbox_inches="tight")
    plt.close(fig)


def recognizer_architecture():
    fig, ax = plt.subplots(figsize=(4.2, 2.9))
    clean_ax(ax)
    title(ax, "Recognizer contract", "Two model paths expose the same three intent events.")

    box(ax, 0.05, 0.62, 0.17, 0.11, "log-mel\nwindow", LIGHT_BLUE, BLUE, fs=7.0)
    box(ax, 0.30, 0.66, 0.21, 0.095, "conv frontend", "#F2F6FA", BLUE, fs=7.0)
    box(ax, 0.60, 0.66, 0.21, 0.095, "temporal\nencoder", "#F2F6FA", BLUE, fs=7.0)
    box(ax, 0.30, 0.45, 0.21, 0.095, "compact\nfrontend", LIGHT_TEAL, TEAL, fs=7.0)
    box(ax, 0.60, 0.45, 0.21, 0.095, "integer\nmodel", LIGHT_TEAL, TEAL, fs=7.0)
    box(ax, 0.05, 0.27, 0.17, 0.11, "intent\ncontract", "#F6F2E8", YELLOW, fs=7.0)
    box(ax, 0.30, 0.24, 0.56, 0.13, "emergency      movement      unknown", "#FDFDFB", INK, fs=7.0)

    ax.text(0.05, 0.79, "offline reference", ha="left", va="center", fontsize=7.3, color=BLUE, fontweight="bold")
    ax.text(0.05, 0.56, "embedded path", ha="left", va="center", fontsize=7.3, color=TEAL, fontweight="bold")
    arrow(ax, 0.22, 0.675, 0.30, 0.708, BLUE)
    arrow(ax, 0.51, 0.708, 0.60, 0.708, BLUE)
    arrow(ax, 0.81, 0.708, 0.81, 0.37, BLUE, lw=1.0)
    arrow(ax, 0.22, 0.675, 0.30, 0.497, TEAL)
    arrow(ax, 0.51, 0.497, 0.60, 0.497, TEAL)
    arrow(ax, 0.81, 0.497, 0.81, 0.37, TEAL, lw=1.0)
    arrow(ax, 0.22, 0.325, 0.30, 0.305, YELLOW)

    ax.text(
        0.05,
        0.1,
        "Takeaway: model capacity changes, but the control-facing event interface does not.",
        ha="left",
        va="center",
        fontsize=7.2,
        color=INK,
    )
    fig.savefig(FIG / "recognizer_architecture.pdf", bbox_inches="tight")
    plt.close(fig)


def user_study_evidence():
    fig, ax = plt.subplots(figsize=(7.75, 3.25))
    clean_ax(ax)
    title(
        ax,
        "Participant-level controlled prompt evidence",
        "The study records prompt trials, embedded/reference predictions, saved audio, and bridge-facing logs.",
    )

    # Panel labels.
    for label, x, y in [("A", 0.035, 0.79), ("B", 0.035, 0.36), ("C", 0.58, 0.79), ("D", 0.58, 0.36)]:
        ax.add_patch(Circle((x, y), 0.018, color=INK))
        ax.text(x, y, label, ha="center", va="center", fontsize=7.2, color="white", fontweight="bold")

    # A pipeline.
    ax.text(0.065, 0.81, "participant/session pipeline", fontsize=8.2, fontweight="bold", color=INK, va="center")
    ax_y = 0.64
    pipeline = [
        (0.06, "participant"),
        (0.18, "prompt\nlist"),
        (0.30, "embedded\ncapture/infer"),
        (0.44, "saved audio\n+ logs"),
    ]
    for x, txt in pipeline:
        box(ax, x, ax_y, 0.102, 0.105, txt, "#F7FAFC", BLUE, fs=6.55)
    for x1, x2 in [(0.162, 0.18), (0.282, 0.30), (0.402, 0.44)]:
        arrow(ax, x1, ax_y + 0.053, x2, ax_y + 0.053, BLUE, lw=1.0)

    # B matrix.
    ax.text(0.065, 0.38, "intent/keyword/repeat matrix", fontsize=8.2, fontweight="bold", color=INK, va="center")
    x0, y0 = 0.065, 0.18
    ax.add_patch(Rectangle((x0, y0), 0.44, 0.125, facecolor=PAPER, edgecolor=INK, linewidth=1.0))
    col_w = 0.44 / 4
    for i, label in enumerate(["participants", "3 intents", "5 keywords", "10 repeats"]):
        if i > 0:
            ax.plot([x0 + i * col_w, x0 + i * col_w], [y0, y0 + 0.125], color=GRAY, lw=0.8)
        ax.text(x0 + i * col_w + col_w / 2, y0 + 0.077, label, ha="center", va="center", fontsize=7.0, color=INK)
        ax.text(x0 + i * col_w + col_w / 2, y0 + 0.035, "XXX" if i == 0 else "", ha="center", va="center", fontsize=7.0, color=MUTED)
    ax.text(0.065, 0.12, "Prompt factors only: participant, intent, keyword, repeat.", fontsize=6.9, color=MUTED)

    # C results.
    ax.text(0.61, 0.81, "result summary", fontsize=8.2, fontweight="bold", color=INK, va="center")
    metrics = [
        ("accuracy", "XXX"),
        ("emergency recall", "XXX"),
        ("unknown false event rate", "XXX"),
        ("embedded/ref. disagreement", "XXX"),
    ]
    for i, (name, val) in enumerate(metrics):
        yy = 0.69 - i * 0.075
        ax.text(0.61, yy, name, ha="left", va="center", fontsize=7.4, color=INK)
        ax.text(0.94, yy, val, ha="right", va="center", fontsize=7.4, color=MUTED, fontweight="bold")
        ax.plot([0.61, 0.95], [yy - 0.032, yy - 0.032], color=GRAY, lw=0.7)

    # D log strip.
    ax.text(0.61, 0.38, "demo/log evidence strip", fontsize=8.2, fontweight="bold", color=INK, va="center")
    strip = [
        ("speech\nevent", BLUE),
        ("intent\nevent", TEAL),
        ("bridge\ndecision", GREEN),
        ("outcome\nlog", ORANGE),
    ]
    for i, (txt, color) in enumerate(strip):
        xx = 0.61 + i * 0.09
        box(ax, xx, 0.2, 0.072, 0.095, txt, "#F7FAFC", color, fs=6.6)
        if i < len(strip) - 1:
            arrow(ax, xx + 0.072, 0.247, xx + 0.09, 0.247, color, lw=0.9)

    ax.text(
        0.61,
        0.12,
        "Takeaway: participant variability is evaluated through controlled prompts and auditable logs.",
        fontsize=7.0,
        color=INK,
        ha="left",
        va="center",
    )

    fig.savefig(FIG / "user_study_evidence.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    system_architecture()
    recognizer_architecture()
    user_study_evidence()
    print(FIG / "system_architecture.pdf")
    print(FIG / "recognizer_architecture.pdf")
    print(FIG / "user_study_evidence.pdf")


if __name__ == "__main__":
    main()
