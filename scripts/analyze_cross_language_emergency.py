#!/usr/bin/env python3

import argparse
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/numba_cache")

import librosa
import matplotlib.pyplot as plt
import numpy as np

SR = 16000
N_FFT = 1024
HOP = 256
N_MELS = 128
LANGS = ["english", "chinese", "japanese"]


def load_group(root: Path, lang: str, style: str):
    paths = sorted((root / lang / style).glob("*.wav"))
    waves = []
    for p in paths:
        try:
            y, _ = librosa.load(p, sr=SR, mono=True)
            waves.append(y.astype(np.float32))
        except Exception:
            continue
    return paths, waves


def avg_stft_db(waves):
    specs = []
    for y in waves:
        S = np.abs(librosa.stft(y, n_fft=N_FFT, hop_length=HOP, center=False)) ** 2
        S_db = librosa.power_to_db(S + 1e-12, ref=np.max)
        specs.append(S_db)
    return np.mean(np.stack(specs, axis=0), axis=0)


def avg_logmel_db(waves):
    specs = []
    for y in waves:
        M = librosa.feature.melspectrogram(y=y, sr=SR, n_fft=N_FFT, hop_length=HOP, n_mels=N_MELS, power=2.0)
        M_db = librosa.power_to_db(M + 1e-12, ref=np.max)
        specs.append(M_db)
    return np.mean(np.stack(specs, axis=0), axis=0)


def avg_energy_curve(waves):
    curves = []
    for y in waves:
        S = np.abs(librosa.stft(y, n_fft=N_FFT, hop_length=HOP, center=False)) ** 2
        curves.append(np.mean(S, axis=1))
    return np.mean(np.stack(curves, axis=0), axis=0)


def plot_lang_compare(out_png: Path, lang: str, em_waves, no_waves):
    stft_em = avg_stft_db(em_waves)
    stft_no = avg_stft_db(no_waves)
    mel_em = avg_logmel_db(em_waves)
    mel_no = avg_logmel_db(no_waves)

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes = axes.ravel()

    axes[0].imshow(stft_em, origin="lower", aspect="auto", cmap="magma")
    axes[0].set_title(f"{lang} emergency STFT")

    axes[1].imshow(stft_no, origin="lower", aspect="auto", cmap="magma")
    axes[1].set_title(f"{lang} normal STFT")

    axes[2].imshow(mel_em, origin="lower", aspect="auto", cmap="viridis")
    axes[2].set_title(f"{lang} emergency log-mel")

    axes[3].imshow(mel_no, origin="lower", aspect="auto", cmap="viridis")
    axes[3].set_title(f"{lang} normal log-mel")

    for ax in axes:
        ax.set_xlabel("Frame")
        ax.set_ylabel("Freq bin")

    fig.tight_layout()
    fig.savefig(out_png, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_placeholder(out_png: Path, title: str, message: str):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.axis("off")
    ax.set_title(title)
    ax.text(0.5, 0.5, message, ha="center", va="center")
    fig.tight_layout()
    fig.savefig(out_png, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", default="analysis/cross_language_emergency/standardized")
    parser.add_argument("--output-root", default="analysis/cross_language_emergency")
    args = parser.parse_args()

    input_root = Path(args.input_root)
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    stats = {}
    for lang in LANGS:
        em_paths, em_waves = load_group(input_root, lang, "emergency")
        no_paths, no_waves = load_group(input_root, lang, "normal")
        stats[lang] = {
            "emergency_count": len(em_waves),
            "normal_count": len(no_waves),
        }

        if lang in {"english", "chinese"}:
            out_png = output_root / f"{lang}_emergency_vs_normal.png"
            if len(em_waves) > 0 and len(no_waves) > 0:
                plot_lang_compare(out_png, lang, em_waves, no_waves)
            else:
                plot_placeholder(
                    out_png,
                    f"{lang} emergency vs normal",
                    "Insufficient standardized data for this language",
                )

    # Cross-language frequency band compare
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    fig2, ax2 = plt.subplots(figsize=(10, 5))

    for lang in LANGS:
        em_paths, em_waves = load_group(input_root, lang, "emergency")
        no_paths, no_waves = load_group(input_root, lang, "normal")
        if em_waves:
            em_curve = avg_energy_curve(em_waves)
            ax1.plot(em_curve, label=f"{lang}-emergency")
            ax2.plot(em_curve, label=f"{lang}-emergency")
        if no_waves:
            no_curve = avg_energy_curve(no_waves)
            ax1.plot(no_curve, linestyle="--", label=f"{lang}-normal")

    ax1.set_title("Cross-language emergency vs normal average frequency energy")
    ax1.set_xlabel("Frequency bin")
    ax1.set_ylabel("Mean power")
    ax1.grid(alpha=0.25)
    handles, labels = ax1.get_legend_handles_labels()
    if handles:
        ax1.legend(fontsize=8)
    fig1.tight_layout()
    fig1.savefig(output_root / "cross_language_band_compare.png", dpi=180, bbox_inches="tight")
    plt.close(fig1)

    ax2.set_title("Emergency-only average frequency energy")
    ax2.set_xlabel("Frequency bin")
    ax2.set_ylabel("Mean power")
    ax2.grid(alpha=0.25)
    handles, labels = ax2.get_legend_handles_labels()
    if handles:
        ax2.legend(fontsize=8)
    fig2.tight_layout()
    fig2.savefig(output_root / "avg_energy_curves.png", dpi=180, bbox_inches="tight")
    plt.close(fig2)

    findings_path = output_root / "findings.md"
    with open(findings_path, "w", encoding="utf-8") as f:
        f.write("# Cross-language Emergency Acoustic Findings\n\n")
        f.write("## Data Coverage\n\n")
        for lang in LANGS:
            f.write(
                f"- {lang}: emergency={stats[lang]['emergency_count']}, "
                f"normal={stats[lang]['normal_count']}\n"
            )

        f.write("\n## Observation Template\n\n")
        f.write("- Compare emergency vs normal per language on STFT/log-mel figures.\n")
        f.write("- Check whether emergency curves concentrate higher energy in consistent bands across languages.\n")
        f.write("- Convert repeatable patterns into future feature design (frequency-aware weighting/augmentation).\n")
        f.write("\n## Caveat\n\n")
        f.write("These observations are exploratory and should be validated with controlled train/eval experiments.\n")

    print(f"Saved: {findings_path}")


if __name__ == "__main__":
    main()
