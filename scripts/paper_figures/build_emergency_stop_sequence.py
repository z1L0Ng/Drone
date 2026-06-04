#!/usr/bin/env python3
"""Build the three-panel emergency-stop demonstration photo figure."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib.pyplot as plt
from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[2]
FIG_DIR = ROOT / "docs" / "paper_sensys2027" / "figures"
SOURCE_DIR = FIG_DIR / "source" / "emergency_stop_sequence" / "ql"
OUT_PDF = FIG_DIR / "emergency_stop_sequence.pdf"
OUT_PNG = FIG_DIR / "emergency_stop_sequence.png"


PANELS = [
    {
        "label": "(a) Hovering",
        "path": SOURCE_DIR / "IMG_2455.HEIC.png",
        "crop": (160, 170, 2240, 1730),
    },
    {
        "label": "(b) Emergency",
        "path": SOURCE_DIR / "IMG_2452.HEIC.png",
        "crop": (520, 170, 2380, 1565),
    },
    {
        "label": "(c) Safe stop",
        "path": SOURCE_DIR / "IMG_2457.HEIC.png",
        "crop": (660, 470, 2060, 1520),
    },
]

INK = "#1F2933"


def load_panel(path: Path, crop: tuple[int, int, int, int]) -> Image.Image:
    image = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    return image.crop(crop)


def main() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )

    fig, axes = plt.subplots(1, 3, figsize=(7.05, 2.35))
    for ax, panel in zip(axes, PANELS, strict=True):
        image = load_panel(panel["path"], panel["crop"])
        ax.imshow(image)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(panel["label"], fontsize=8.0, color=INK, pad=3)
        for spine in ax.spines.values():
            spine.set_color("#C7D0D8")
            spine.set_linewidth(0.8)

    fig.subplots_adjust(left=0.012, right=0.988, top=0.87, bottom=0.03, wspace=0.035)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PDF, bbox_inches="tight")
    fig.savefig(OUT_PNG, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(OUT_PDF)
    print(OUT_PNG)


if __name__ == "__main__":
    main()
