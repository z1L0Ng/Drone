#!/usr/bin/env python3

import argparse
import json
import os
from datetime import datetime
from typing import Tuple

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/numba_cache")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

try:
    import tensorflow as tf
except Exception as exc:  # pragma: no cover
    tf = None
    TF_IMPORT_ERROR = exc
else:
    TF_IMPORT_ERROR = None
import joblib
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import soundfile as sf
from scipy import signal
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

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
CENTER = False
PITCH_FMIN = 50.0
PITCH_FMAX = 500.0


def setup_gpu() -> None:
    if tf is None:
        return
    gpus = tf.config.list_physical_devices("GPU")
    if gpus:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)


def normalize_label_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def load_audio_1s(filepath: str) -> np.ndarray:
    try:
        y, sr = sf.read(filepath, dtype="float32")
        if y.ndim > 1:
            y = np.mean(y, axis=1)
        if sr != SAMPLE_RATE:
            y = signal.resample_poly(y, SAMPLE_RATE, sr).astype(np.float32)
        if len(y) < TARGET_LEN:
            y = np.pad(y, (0, TARGET_LEN - len(y)))
        else:
            y = y[:TARGET_LEN]
        return y.astype(np.float32)
    except Exception:
        return np.zeros(TARGET_LEN, dtype=np.float32)


