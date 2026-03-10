#!/usr/bin/env python3

import argparse
import csv
import hashlib
import json
import os
import shutil
from collections import defaultdict

import numpy as np
import soundfile as sf
from scipy import signal


SAMPLE_RATE = 16000
DURATION = 1.0
TARGET_LEN = int(SAMPLE_RATE * DURATION)


EMERGENCY_WORDS = {
    "freeze",
    "no",
    "wow",
    "stop",
    "yes",
    "help",
    "hold",
    "get_back",
    "backward",
    "warning_alert",
}

MOVEMENT_WORDS = {
    "down",
    "follow",
    "go",
    "left",
    "right",
    "up",
    "forward",
    "go_forward",
    "turn_left",
    "turn_right",
    "rotate",
    "take_off",
    "fly",
    "on",
    "off",
}


def normalize_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def map_word_to_label(word: str):
    key = normalize_name(word)
    if key in EMERGENCY_WORDS:
        return "emergency"
    if key in MOVEMENT_WORDS:
        return "movement"
    return None


def canonical_audio_hash(wav_path: str) -> str:
    y, sr = sf.read(wav_path, dtype="float32")
    if y.ndim > 1:
        y = np.mean(y, axis=1)
    if sr != SAMPLE_RATE:
        y = signal.resample_poly(y, SAMPLE_RATE, sr).astype(np.float32)
    if len(y) < TARGET_LEN:
        y = np.pad(y, (0, TARGET_LEN - len(y)))
    else:
        y = y[:TARGET_LEN]
    return hashlib.sha1(y.tobytes()).hexdigest()


def ensure_unique_path(dst_dir: str, filename: str) -> str:
    stem, ext = os.path.splitext(filename)
    out = os.path.join(dst_dir, filename)
    idx = 1
    while os.path.exists(out):
        out = os.path.join(dst_dir, f"{stem}__{idx}{ext}")
        idx += 1
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="/Users/zilongzeng/Documents/data",
        help="Input root: <speaker>/<word>/*.wav",
    )
    parser.add_argument(
        "--output",
        default="result/speaker_isolation/cleaned_testset",
        help="Output root: <speaker>/<emergency|movement>/*.wav",
    )
    parser.add_argument(
        "--dedup-scope",
        choices=("speaker", "global"),
        default="speaker",
        help="Dedup by canonical audio hash within each speaker or globally.",
    )
    parser.add_argument(
        "--clear-output",
        action="store_true",
        help="Remove output directory before generating cleaned files.",
    )
    args = parser.parse_args()

    input_root = os.path.abspath(args.input)
    output_root = os.path.abspath(args.output)

    if not os.path.isdir(input_root):
        raise FileNotFoundError(f"Input directory not found: {input_root}")

    if args.clear_output and os.path.isdir(output_root):
        shutil.rmtree(output_root)

    os.makedirs(output_root, exist_ok=True)

    manifest_rows = []
    seen_hashes = set()
    summary = defaultdict(lambda: defaultdict(int))

    speaker_dirs = sorted(
        d for d in os.listdir(input_root) if os.path.isdir(os.path.join(input_root, d))
    )

    for speaker in speaker_dirs:
        speaker_dir = os.path.join(input_root, speaker)
        word_dirs = sorted(
            d for d in os.listdir(speaker_dir) if os.path.isdir(os.path.join(speaker_dir, d))
        )

        for word in word_dirs:
            label = map_word_to_label(word)
            word_dir = os.path.join(speaker_dir, word)

            for root, _, files in os.walk(word_dir):
                for fn in sorted(files):
                    if not fn.lower().endswith(".wav"):
                        continue

                    src = os.path.join(root, fn)
                    rel_src = os.path.relpath(src, input_root)
                    row = {
                        "speaker": speaker,
                        "word": word,
                        "label": label or "",
                        "src_relpath": rel_src,
                        "status": "",
                        "reason": "",
                        "audio_hash": "",
                        "dst_relpath": "",
                    }

                    if label is None:
                        row["status"] = "skip"
                        row["reason"] = "unmapped_word"
                        summary[speaker]["skip_unmapped"] += 1
                        manifest_rows.append(row)
                        continue

                    try:
                        audio_hash = canonical_audio_hash(src)
                    except Exception as exc:
                        row["status"] = "skip"
                        row["reason"] = f"load_error:{type(exc).__name__}"
                        summary[speaker]["skip_error"] += 1
                        manifest_rows.append(row)
                        continue

                    row["audio_hash"] = audio_hash
                    dedup_key = (speaker, audio_hash) if args.dedup_scope == "speaker" else audio_hash

                    if dedup_key in seen_hashes:
                        row["status"] = "skip"
                        row["reason"] = "duplicate_audio"
                        summary[speaker]["skip_duplicate"] += 1
                        manifest_rows.append(row)
                        continue

                    seen_hashes.add(dedup_key)
                    dst_dir = os.path.join(output_root, speaker, label)
                    os.makedirs(dst_dir, exist_ok=True)
                    dst_name = f"{normalize_name(word)}__{fn}"
                    dst = ensure_unique_path(dst_dir, dst_name)
                    shutil.copy2(src, dst)

                    row["status"] = "keep"
                    row["dst_relpath"] = os.path.relpath(dst, output_root)
                    summary[speaker][f"keep_{label}"] += 1
                    summary[speaker]["keep_total"] += 1
                    manifest_rows.append(row)

    manifest_path = os.path.join(output_root, "manifest.csv")
    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "speaker",
                "word",
                "label",
                "src_relpath",
                "status",
                "reason",
                "audio_hash",
                "dst_relpath",
            ],
        )
        writer.writeheader()
        writer.writerows(manifest_rows)

    summary_obj = {
        "input_root": input_root,
        "output_root": output_root,
        "dedup_scope": args.dedup_scope,
        "speakers": {spk: dict(vals) for spk, vals in summary.items()},
        "totals": {
            "keep_total": sum(v.get("keep_total", 0) for v in summary.values()),
            "skip_duplicate": sum(v.get("skip_duplicate", 0) for v in summary.values()),
            "skip_unmapped": sum(v.get("skip_unmapped", 0) for v in summary.values()),
            "skip_error": sum(v.get("skip_error", 0) for v in summary.values()),
            "manifest_rows": len(manifest_rows),
        },
        "manifest": manifest_path,
    }

    summary_path = os.path.join(output_root, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_obj, f, ensure_ascii=False, indent=2)

    print(json.dumps(summary_obj, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
