#!/usr/bin/env python3
"""Evaluate the w14 acoustic recognizer across deterministic rotor-noise SNRs.

This script is intentionally evaluation-only. It loads the existing processed
test split, the existing label encoder, and a fixed checkpoint, then writes
paper-traceable metrics for a rotor-noise robustness matrix.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/numba_cache")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import joblib
import numpy as np
import soundfile as sf
import tensorflow as tf
from scipy import signal
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)

from model import build_model
from model_config import (
    DURATION,
    FMAX,
    FMIN,
    HOP_LENGTH,
    MAX_FRAMES,
    N_FFT,
    N_MELS,
    SAMPLE_RATE,
    TOP_DB,
    get_model_kwargs,
)


TARGET_LEN = int(SAMPLE_RATE * DURATION)
INPUT_SHAPE = (N_MELS, MAX_FRAMES, 1)
LABELS = ("emergency", "movement", "unknown")
MODEL_ROLE = "offline_acoustic_reference_w14_preprocess_ext"
SNR_FORMULA = (
    "P_noise_target = P_speech / 10^(SNR_dB/10); "
    "scaled_noise = noise * sqrt(P_noise_target / P_noise); "
    "mixed = clean + scaled_noise"
)


@dataclass(frozen=True)
class Condition:
    name: str
    slug: str
    snr_db: float | None


CONDITIONS = (
    Condition("No added rotor noise", "clean", None),
    Condition("Rotor noise, 0 dB SNR", "snr_0db", 0.0),
    Condition("Rotor noise, -5 dB SNR", "snr_m5db", -5.0),
    Condition("Rotor noise, -10 dB SNR", "snr_m10db", -10.0),
    Condition("Rotor noise, -15 dB SNR", "snr_m15db", -15.0),
)


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def abs_path(raw: str | Path) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def require_path(path: Path, kind: str) -> None:
    if kind == "dir":
        ok = path.is_dir()
    elif kind == "file":
        ok = path.is_file()
    else:
        raise ValueError(f"Unknown path kind: {kind}")
    if not ok:
        raise FileNotFoundError(f"Required {kind} not found: {path}")


def run_git(args: list[str]) -> str:
    try:
        out = subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.STDOUT)
        return out.strip()
    except Exception as exc:  # pragma: no cover - best-effort manifest metadata
        return f"UNAVAILABLE: {exc}"


def json_dump(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=True, indent=2)
        f.write("\n")


def load_run_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def config_path(config: dict[str, Any], *keys: str) -> str | None:
    cur: Any = config
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return str(cur)


def validate_w14_config(
    config: dict[str, Any],
    weights_path: Path,
    processed_path: Path,
    encoder_path: Path,
    noise_dir: Path,
    model_profile: str,
) -> None:
    checks = {
        ("paths", "processed_data_path"): processed_path,
        ("paths", "encoder_path"): encoder_path,
        ("paths", "noise_source_dir"): noise_dir,
        ("paths", "student_ckpt"): weights_path,
    }
    for keys, expected in checks.items():
        raw = config_path(config, *keys)
        if raw is None:
            raise RuntimeError(f"Run config is missing {'.'.join(keys)}")
        actual = abs_path(raw)
        if actual != expected:
            raise RuntimeError(
                f"Run config mismatch for {'.'.join(keys)}: "
                f"config={actual}, requested={expected}"
            )

    cfg_profile = str(config.get("train", {}).get("student_model_profile", "")).strip().lower()
    if cfg_profile != str(model_profile).strip().lower():
        raise RuntimeError(
            f"Run config student_model_profile={cfg_profile!r} does not match "
            f"requested model_profile={model_profile!r}"
        )


def setup_tf() -> None:
    gpus = tf.config.list_physical_devices("GPU")
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)


def load_audio_1s(path: Path) -> np.ndarray:
    try:
        y, sr = sf.read(str(path), dtype="float32")
    except Exception as exc:
        raise RuntimeError(f"Failed to read audio file {path}: {exc}") from exc
    if y.ndim > 1:
        y = np.mean(y, axis=1)
    if sr != SAMPLE_RATE:
        gcd = int(np.gcd(sr, SAMPLE_RATE))
        y = signal.resample_poly(y, SAMPLE_RATE // gcd, sr // gcd).astype(np.float32)
    if len(y) < TARGET_LEN:
        y = np.pad(y, (0, TARGET_LEN - len(y)), mode="constant")
    elif len(y) > TARGET_LEN:
        y = y[:TARGET_LEN]
    return np.asarray(y, dtype=np.float32)


def list_noise_files(noise_dir: Path) -> list[Path]:
    files = sorted(
        p for p in noise_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in {".wav", ".flac", ".ogg", ".mp3"}
    )
    if not files:
        raise RuntimeError(f"No audio noise files found under {noise_dir}")
    return files


def load_noise_bank(noise_files: list[Path]) -> tuple[list[np.ndarray], list[dict[str, Any]]]:
    bank: list[np.ndarray] = []
    metadata: list[dict[str, Any]] = []
    for path in noise_files:
        info = sf.info(str(path))
        y = load_audio_1s(path)
        power = float(np.mean(np.square(y), dtype=np.float64))
        if power <= 1e-12:
            raise RuntimeError(f"Noise file has near-zero power: {path}")
        bank.append(y)
        metadata.append(
            {
                "path": rel(path),
                "sample_rate": int(info.samplerate),
                "frames": int(info.frames),
                "duration_sec": float(info.frames / info.samplerate) if info.samplerate else None,
                "loaded_len": int(y.shape[0]),
                "power": power,
            }
        )
    return bank, metadata


def deterministic_noise(noise_bank: list[np.ndarray], seed: int, cond_index: int, sample_index: int) -> np.ndarray:
    seq = np.random.SeedSequence([int(seed), int(cond_index), int(sample_index)])
    rng = np.random.default_rng(seq)
    noise = noise_bank[int(rng.integers(0, len(noise_bank)))]
    if len(noise) == TARGET_LEN:
        return noise
    if len(noise) < TARGET_LEN:
        return np.resize(noise, TARGET_LEN).astype(np.float32)
    start = int(rng.integers(0, len(noise) - TARGET_LEN + 1))
    return noise[start:start + TARGET_LEN].astype(np.float32)


def mix_at_snr(clean: np.ndarray, noise: np.ndarray, snr_db: float) -> tuple[np.ndarray, dict[str, Any]]:
    speech_power = float(np.mean(np.square(clean), dtype=np.float64))
    noise_power = float(np.mean(np.square(noise), dtype=np.float64))
    if speech_power <= 1e-12:
        raise RuntimeError("Encountered near-zero-power clean speech sample; cannot set SNR")
    if noise_power <= 1e-12:
        raise RuntimeError("Encountered near-zero-power noise sample; cannot set SNR")

    target_noise_power = speech_power / float(10.0 ** (snr_db / 10.0))
    noise_scale = float(np.sqrt(target_noise_power / noise_power))
    mixed = clean + noise * noise_scale
    peak_before = float(np.max(np.abs(mixed))) if mixed.size else 0.0
    normalized = False
    if peak_before > 1.0:
        mixed = mixed / peak_before
        normalized = True
    return mixed.astype(np.float32), {
        "speech_power": speech_power,
        "noise_power": noise_power,
        "target_noise_power": target_noise_power,
        "noise_scale": noise_scale,
        "peak_before_normalization": peak_before,
        "peak_normalized": normalized,
    }


class LogMelFrontend:
    def __init__(self) -> None:
        self.mel_weight = tf.signal.linear_to_mel_weight_matrix(
            num_mel_bins=N_MELS,
            num_spectrogram_bins=(N_FFT // 2 + 1),
            sample_rate=SAMPLE_RATE,
            lower_edge_hertz=FMIN,
            upper_edge_hertz=(FMAX if FMAX is not None else SAMPLE_RATE / 2.0),
            dtype=tf.float32,
        )

    def __call__(self, wavs: np.ndarray) -> tf.Tensor:
        wav = tf.convert_to_tensor(wavs, dtype=tf.float32)
        stft = tf.signal.stft(
            wav,
            frame_length=N_FFT,
            frame_step=HOP_LENGTH,
            fft_length=N_FFT,
            pad_end=False,
        )
        power = tf.square(tf.abs(stft))
        mel = tf.linalg.matmul(power, self.mel_weight)
        mel = tf.transpose(mel, perm=[0, 2, 1])
        mel = tf.maximum(mel, 1e-10)
        log_mel = 10.0 * tf.math.log(mel) / tf.math.log(tf.constant(10.0, dtype=tf.float32))
        ref = tf.reduce_max(log_mel, axis=[1, 2], keepdims=True)
        feat = tf.maximum(log_mel - ref, -TOP_DB)
        frame_count = int(feat.shape[2])
        if frame_count < MAX_FRAMES:
            feat = tf.pad(feat, [[0, 0], [0, 0], [0, MAX_FRAMES - frame_count]])
        else:
            feat = feat[:, :, :MAX_FRAMES]
        return tf.expand_dims(feat, axis=-1)


def load_test_split(processed_path: Path, limit: int | None) -> tuple[np.ndarray, np.ndarray]:
    data = np.load(str(processed_path), allow_pickle=True)
    required = {"X_test", "y_test"}
    missing = sorted(required - set(data.files))
    if missing:
        raise RuntimeError(f"Processed split missing required keys: {missing}")
    x_paths = np.asarray(data["X_test"])
    y_true = np.asarray(data["y_test"], dtype=np.int64)
    if x_paths.shape[0] != y_true.shape[0]:
        raise RuntimeError(f"X_test/y_test length mismatch: {x_paths.shape[0]} vs {y_true.shape[0]}")
    if limit is not None:
        x_paths = x_paths[:limit]
        y_true = y_true[:limit]
    resolved = np.array([str(abs_path(str(p))) for p in x_paths], dtype=object)
    missing_files = [p for p in resolved if not Path(str(p)).is_file()]
    if missing_files:
        preview = ", ".join(str(p) for p in missing_files[:5])
        raise RuntimeError(f"Missing {len(missing_files)} test audio files; first missing: {preview}")
    return resolved, y_true


def class_counts(y_true: np.ndarray, class_names: list[str]) -> dict[str, int]:
    return {name: int(np.sum(y_true == idx)) for idx, name in enumerate(class_names)}


def evaluate_condition(
    condition: Condition,
    cond_index: int,
    model: tf.keras.Model,
    frontend: LogMelFrontend,
    x_paths: np.ndarray,
    y_true: np.ndarray,
    noise_bank: list[np.ndarray],
    seed: int,
    batch_size: int,
    class_names: list[str],
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    y_pred_chunks: list[np.ndarray] = []
    conf_chunks: list[np.ndarray] = []
    max_peak_before = 0.0
    n_peak_normalized = 0
    n_mixed = 0

    for start in range(0, len(x_paths), batch_size):
        stop = min(start + batch_size, len(x_paths))
        wavs = np.empty((stop - start, TARGET_LEN), dtype=np.float32)
        for batch_i, sample_i in enumerate(range(start, stop)):
            clean = load_audio_1s(Path(str(x_paths[sample_i])))
            if condition.snr_db is None:
                wav = clean
            else:
                noise = deterministic_noise(noise_bank, seed, cond_index, sample_i)
                wav, mix_meta = mix_at_snr(clean, noise, float(condition.snr_db))
                n_mixed += 1
                max_peak_before = max(max_peak_before, float(mix_meta["peak_before_normalization"]))
                if mix_meta["peak_normalized"]:
                    n_peak_normalized += 1
            wavs[batch_i] = wav

        x_batch = frontend(wavs)
        proba = model(x_batch, training=False).numpy()
        y_pred_chunks.append(np.argmax(proba, axis=1).astype(np.int64))
        conf_chunks.append(np.max(proba, axis=1).astype(np.float32))
        if (stop % (batch_size * 20) == 0) or stop == len(x_paths):
            print(f"[eval] {condition.slug}: {stop}/{len(x_paths)}", flush=True)

    y_pred = np.concatenate(y_pred_chunks, axis=0)
    confidence = np.concatenate(conf_chunks, axis=0)

    cm = confusion_matrix(y_true, y_pred, labels=np.arange(len(class_names)))
    report = classification_report(
        y_true,
        y_pred,
        labels=np.arange(len(class_names)),
        target_names=class_names,
        output_dict=True,
        zero_division=0,
    )
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=np.arange(len(class_names)),
        zero_division=0,
    )

    emergency_idx = class_names.index("emergency")
    movement_idx = class_names.index("movement")
    unknown_idx = class_names.index("unknown")
    unknown_mask = y_true == unknown_idx
    unknown_false_events = int(np.sum(np.isin(y_pred[unknown_mask], [emergency_idx, movement_idx])))
    n_unknown = int(np.sum(unknown_mask))
    unknown_false_event_rate = float(unknown_false_events / n_unknown) if n_unknown else 0.0

    summary = {
        "condition": condition.name,
        "slug": condition.slug,
        "snr_db": condition.snr_db,
        "model_role": MODEL_ROLE,
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "emergency_recall": float(recall[emergency_idx]),
        "unknown_false_event_rate": unknown_false_event_rate,
        "n_total": int(len(y_true)),
        "n_emergency": int(np.sum(y_true == emergency_idx)),
        "n_movement": int(np.sum(y_true == movement_idx)),
        "n_unknown": n_unknown,
    }

    per_class = []
    for idx, name in enumerate(class_names):
        mask = y_true == idx
        per_class.append(
            {
                "condition": condition.name,
                "slug": condition.slug,
                "snr_db": condition.snr_db,
                "model_role": MODEL_ROLE,
                "class_label": name,
                "precision": float(precision[idx]),
                "recall": float(recall[idx]),
                "f1": float(f1[idx]),
                "support": int(support[idx]),
                "confidence_mean": float(np.mean(confidence[mask])) if np.any(mask) else 0.0,
                "confidence_median": float(np.median(confidence[mask])) if np.any(mask) else 0.0,
            }
        )

    details = {
        "condition": condition.name,
        "slug": condition.slug,
        "snr_db": condition.snr_db,
        "confusion_matrix": cm.astype(int).tolist(),
        "classification_report": report,
        "unknown_false_events": unknown_false_events,
        "mixing_stats": {
            "n_mixed": int(n_mixed),
            "n_peak_normalized": int(n_peak_normalized),
            "peak_normalized_fraction": float(n_peak_normalized / n_mixed) if n_mixed else 0.0,
            "max_peak_before_normalization": float(max_peak_before),
        },
        "confidence_summary": {
            "mean": float(np.mean(confidence)),
            "median": float(np.median(confidence)),
            "p05": float(np.quantile(confidence, 0.05)),
            "p95": float(np.quantile(confidence, 0.95)),
        },
    }
    return summary, per_class, details


def write_snr_matrix(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "condition",
        "snr_db",
        "model_role",
        "accuracy",
        "macro_f1",
        "emergency_recall",
        "unknown_false_event_rate",
        "n_total",
        "n_emergency",
        "n_movement",
        "n_unknown",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            out = dict(row)
            out["snr_db"] = "" if out["snr_db"] is None else out["snr_db"]
            for key in ["accuracy", "macro_f1", "emergency_recall", "unknown_false_event_rate"]:
                out[key] = f"{float(out[key]):.6f}"
            writer.writerow({k: out[k] for k in fieldnames})


def write_per_class(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "condition",
        "snr_db",
        "model_role",
        "class_label",
        "precision",
        "recall",
        "f1",
        "support",
        "confidence_mean",
        "confidence_median",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            out = dict(row)
            out["snr_db"] = "" if out["snr_db"] is None else out["snr_db"]
            for key in ["precision", "recall", "f1", "confidence_mean", "confidence_median"]:
                out[key] = f"{float(out[key]):.6f}"
            writer.writerow({k: out[k] for k in fieldnames})


def fmt_metric(value: float) -> str:
    return f"{value:.3f}"


def latex_rows(rows: list[dict[str, Any]]) -> str:
    return "\n".join(
        (
            f"{row['condition']} & {fmt_metric(row['accuracy'])} & "
            f"{fmt_metric(row['macro_f1'])} & {fmt_metric(row['emergency_recall'])} & "
            f"{fmt_metric(row['unknown_false_event_rate'])} \\\\"
        )
        for row in rows
    )


def markdown_table(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| Condition | Acc. | Macro F1 | Emerg. R | Unknown false event rate | n |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['condition']} | {fmt_metric(row['accuracy'])} | "
            f"{fmt_metric(row['macro_f1'])} | {fmt_metric(row['emergency_recall'])} | "
            f"{fmt_metric(row['unknown_false_event_rate'])} | {row['n_total']} |"
        )
    return "\n".join(lines)


def write_report(
    path: Path,
    rows: list[dict[str, Any]],
    manifest_path: Path,
    snr_csv: Path,
    per_class_csv: Path,
    cm_json: Path,
    args: argparse.Namespace,
    run_status: str,
    caveats: list[str],
) -> None:
    command = " ".join(shlex.quote(part) for part in sys.argv)
    shell_command = (
        "MPLCONFIGDIR=/tmp/matplotlib NUMBA_CACHE_DIR=/tmp/numba_cache "
        f"NUMBA_DISABLE_JIT=1 conda run -n drone python {command}"
    )
    env_lines = [
        f"MPLCONFIGDIR={os.environ.get('MPLCONFIGDIR', '')}",
        f"NUMBA_CACHE_DIR={os.environ.get('NUMBA_CACHE_DIR', '')}",
        f"NUMBA_DISABLE_JIT={os.environ.get('NUMBA_DISABLE_JIT', '')}",
    ]
    text = f"""# Rotor Noise SNR Matrix