def extract_logmel(y: np.ndarray) -> np.ndarray:
    wav = tf.convert_to_tensor(y, dtype=tf.float32)
    stft = tf.signal.stft(
        wav,
        frame_length=N_FFT,
        frame_step=HOP_LENGTH,
        fft_length=N_FFT,
        pad_end=False,
    )
    power = tf.abs(stft) ** 2
    mel_weight = tf.signal.linear_to_mel_weight_matrix(
        num_mel_bins=N_MELS,
        num_spectrogram_bins=(N_FFT // 2 + 1),
        sample_rate=SAMPLE_RATE,
        lower_edge_hertz=FMIN,
        upper_edge_hertz=(FMAX if FMAX is not None else SAMPLE_RATE / 2.0),
    )
    mel = tf.matmul(power, mel_weight)
    mel = tf.transpose(mel, perm=[1, 0])
    mel = tf.maximum(mel, 1e-10)
    log_mel = 10.0 * tf.math.log(mel) / tf.math.log(tf.constant(10.0, dtype=tf.float32))
    ref = tf.reduce_max(log_mel)
    feat = tf.maximum(log_mel - ref, -TOP_DB).numpy()
    if feat.shape[1] < MAX_FRAMES:
        feat = np.pad(feat, ((0, 0), (0, MAX_FRAMES - feat.shape[1])), mode="constant")
    else:
        feat = feat[:, :MAX_FRAMES]
    return feat.astype(np.float32)


def _framed_rms(y: np.ndarray) -> np.ndarray:
    n = len(y)
    if n <= 0:
        return np.zeros((0,), dtype=np.float32)
    starts = list(range(0, max(1, n - N_FFT + 1), HOP_LENGTH))
    if not starts:
        starts = [0]
    rms = np.zeros((len(starts),), dtype=np.float32)
    for i, s in enumerate(starts):
        frame = y[s:s + N_FFT]
        if frame.shape[0] < N_FFT:
            frame = np.pad(frame, (0, N_FFT - frame.shape[0]))
        rms[i] = float(np.sqrt(np.mean(np.square(frame), dtype=np.float64) + 1e-12))
    return rms


def _framed_pitch_autocorr(y: np.ndarray) -> np.ndarray:
    n = len(y)
    if n <= 0:
        return np.zeros((0,), dtype=np.float32)
    starts = list(range(0, max(1, n - N_FFT + 1), HOP_LENGTH))
    if not starts:
        starts = [0]
    pitch = np.full((len(starts),), np.nan, dtype=np.float32)
    lag_min = max(1, int(SAMPLE_RATE / max(PITCH_FMAX, 1.0)))
    lag_max = max(lag_min + 1, int(SAMPLE_RATE / max(PITCH_FMIN, 1.0)))
    window = np.hanning(N_FFT).astype(np.float32)
    for i, s in enumerate(starts):
        frame = y[s:s + N_FFT]
        if frame.shape[0] < N_FFT:
            frame = np.pad(frame, (0, N_FFT - frame.shape[0]))
        frame = (frame - np.mean(frame)) * window
        ac = np.correlate(frame, frame, mode="full")[N_FFT - 1:]
        if ac.size <= lag_min:
            continue
        upper = min(lag_max, ac.size - 1)
        ac0 = float(ac[0]) if ac.size > 0 else 0.0
        if ac0 <= 1e-12:
            continue
        ac[:lag_min] = 0.0
        if upper + 1 < ac.size:
            ac[upper + 1:] = 0.0
        lag = int(np.argmax(ac))
        peak = float(ac[lag])
        if lag <= 0 or peak / ac0 < 0.1:
            continue
        pitch[i] = float(SAMPLE_RATE / lag)
    return pitch


def extract_stats_features(y: np.ndarray, stats_dim: int) -> np.ndarray:
    rms = _framed_rms(y).astype(np.float32)
    energy_env_std = float(np.std(rms)) if rms.size > 0 else 0.0

    pitch = _framed_pitch_autocorr(y).astype(np.float32)

    valid_pitch = np.isfinite(pitch) & (pitch > 0.0)
    if np.any(valid_pitch):
        pitch_vals = pitch[valid_pitch]
        pitch_mean = float(np.mean(pitch_vals))
        pitch_std = float(np.std(pitch_vals))
    else:
        pitch_mean = 0.0
        pitch_std = 0.0

    pitch_energy_corr = 0.0
    if pitch.shape[0] == rms.shape[0]:
        idx = valid_pitch
        if np.sum(idx) >= 2:
            p = pitch[idx]
            e = rms[idx]
            if np.std(p) > 1e-8 and np.std(e) > 1e-8:
                pitch_energy_corr = float(np.corrcoef(p, e)[0, 1])

    stats = np.array(
        [
            pitch_mean,
            pitch_std,
            energy_env_std,
            np.clip(pitch_energy_corr, -1.0, 1.0),
        ],
        dtype=np.float32,
    )
    stats = np.nan_to_num(stats, nan=0.0, posinf=0.0, neginf=0.0)
    if int(stats_dim) == stats.shape[0]:
        return stats
    out = np.zeros((int(stats_dim),), dtype=np.float32)
    n = min(out.shape[0], stats.shape[0])
    out[:n] = stats[:n]
    return out


def scan_testset(test_data_dir: str, class_names: np.ndarray):
    class_map = {normalize_label_name(c): i for i, c in enumerate(class_names)}
    x_paths, y_true = [], []

    if not os.path.isdir(test_data_dir):
        raise FileNotFoundError(f"Testset not found: {test_data_dir}")

    for label_name in sorted(os.listdir(test_data_dir)):
        label_dir = os.path.join(test_data_dir, label_name)
        if not os.path.isdir(label_dir):
            continue
        key = normalize_label_name(label_name)
        if key not in class_map:
            continue
        label_idx = class_map[key]
        for root, _, files in os.walk(label_dir):
            for fn in files:
                if fn.lower().endswith(".wav"):
                    x_paths.append(os.path.join(root, fn))
                    y_true.append(label_idx)

    if not x_paths:
        raise RuntimeError("No valid wav files found under testset for known labels")

    return np.array(x_paths), np.array(y_true)


def build_feature_tensor(
    filepaths: np.ndarray,
    use_stats_branch: bool,
    stats_dim: int,
) -> np.ndarray | Tuple[np.ndarray, np.ndarray]:
    total = len(filepaths)
    print(f"[feature] building inputs for {total} files (stats_branch={int(use_stats_branch)})", flush=True)
    x_mel = np.empty((len(filepaths), *INPUT_SHAPE), dtype=np.float32)
    x_stats = np.empty((len(filepaths), int(stats_dim)), dtype=np.float32) if use_stats_branch else None
    for i, p in enumerate(filepaths):
        y = load_audio_1s(p)
        feat = extract_logmel(y)
        x_mel[i] = np.expand_dims(feat, axis=-1)
        if use_stats_branch:
            x_stats[i] = extract_stats_features(y, stats_dim=stats_dim)
        if (i + 1) % 200 == 0 or (i + 1) == total:
            print(f"[feature] {i + 1}/{total}", flush=True)
    return (x_mel, x_stats) if use_stats_branch else x_mel


def bool_flag(raw: str) -> bool:
    return str(raw).strip().lower() in {"1", "true", "yes", "y", "on"}


def parse_int_tuple(raw: str) -> Tuple[int, ...]:
    text = str(raw).strip()
    if not text:
        return tuple()
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if not parts:
        return tuple()
    return tuple(int(p) for p in parts)


def safe_get_class_metric(report_dict: dict, class_name: str, field: str) -> float:
    if class_name not in report_dict:
        return 0.0
    return float(report_dict[class_name].get(field, 0.0))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights", required=True)
    parser.add_argument("--encoder", default="saved_models/label_encoder.joblib")
    parser.add_argument("--testset", default="testset")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--model-profile", default="base")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--exp-id", required=True)
    parser.add_argument("--kd-variant", default="unknown")
    parser.add_argument("--aug-flag", default="false")
    parser.add_argument("--prewarm-flag", default="false")
    parser.add_argument("--link-best-model", action="store_true")
    parser.add_argument("--use-stats-branch", default="0")
    parser.add_argument("--stats-dim", type=int, default=4)
    parser.add_argument("--stats-mlp-units", default="32,16")
    parser.add_argument("--fuse-units", type=int, default=128)
    parser.add_argument("--fusion-mode", default="concat")
    parser.add_argument("--gate-units", type=int, default=16)
    args = parser.parse_args()

    if tf is None:
        raise SystemExit(f"TensorFlow is required for evaluation but unavailable: {TF_IMPORT_ERROR}")

    from model import build_model  # Imported lazily to avoid noisy traceback when TensorFlow is absent.

    setup_gpu()

    os.makedirs(args.output_dir, exist_ok=True)
    le = joblib.load(args.encoder)
    class_names = list(le.classes_)
    use_stats_branch = bool_flag(args.use_stats_branch)

    x_paths, y_true = scan_testset(args.testset, np.array(class_names))
    x = build_feature_tensor(
        x_paths,
        use_stats_branch=use_stats_branch,
        stats_dim=args.stats_dim,
    )

    model_kwargs = get_model_kwargs(args.model_profile)
    if use_stats_branch:
        model_kwargs.update(
            use_stats_branch=True,
            stats_dim=int(args.stats_dim),
            stats_mlp_units=parse_int_tuple(args.stats_mlp_units),
            fuse_units=int(args.fuse_units),
            fusion_mode=str(args.fusion_mode).strip().lower(),
            gate_units=int(args.gate_units),
        )
    model = build_model(INPUT_SHAPE, len(class_names), **model_kwargs)
    print("[eval] model built", flush=True)
    model.load_weights(args.weights)
    print("[eval] weights loaded", flush=True)

    print("[eval] start predict", flush=True)
    if isinstance(x, tuple):
        print(f"[eval] input tuple shapes: mel={x[0].shape}, stats={x[1].shape}", flush=True)
    else:
        print(f"[eval] input shape: {x.shape}", flush=True)
    y_proba = model.predict(x, batch_size=32, verbose=0)
    print("[eval] predict done", flush=True)
    y_pred = np.argmax(y_proba, axis=1)

    overall_acc = float(accuracy_score(y_true, y_pred))
    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))

    report_text = classification_report(y_true, y_pred, target_names=class_names, digits=4, zero_division=0)
    report_dict = classification_report(
        y_true,
        y_pred,
        target_names=class_names,
        output_dict=True,
        zero_division=0,
    )

    emergency_recall = safe_get_class_metric(report_dict, "emergency", "recall")
    emergency_f1 = safe_get_class_metric(report_dict, "emergency", "f1-score")
    movement_recall = safe_get_class_metric(report_dict, "movement", "recall")

    cm = confusion_matrix(y_true, y_pred, labels=np.arange(len(class_names)))
    print("[eval] metrics computed", flush=True)

    cm_path = os.path.join(args.output_dir, "confusion_matrix.png")
    print("[eval] plotting confusion matrix", flush=True)
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=class_names, yticklabels=class_names)
    plt.title(f"{args.exp_id} Confusion Matrix")
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.tight_layout()
    plt.savefig(cm_path, dpi=180, bbox_inches="tight")
    plt.close()
    print("[eval] confusion matrix saved", flush=True)

    with open(os.path.join(args.output_dir, "classification_report.txt"), "w", encoding="utf-8") as f:
        f.write(report_text)

    np.savez(
        os.path.join(args.output_dir, "predictions.npz"),
        y_true=y_true,
        y_pred=y_pred,
        y_proba=y_proba,
        filepaths=x_paths,
    )

    metrics = {
        "run_id": args.run_id,
        "exp_id": args.exp_id,
        "kd_variant": args.kd_variant,
        "aug_flag": bool_flag(args.aug_flag),
        "prewarm_flag": bool_flag(args.prewarm_flag),
        "overall_acc": overall_acc,
        "emergency_recall": emergency_recall,
        "emergency_f1": emergency_f1,
        "movement_recall": movement_recall,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "checkpoint": os.path.abspath(args.weights),
        "model_profile": args.model_profile,
        "use_stats_branch": use_stats_branch,
        "stats_dim": int(args.stats_dim),
        "stats_mlp_units": list(parse_int_tuple(args.stats_mlp_units)),
        "fuse_units": int(args.fuse_units),
        "fusion_mode": str(args.fusion_mode).strip().lower(),
        "gate_units": int(args.gate_units),
        "testset": os.path.abspath(args.testset),
        "num_samples": int(len(y_true)),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "class_metrics": report_dict,
        "cm_path": os.path.abspath(cm_path),
    }

    metrics_path = os.path.join(args.output_dir, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=True, indent=2)

    if args.link_best_model:
        target = os.path.abspath(args.weights)
        link_path = os.path.join(args.output_dir, "best_model.ckpt")
        try:
            if os.path.lexists(link_path):
                os.remove(link_path)
            os.symlink(target, link_path)
        except Exception:
            pass

    summary_path = os.path.join(args.output_dir, "summary.md")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"# {args.exp_id} Summary\n\n")
        f.write(f"- run_id: `{args.run_id}`\n")
        f.write(f"- checkpoint: `{os.path.abspath(args.weights)}`\n")
        f.write(f"- overall_acc: `{overall_acc:.4f}`\n")
        f.write(f"- emergency_recall: `{emergency_recall:.4f}`\n")
        f.write(f"- emergency_f1: `{emergency_f1:.4f}`\n")
        f.write(f"- movement_recall: `{movement_recall:.4f}`\n")
        f.write(f"- confusion_matrix: `{cm_path}`\n")

    print(f"Saved: {metrics_path}")
    print(f"Saved: {summary_path}")
    print(f"Saved: {cm_path}")


if __name__ == "__main__":
    main()
