#!/usr/bin/env python3

import argparse
import json
import os
from datetime import datetime

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/numba_cache")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import joblib
import librosa
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import soundfile as sf
from scipy import signal
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
try:
    import tensorflow as tf
except Exception as exc:  # pragma: no cover
    tf = None
    TF_IMPORT_ERROR = exc
else:
    TF_IMPORT_ERROR = None

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
    mel = librosa.feature.melspectrogram(
        y=y,
        sr=SAMPLE_RATE,
        n_fft=N_FFT,
        hop_length=HOP_LENGTH,
        center=False,
        n_mels=N_MELS,
        fmin=FMIN,
        fmax=FMAX,
        power=2.0,
    )
    feat = librosa.power_to_db(mel, ref=np.max, top_db=TOP_DB)
    if feat.shape[1] < MAX_FRAMES:
        feat = np.pad(feat, ((0, 0), (0, MAX_FRAMES - feat.shape[1])), mode="constant")
    else:
        feat = feat[:, :MAX_FRAMES]
    return feat.astype(np.float32)


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


def build_feature_tensor(filepaths: np.ndarray) -> np.ndarray:
    x = np.empty((len(filepaths), *INPUT_SHAPE), dtype=np.float32)
    for i, p in enumerate(filepaths):
        feat = extract_logmel(load_audio_1s(p))
        x[i] = np.expand_dims(feat, axis=-1)
    return x


def bool_flag(raw: str) -> bool:
    return str(raw).strip().lower() in {"1", "true", "yes", "y", "on"}


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
    args = parser.parse_args()

    if tf is None:
        raise SystemExit(f"TensorFlow is required for evaluation but unavailable: {TF_IMPORT_ERROR}")

    from model import build_model  # Imported lazily to avoid noisy traceback when TensorFlow is absent.

    setup_gpu()

    os.makedirs(args.output_dir, exist_ok=True)
    le = joblib.load(args.encoder)
    class_names = list(le.classes_)

    x_paths, y_true = scan_testset(args.testset, np.array(class_names))
    x = build_feature_tensor(x_paths)

    model_kwargs = get_model_kwargs(args.model_profile)
    model = build_model(INPUT_SHAPE, len(class_names), **model_kwargs)
    model.load_weights(args.weights)
    model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])

    y_proba = model.predict(x, batch_size=32, verbose=0)
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

    cm_path = os.path.join(args.output_dir, "confusion_matrix.png")
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=class_names, yticklabels=class_names)
    plt.title(f"{args.exp_id} Confusion Matrix")
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.tight_layout()
    plt.savefig(cm_path, dpi=180, bbox_inches="tight")
    plt.close()

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
