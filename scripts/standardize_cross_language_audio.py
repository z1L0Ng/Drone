#!/usr/bin/env python3

import argparse
import csv
import os
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

TARGET_SR = 16000
TARGET_SEC = 1.0
TARGET_LEN = int(TARGET_SR * TARGET_SEC)
SUPPORTED_LANGS = {"english", "chinese", "japanese"}
SUPPORTED_STYLES = {"emergency", "normal"}


def standardize(wav_path: str) -> np.ndarray:
    y, _ = librosa.load(wav_path, sr=TARGET_SR, mono=True)
    if len(y) < TARGET_LEN:
        y = np.pad(y, (0, TARGET_LEN - len(y)))
    else:
        y = y[:TARGET_LEN]
    return y.astype(np.float32)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", default="local_data/cross_language")
    parser.add_argument("--output-root", default="analysis/cross_language_emergency/standardized")
    parser.add_argument("--metadata", default="analysis/cross_language_emergency/standardized_metadata.csv")
    args = parser.parse_args()

    input_root = Path(args.input_root)
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    Path(args.metadata).parent.mkdir(parents=True, exist_ok=True)

    rows = []
    kept = 0

    for lang_dir in sorted(input_root.glob("*")):
        if not lang_dir.is_dir():
            continue
        lang = lang_dir.name.lower()
        if lang not in SUPPORTED_LANGS:
            continue

        for style_dir in sorted(lang_dir.glob("*")):
            if not style_dir.is_dir():
                continue
            style = style_dir.name.lower()
            if style not in SUPPORTED_STYLES:
                continue

            wav_files = sorted(style_dir.rglob("*.wav"))
            for wav_path in wav_files:
                rel_stem = wav_path.stem
                out_dir = output_root / lang / style
                out_dir.mkdir(parents=True, exist_ok=True)
                out_path = out_dir / f"{rel_stem}.wav"

                try:
                    y = standardize(str(wav_path))
                    sf.write(str(out_path), y, TARGET_SR)
                    rms = float(np.sqrt(np.mean(np.square(y))) + 1e-12)
                    rows.append(
                        {
                            "src": str(wav_path),
                            "dst": str(out_path),
                            "language": lang,
                            "style": style,
                            "duration_sec": TARGET_SEC,
                            "sample_rate": TARGET_SR,
                            "rms": rms,
                            "status": "ok",
                        }
                    )
                    kept += 1
                except Exception as exc:
                    rows.append(
                        {
                            "src": str(wav_path),
                            "dst": "",
                            "language": lang,
                            "style": style,
                            "duration_sec": TARGET_SEC,
                            "sample_rate": TARGET_SR,
                            "rms": "",
                            "status": f"error:{exc}",
                        }
                    )

    with open(args.metadata, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["src", "dst", "language", "style", "duration_sec", "sample_rate", "rms", "status"],
        )
        w.writeheader()
        w.writerows(rows)

    print(f"Standardized files: {kept}")
    print(f"Saved: {args.metadata}")


if __name__ == "__main__":
    main()
