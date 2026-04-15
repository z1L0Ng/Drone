#!/usr/bin/env python3

import argparse
import csv
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Dict, List, Tuple

import joblib
import tensorflow as tf
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import soundfile as sf
from scipy import signal
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

sys.path.insert(0, os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "src"))
from model import build_model
from model_config import DURATION, FMAX, FMIN, HOP_LENGTH, MAX_FRAMES, N_FFT, N_MELS, SAMPLE_RATE, TOP_DB


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FINETUNE_SCRIPT = os.path.join(ROOT, "scripts", "run_finetune_logmel_kd.py")
TARGET_LEN = int(SAMPLE_RATE * DURATION)
INPUT_SHAPE = (N_MELS, MAX_FRAMES, 1)
PITCH_FMIN = 50.0
PITCH_FMAX = 500.0


@dataclass
class Candidate:
    name: str
    ckpt: str
    use_stats_branch: int
    stats_dim: int = 4
    stats_mlp_units: str = "32,16"
    fuse_units: int = 128
    fusion_mode: str = "concat"
    gate_units: int = 16


def _as_abs(path: str) -> str:
    return path if os.path.isabs(path) else os.path.abspath(os.path.join(ROOT, path))


def _run(cmd: List[str]) -> None:
    env = os.environ.copy()
    pid = str(os.getpid())
    mpl_dir = f"/tmp/matplotlib_{pid}"
    numba_dir = f"/tmp/numba_cache_{pid}"
    xdg_cache = f"/tmp/xdg_cache_{pid}"
    os.makedirs(mpl_dir, exist_ok=True)
    os.makedirs(numba_dir, exist_ok=True)
    os.makedirs(xdg_cache, exist_ok=True)
    env.setdefault("MPLCONFIGDIR", mpl_dir)
    env.setdefault("NUMBA_CACHE_DIR", numba_dir)
    env.setdefault("XDG_CACHE_HOME", xdg_cache)
    env.setdefault("NUMBA_DISABLE_JIT", "1")
    env.setdefault("TF_DETERMINISTIC_OPS", "1")
    env.setdefault("PYTHONUNBUFFERED", "1")
    subprocess.run(cmd, cwd=ROOT, check=True, env=env)


def _parse_classification_report(path: str) -> Dict[str, Dict[str, float]]:
    result: Dict[str, Dict[str, float]] = {}
    pattern = re.compile(
        r"^\s*(emergency|movement|unknown)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+(\d+)\s*$"
    )
    acc_pattern = re.compile(r"^\s*accuracy\s+([0-9.]+)\s+(\d+)\s*$")
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            m = pattern.match(line)
            if m:
                cls = m.group(1)
                result[cls] = {
                    "precision": float(m.group(2)),
                    "recall": float(m.group(3)),
                    "f1": float(m.group(4)),
                    "support": float(m.group(5)),
                }
                continue
            am = acc_pattern.match(line)
            if am:
                result["overall"] = {
                    "accuracy": float(am.group(1)),
                    "support": float(am.group(2)),
                }
    return result


def _safe_get(m: Dict[str, Dict[str, float]], cls: str, field: str) -> float:
    return float(m.get(cls, {}).get(field, 0.0))


def _normalize_label_name(name: str) -> str:
    return str(name).strip().lower().replace(" ", "_")


def _scan_testset(testset: str, class_names: List[str]) -> Tuple[np.ndarray, np.ndarray]:
    class_map = {_normalize_label_name(c): i for i, c in enumerate(class_names)}
    x_paths: List[str] = []
    y_true: List[int] = []
    for label_name in sorted(os.listdir(testset)):
        label_dir = os.path.join(testset, label_name)
        if not os.path.isdir(label_dir):
            continue
        key = _normalize_label_name(label_name)
        if key not in class_map:
            continue
        label_idx = class_map[key]
        for root, _, files in os.walk(label_dir):
            for fn in files:
                if fn.lower().endswith(".wav"):
                    x_paths.append(os.path.join(root, fn))
                    y_true.append(label_idx)
    if not x_paths:
        raise RuntimeError(f"No wav files found in testset={testset}")
    return np.array(x_paths), np.array(y_true)


def _load_audio_1s(path: str) -> np.ndarray:
    try:
        y, sr = sf.read(path, dtype="float32")
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


def _extract_logmel(y: np.ndarray) -> np.ndarray:
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