Status: {run_status}

## Summary

This is an offline acoustic-recognizer robustness evaluation. It is not safety
validation, flight validation, or an ESP32 firmware test. Prediction uses argmax
over the model softmax output; no confidence threshold is tuned on the test set.

{markdown_table(rows)}

## Artifacts

- `snr_matrix.csv`: `{rel(snr_csv)}`
- `per_class_metrics.csv`: `{rel(per_class_csv)}`
- `confusion_matrices.json`: `{rel(cm_json)}`
- `run_manifest.json`: `{rel(manifest_path)}`
- `report.md`: `{rel(path)}`

## Exact Commands

Environment:

```bash
{chr(10).join(env_lines)}
```

Shell command:

```bash
{shell_command}
```

Python argv recorded by the evaluator:

```bash
{command}
```

## Inputs

- checkpoint: `{rel(abs_path(args.weights))}`
- run config: `{rel(abs_path(args.run_config))}`
- processed split: `{rel(abs_path(args.processed_data_path))}`
- label encoder: `{rel(abs_path(args.label_encoder))}`
- noise source directory: `{rel(abs_path(args.noise_source_dir))}`
- seed: `{args.seed}`
- SNR formula: `{SNR_FORMULA}`

## LaTeX Table Body

```latex
{latex_rows(rows)}
```