def _extract_stats(y: np.ndarray, stats_dim: int) -> np.ndarray:
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


def _parse_int_tuple(raw: str) -> Tuple[int, ...]:
    text = str(raw).strip()
    if not text:
        return tuple()
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if not parts:
        return tuple()
    return tuple(int(p) for p in parts)


def _run_inference(
    candidate: Candidate,
    testset: str,
    encoder: str,
    output_dir: str,
) -> Dict[str, float]:
    print(f"[inference] start {candidate.name}", flush=True)
    if os.path.isdir(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    le = joblib.load(encoder)
    class_names = list(le.classes_)
    x_paths, y_true = _scan_testset(testset, class_names)
    print(f"[inference] {candidate.name} samples={len(x_paths)}", flush=True)

    x_mel = np.empty((len(x_paths), *INPUT_SHAPE), dtype=np.float32)
    x_stats = np.empty((len(x_paths), int(candidate.stats_dim)), dtype=np.float32) if candidate.use_stats_branch else None
    for i, p in enumerate(x_paths):
        wav = _load_audio_1s(p)
        x_mel[i] = np.expand_dims(_extract_logmel(wav), axis=-1)
        if candidate.use_stats_branch:
            x_stats[i] = _extract_stats(wav, stats_dim=candidate.stats_dim)
        if (i + 1) % 200 == 0 or (i + 1) == len(x_paths):
            print(f"[inference] {candidate.name} feature {i + 1}/{len(x_paths)}", flush=True)
    model_kwargs = dict(
        num_layers=1,
        head_size=32,
        num_heads=4,
        ff_dim=256,
        dropout_rate=0.15,
        fnn_units=[128],
    )
    if candidate.use_stats_branch:
        model_kwargs.update(
            use_stats_branch=True,
            stats_dim=int(candidate.stats_dim),
            stats_mlp_units=_parse_int_tuple(candidate.stats_mlp_units),
            fuse_units=int(candidate.fuse_units),
            fusion_mode=str(candidate.fusion_mode).strip().lower(),
            gate_units=int(candidate.gate_units),
        )
    model = build_model(INPUT_SHAPE, len(class_names), **model_kwargs)
    print(f"[inference] {candidate.name} model built", flush=True)
    model.load_weights(candidate.ckpt)
    print(f"[inference] {candidate.name} weights loaded", flush=True)
    model_input = (x_mel, x_stats) if candidate.use_stats_branch else x_mel
    print(f"[inference] {candidate.name} predict start", flush=True)
    y_proba = model.predict(model_input, batch_size=32, verbose=0)
    print(f"[inference] {candidate.name} predict done", flush=True)
    y_pred = np.argmax(y_proba, axis=1)

    report_text = classification_report(y_true, y_pred, target_names=class_names, digits=4, zero_division=0)
    with open(os.path.join(output_dir, "classification_report.txt"), "w", encoding="utf-8") as f:
        f.write(report_text)

    cm = confusion_matrix(y_true, y_pred, labels=np.arange(len(class_names)))
    cm_path = os.path.join(output_dir, "confusion_matrix.png")
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=class_names, yticklabels=class_names)
    plt.title(f"{candidate.name} Confusion Matrix")
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.tight_layout()
    plt.savefig(cm_path, dpi=180, bbox_inches="tight")
    plt.close()

    np.savez(
        os.path.join(output_dir, "predictions.npz"),
        y_true=y_true,
        y_pred=y_pred,
        y_proba=y_proba,
        filepaths=x_paths,
    )
    print(f"[inference] {candidate.name} artifacts saved", flush=True)

    report = _parse_classification_report(os.path.join(output_dir, "classification_report.txt"))
    return {
        "setting": candidate.name,
        "checkpoint": candidate.ckpt,
        "use_stats_branch": int(candidate.use_stats_branch),
        "overall_acc": _safe_get(report, "overall", "accuracy"),
        "emergency_recall": _safe_get(report, "emergency", "recall"),
        "emergency_f1": _safe_get(report, "emergency", "f1"),
        "movement_recall": _safe_get(report, "movement", "recall"),
        "unknown_recall": _safe_get(report, "unknown", "recall"),
        "report_path": os.path.join(output_dir, "classification_report.txt"),
        "cm_path": os.path.join(output_dir, "confusion_matrix.png"),
    }