## Caveats / Failure Modes

"""
    for caveat in caveats:
        text += f"- {caveat}\n"
    path.write_text(text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weights", default="saved_models/weekly_drone_2026w14/preprocess_ext/student_kd_best.weights.h5")
    parser.add_argument("--run-config", default="weeklyresult/weekly_drone_2026w14/preprocess_ext/run_config.json")
    parser.add_argument("--processed-data-path", default="dataset/processed/data_paths.npz")
    parser.add_argument("--label-encoder", default="saved_models/label_encoder.joblib")
    parser.add_argument("--noise-source-dir", default="dataset/raw/tellonoise")
    parser.add_argument("--output-dir", default="weeklyresult/weekly_drone_2026w23/rotor_noise_snr_matrix_20260603")
    parser.add_argument("--model-profile", default="base")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--seed", type=int, default=20260603)
    parser.add_argument("--limit", type=int, default=None, help="Optional smoke-test limit; omit for full test split.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    weights_path = abs_path(args.weights)
    run_config_path = abs_path(args.run_config)
    processed_path = abs_path(args.processed_data_path)
    encoder_path = abs_path(args.label_encoder)
    noise_dir = abs_path(args.noise_source_dir)
    output_dir = abs_path(args.output_dir)

    require_path(weights_path, "file")
    require_path(run_config_path, "file")
    require_path(processed_path, "file")
    require_path(encoder_path, "file")
    require_path(noise_dir, "dir")
    output_dir.mkdir(parents=True, exist_ok=True)

    config = load_run_config(run_config_path)
    validate_w14_config(config, weights_path, processed_path, encoder_path, noise_dir, args.model_profile)

    setup_tf()

    label_encoder = joblib.load(str(encoder_path))
    class_names = [str(x) for x in label_encoder.classes_]
    if tuple(class_names) != LABELS:
        raise RuntimeError(f"Label encoder classes {class_names} do not match required labels {LABELS}")

    x_paths, y_true = load_test_split(processed_path, args.limit)
    counts = class_counts(y_true, class_names)
    expected_labels = set(range(len(class_names)))
    found_labels = set(int(x) for x in np.unique(y_true))
    if not found_labels.issubset(expected_labels):
        raise RuntimeError(f"Test labels contain ids outside label encoder range: {sorted(found_labels)}")

    noise_files = list_noise_files(noise_dir)
    noise_bank, noise_metadata = load_noise_bank(noise_files)

    print("[setup] building model", flush=True)
    model_kwargs = get_model_kwargs(args.model_profile)
    model = build_model(INPUT_SHAPE, len(class_names), **model_kwargs)
    model.load_weights(str(weights_path))
    print("[setup] weights loaded", flush=True)

    frontend = LogMelFrontend()

    matrix_rows: list[dict[str, Any]] = []
    per_class_rows: list[dict[str, Any]] = []
    cm_payload: dict[str, Any] = {"labels": class_names, "conditions": {}}

    for cond_index, condition in enumerate(CONDITIONS):
        print(f"[eval] condition={condition.name}", flush=True)
        summary, per_class, details = evaluate_condition(
            condition=condition,
            cond_index=cond_index,
            model=model,
            frontend=frontend,
            x_paths=x_paths,
            y_true=y_true,
            noise_bank=noise_bank,
            seed=args.seed,
            batch_size=int(args.batch_size),
            class_names=class_names,
        )
        matrix_rows.append(summary)
        per_class_rows.extend(per_class)
        cm_payload["conditions"][condition.slug] = details

    snr_csv = output_dir / "snr_matrix.csv"
    per_class_csv = output_dir / "per_class_metrics.csv"
    cm_json = output_dir / "confusion_matrices.json"
    manifest_path = output_dir / "run_manifest.json"
    report_path = output_dir / "report.md"

    write_snr_matrix(snr_csv, matrix_rows)
    write_per_class(per_class_csv, per_class_rows)
    json_dump(cm_json, cm_payload)

    full_split_n = int(np.load(str(processed_path), allow_pickle=True)["y_test"].shape[0])
    run_status = "preliminary for paper until manager approves full-split support policy"
    caveats = [
        "The matrix evaluates the offline acoustic reference recognizer only; it does not validate flight behavior or the safety bridge.",
        "The clean row is the clean held-out dataset split with no added local rotor noise, not a live no-rotor recording condition.",
        "The run uses the full X_test/y_test split. The older w14 classification_report_noisy.txt used 9984 samples because its Keras Sequence length floored by batch size.",
        "Rotor-noise mixtures use local dataset/raw/tellonoise clips selected by the w14 run config; source files are treated as local recorded/collected noise assets, not as flight validation.",
        "If peak amplitude exceeded 1.0 after mixing, the whole mixture was peak-normalized; this avoids clipping while preserving SNR ratio.",
    ]
    if args.limit is not None:
        run_status = "smoke test only; not paper-ready"
        caveats.append(f"Only the first {len(y_true)} examples were evaluated because --limit was set.")

    manifest = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "git": {
            "branch": run_git(["branch", "--show-current"]),
            "head": run_git(["rev-parse", "HEAD"]),
            "status_short_branch": run_git(["status", "--short", "--branch"]).splitlines(),
        },
        "model": {
            "model_role": MODEL_ROLE,
            "checkpoint_path": rel(weights_path),
            "checkpoint_abs_path": str(weights_path),
            "checkpoint_size_bytes": int(weights_path.stat().st_size),
            "run_config_path": rel(run_config_path),
            "model_profile": args.model_profile,
            "model_kwargs": model_kwargs,
            "frontend": "log-mel",
            "input_shape": list(INPUT_SHAPE),
            "use_stats_branch": False,
        },
        "dataset": {
            "processed_data_path": rel(processed_path),
            "processed_data_abs_path": str(processed_path),
            "test_split_keys": ["X_test", "y_test"],
            "label_encoder_path": rel(encoder_path),
            "label_encoder_abs_path": str(encoder_path),
            "labels": class_names,
            "n_total": int(len(y_true)),
            "full_x_test_n": full_split_n,
            "used_full_test_split": args.limit is None and len(y_true) == full_split_n,
            "class_counts": counts,
            "missing_test_files": 0,
        },
        "noise": {
            "source_dir": rel(noise_dir),
            "source_abs_dir": str(noise_dir),
            "source_description": "local dataset/raw/tellonoise noise clips referenced by the w14 run_config",
            "file_count": len(noise_files),
            "files": noise_metadata,
        },
        "mixing": {
            "seed": int(args.seed),
            "conditions": [
                {"name": c.name, "slug": c.slug, "snr_db": c.snr_db}
                for c in CONDITIONS
            ],
            "snr_formula": SNR_FORMULA,
            "noise_match_rule": "resample to 16 kHz if needed, then crop or tile to 1.0 s",
            "clipping_rule": "if mixed peak abs > 1.0, divide the whole mixed waveform by that peak",
            "condition_mixing_stats": {
                slug: cm_payload["conditions"][slug]["mixing_stats"]
                for slug in cm_payload["conditions"]
            },
        },
        "prediction": {
            "decision_rule": "argmax over softmax probabilities",
            "confidence_threshold": None,
            "threshold_tuned_on_test_set": False,
        },
        "commands": {
            "shell_command": (
                "MPLCONFIGDIR=/tmp/matplotlib NUMBA_CACHE_DIR=/tmp/numba_cache "
                f"NUMBA_DISABLE_JIT=1 conda run -n drone python "
                f"{' '.join(shlex.quote(part) for part in sys.argv)}"
            ),
            "python_argv": sys.argv,
            "python_argv_shell": " ".join(shlex.quote(part) for part in sys.argv),
            "environment": {
                "MPLCONFIGDIR": os.environ.get("MPLCONFIGDIR", ""),
                "NUMBA_CACHE_DIR": os.environ.get("NUMBA_CACHE_DIR", ""),
                "NUMBA_DISABLE_JIT": os.environ.get("NUMBA_DISABLE_JIT", ""),
            },
        },
        "outputs": {
            "snr_matrix_csv": rel(snr_csv),
            "per_class_metrics_csv": rel(per_class_csv),
            "confusion_matrices_json": rel(cm_json),
            "run_manifest_json": rel(manifest_path),
            "report_md": rel(report_path),
        },
        "status": run_status,
    }
    json_dump(manifest_path, manifest)
    write_report(
        report_path,
        matrix_rows,
        manifest_path,
        snr_csv,
        per_class_csv,
        cm_json,
        args,
        run_status,
        caveats,
    )

    print(f"[done] wrote {rel(output_dir)}", flush=True)
    print(latex_rows(matrix_rows), flush=True)


if __name__ == "__main__":
    main()