def _run_finetune(
    candidate: Candidate,
    testset: str,
    encoder: str,
    split_cache: str,
    output_dir: str,
    finetuned_ckpt_path: str,
    finetune_ratio: float,
    val_ratio: float,
    epochs: int,
    batch_size: int,
    lr: float,
    seed: int,
) -> Dict[str, float]:
    print(f"[finetune] start {candidate.name}", flush=True)
    if os.path.isdir(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.dirname(finetuned_ckpt_path), exist_ok=True)

    cmd = [
        sys.executable,
        FINETUNE_SCRIPT,
        "--testset",
        testset,
        "--encoder",
        encoder,
        "--weights",
        candidate.ckpt,
        "--finetuned-weights",
        finetuned_ckpt_path,
        "--output",
        output_dir,
        "--split-cache",
        split_cache,
        "--finetune-ratio",
        str(finetune_ratio),
        "--val-ratio",
        str(val_ratio),
        "--epochs",
        str(epochs),
        "--batch-size",
        str(batch_size),
        "--lr",
        str(lr),
        "--seed",
        str(seed),
        "--use-stats-branch",
        str(candidate.use_stats_branch),
        "--stats-dim",
        str(candidate.stats_dim),
        "--stats-mlp-units",
        candidate.stats_mlp_units,
        "--fuse-units",
        str(candidate.fuse_units),
        "--fusion-mode",
        candidate.fusion_mode,
        "--gate-units",
        str(candidate.gate_units),
    ]
    _run(cmd)
    print(f"[finetune] done {candidate.name}", flush=True)

    summary_csv = os.path.join(output_dir, "summary.csv")
    with open(summary_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        row = next(reader)
    acc_original = float(row["acc_original"])
    acc_finetuned = float(row["acc_finetuned"])

    report_original = _parse_classification_report(os.path.join(output_dir, "original", "classification_report.txt"))
    report_finetuned = _parse_classification_report(os.path.join(output_dir, "finetuned", "classification_report.txt"))

    em_rec_orig = _safe_get(report_original, "emergency", "recall")
    em_rec_ft = _safe_get(report_finetuned, "emergency", "recall")
    em_f1_orig = _safe_get(report_original, "emergency", "f1")
    em_f1_ft = _safe_get(report_finetuned, "emergency", "f1")

    return {
        "setting": candidate.name,
        "checkpoint": candidate.ckpt,
        "use_stats_branch": int(candidate.use_stats_branch),
        "acc_original": acc_original,
        "acc_finetuned": acc_finetuned,
        "delta_acc": acc_finetuned - acc_original,
        "emergency_recall_original": em_rec_orig,
        "emergency_recall_finetuned": em_rec_ft,
        "delta_emergency_recall": em_rec_ft - em_rec_orig,
        "emergency_f1_original": em_f1_orig,
        "emergency_f1_finetuned": em_f1_ft,
        "delta_emergency_f1": em_f1_ft - em_f1_orig,
        "movement_recall_finetuned": _safe_get(report_finetuned, "movement", "recall"),
        "unknown_recall_finetuned": _safe_get(report_finetuned, "unknown", "recall"),
        "split_cache": split_cache,
        "summary_csv": summary_csv,
        "report_original": os.path.join(output_dir, "original", "classification_report.txt"),
        "report_finetuned": os.path.join(output_dir, "finetuned", "classification_report.txt"),
        "cm_finetuned": os.path.join(output_dir, "finetuned", "confusion_matrix.png"),
    }


def _write_csv(path: str, rows: List[Dict[str, float]], fieldnames: List[str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def _pick_default_model(rows_ft: List[Dict[str, float]]) -> Dict[str, float]:
    return sorted(
        rows_ft,
        key=lambda r: (r["acc_finetuned"], r["emergency_f1_finetuned"], r["emergency_recall_finetuned"]),
        reverse=True,
    )[0]


def _pick_emergency_first(rows_ft: List[Dict[str, float]]) -> Dict[str, float]:
    return sorted(
        rows_ft,
        key=lambda r: (r["emergency_recall_finetuned"], r["emergency_f1_finetuned"], r["acc_finetuned"]),
        reverse=True,
    )[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--testset", default="/Users/zilongzeng/Research/Drone/testset")
    parser.add_argument("--encoder", default="saved_models/label_encoder.joblib")
    parser.add_argument("--output-root", default="result/weekly_wrapup_2026w15")
    parser.add_argument(
        "--split-cache",
        default="result/weekly_wrapup_2026w15/local_realworld_finetune/split_indices_testset.npz",
    )
    parser.add_argument("--finetune-ratio", type=float, default=0.3)
    parser.add_argument("--val-ratio", type=float, default=0.1)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-5)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    testset = _as_abs(args.testset)
    encoder = _as_abs(args.encoder)
    output_root = _as_abs(args.output_root)
    split_cache = _as_abs(args.split_cache)
    eval_root = os.path.join(output_root, "local_realworld_eval")
    finetune_root = os.path.join(output_root, "local_realworld_finetune")
    ckpt_root = os.path.join(finetune_root, "finetuned_ckpts")

    candidates = [
        Candidate(
            name="w14_ref_baseline",
            ckpt=_as_abs("saved_models/weekly_drone_2026w14/baseline/best_embed_kd/student_kd_best.weights.h5"),
            use_stats_branch=0,
        ),
        Candidate(
            name="w14_ref_preprocess_ext",
            ckpt=_as_abs("saved_models/weekly_drone_2026w14/preprocess_ext/student_kd_best.weights.h5"),
            use_stats_branch=0,
        ),
        Candidate(
            name="w15_run1_stats_fuse_only",
            ckpt=_as_abs("saved_models/weekly_drone_2026w15/stats_fuse_only/student_kd_best.weights.h5"),
            use_stats_branch=1,
            stats_dim=4,
            stats_mlp_units="32,16",
            fuse_units=128,
            fusion_mode="concat",
        ),
        Candidate(
            name="w15_run2_stats_laux_a010",
            ckpt=_as_abs("saved_models/weekly_drone_2026w15/stats_laux_a010/student_kd_best.weights.h5"),
            use_stats_branch=1,
            stats_dim=4,
            stats_mlp_units="32,16",
            fuse_units=128,
            fusion_mode="concat",
        ),
        Candidate(
            name="w15_run3_stats_laux_a020",
            ckpt=_as_abs("saved_models/weekly_drone_2026w15/stats_laux_a020/student_kd_best.weights.h5"),
            use_stats_branch=1,
            stats_dim=4,
            stats_mlp_units="32,16",
            fuse_units=128,
            fusion_mode="concat",
        ),
    ]

    missing = [c.ckpt for c in candidates if not os.path.exists(c.ckpt)]
    if missing:
        raise FileNotFoundError(f"Missing checkpoints: {missing}")

    os.makedirs(eval_root, exist_ok=True)
    os.makedirs(finetune_root, exist_ok=True)
    os.makedirs(ckpt_root, exist_ok=True)
    os.makedirs(os.path.dirname(split_cache), exist_ok=True)

    # Ensure one fresh shared split cache for this gate.
    if os.path.exists(split_cache):
        os.remove(split_cache)

    rows_infer: List[Dict[str, float]] = []
    rows_ft: List[Dict[str, float]] = []

    for c in candidates:
        infer_out = os.path.join(eval_root, c.name)
        finetune_out = os.path.join(finetune_root, c.name)
        finetuned_ckpt = os.path.join(ckpt_root, f"{c.name}.weights.h5")

        rows_infer.append(_run_inference(c, testset, encoder, infer_out))
        tf.keras.backend.clear_session()
        rows_ft.append(
            _run_finetune(
                c,
                testset=testset,
                encoder=encoder,
                split_cache=split_cache,
                output_dir=finetune_out,
                finetuned_ckpt_path=finetuned_ckpt,
                finetune_ratio=args.finetune_ratio,
                val_ratio=args.val_ratio,
                epochs=args.epochs,
                batch_size=args.batch_size,
                lr=args.lr,
                seed=args.seed,
            )
        )
        tf.keras.backend.clear_session()

    rows_infer = sorted(rows_infer, key=lambda r: (r["overall_acc"], r["emergency_f1"]), reverse=True)
    rows_ft = sorted(rows_ft, key=lambda r: (r["acc_finetuned"], r["emergency_f1_finetuned"]), reverse=True)

    infer_csv = os.path.join(output_root, "comparison_local_inference_2026w15.csv")
    finetune_csv = os.path.join(output_root, "comparison_local_finetune_2026w15.csv")
    note_md = os.path.join(output_root, "decision_local_gate_2026w15.md")

    _write_csv(
        infer_csv,
        rows_infer,
        fieldnames=[
            "setting",
            "checkpoint",
            "use_stats_branch",
            "overall_acc",
            "emergency_recall",
            "emergency_f1",
            "movement_recall",
            "unknown_recall",
            "report_path",
            "cm_path",
        ],
    )

    _write_csv(
        finetune_csv,
        rows_ft,
        fieldnames=[
            "setting",
            "checkpoint",
            "use_stats_branch",
            "acc_original",
            "acc_finetuned",
            "delta_acc",
            "emergency_recall_original",
            "emergency_recall_finetuned",
            "delta_emergency_recall",
            "emergency_f1_original",
            "emergency_f1_finetuned",
            "delta_emergency_f1",
            "movement_recall_finetuned",
            "unknown_recall_finetuned",
            "split_cache",
            "summary_csv",
            "report_original",
            "report_finetuned",
            "cm_finetuned",
        ],
    )

    best_default = _pick_default_model(rows_ft)
    best_emergency = _pick_emergency_first(rows_ft)
    preprocess_row = next((r for r in rows_ft if r["setting"] == "w14_ref_preprocess_ext"), None)
    best_acc = float(best_default["acc_finetuned"])
    keep_preprocess_mainline = False
    if preprocess_row is not None:
        keep_preprocess_mainline = float(preprocess_row["acc_finetuned"]) >= (best_acc - 0.005)

    w15_rows = [r for r in rows_ft if r["setting"].startswith("w15_")]
    w15_beats_w14 = False
    if w15_rows:
        best_w15 = sorted(
            w15_rows,
            key=lambda r: (r["acc_finetuned"], r["emergency_f1_finetuned"]),
            reverse=True,
        )[0]
        best_w14 = sorted(
            [r for r in rows_ft if r["setting"].startswith("w14_")],
            key=lambda r: (r["acc_finetuned"], r["emergency_f1_finetuned"]),
            reverse=True,
        )[0]
        w15_beats_w14 = (
            float(best_w15["acc_finetuned"]) > float(best_w14["acc_finetuned"])
            and float(best_w15["emergency_f1_finetuned"]) >= float(best_w14["emergency_f1_finetuned"])
        )
    else:
        best_w15 = None

    line1 = f"默认推荐模型: {best_default['setting']} (acc_ft={best_default['acc_finetuned']:.4f}, em_f1_ft={best_default['emergency_f1_finetuned']:.4f})"
    line2 = f"emergency-first 推荐模型: {best_emergency['setting']} (em_recall_ft={best_emergency['emergency_recall_finetuned']:.4f}, em_f1_ft={best_emergency['emergency_f1_finetuned']:.4f})"
    line3 = (
        "是否保留 w14 preprocess_ext 作为主线: "
        + ("保留（与最优差距<=0.5pp）" if keep_preprocess_mainline else "不作为主线，仅保留为参考基线")
    )
    line4 = "主要风险: Run1-Run3 来源训练使用 KD_REUSE_TEACHER=0（shape mismatch），存在系统性偏差；stats-branch 阈值与误报成本仍需校准。"
    line5 = (
        "下轮建议（new-arch teacher-student）: "
        + ("继续推进，并优先在修复 teacher reuse 后复现 top2。" if w15_beats_w14 else "先不扩大，优先修复 teacher reuse 与阈值校准，再决定是否继续扩大 new-arch。")
    )

    with open(note_md, "w", encoding="utf-8") as f:
        f.write("# Local Real-World Gate Decision (2026w15)\n\n")
        f.write(f"- Inference summary: `{infer_csv}`\n")
        f.write(f"- Finetune summary: `{finetune_csv}`\n")
        f.write(f"- Shared split cache: `{split_cache}`\n\n")
        f.write("## 5-Line Conclusion\n\n")
        f.write(f"1. {line1}\n")
        f.write(f"2. {line2}\n")
        f.write(f"3. {line3}\n")
        f.write(f"4. {line4}\n")
        f.write(f"5. {line5}\n")

    print(f"Saved: {infer_csv}")
    print(f"Saved: {finetune_csv}")
    print(f"Saved: {note_md}")
    print("5-line conclusion:")
    print(line1)
    print(line2)
    print(line3)
    print(line4)
    print(line5)


if __name__ == "__main__":
    main()
