#!/usr/bin/env python3

import os
import argparse
import random
from typing import Tuple
import numpy as np
import tensorflow as tf
import joblib
import soundfile as sf
from scipy import signal
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics import confusion_matrix, classification_report, accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.utils import class_weight

import sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

from model import build_model
from model_config import MODEL_KWARGS
from keras.optimizers import Adam
from keras.callbacks import ModelCheckpoint, EarlyStopping


# -------------------------
# Audio / frontend params
# -------------------------
SAMPLE_RATE = 16000
DURATION = 1.0
TARGET_LEN = int(SAMPLE_RATE * DURATION)

N_MELS = 256
N_FFT = 1024
HOP_LENGTH = 512
FMIN = 50
FMAX = None
TOP_DB = 80.0
MAX_FRAMES = int(DURATION * SAMPLE_RATE / HOP_LENGTH) + 1
INPUT_SHAPE = (N_MELS, MAX_FRAMES, 1)
CENTER = False
PITCH_FMIN = 50.0
PITCH_FMAX = 500.0


def setup_gpu():
    gpus = tf.config.list_physical_devices("GPU")
    if gpus:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        print(f"GPU ready: {len(gpus)} devices")
    else:
        print("No GPU detected, using CPU")


def setup_reproducibility(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    tf.keras.utils.set_random_seed(seed)
    try:
        tf.config.experimental.enable_op_determinism()
    except Exception:
        pass


def normalize_label_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def load_audio_1s(filepath):
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


def extract_logmel(y):
    wav = tf.convert_to_tensor(y, dtype=tf.float32)
    stft = tf.signal.stft(
        wav,
        frame_length=N_FFT,
        frame_step=HOP_LENGTH,
        fft_length=N_FFT,
        pad_end=False,
    )
    power = tf.abs(stft) ** 2  # [time, freq]

    mel_weight = tf.signal.linear_to_mel_weight_matrix(
        num_mel_bins=N_MELS,
        num_spectrogram_bins=(N_FFT // 2 + 1),
        sample_rate=SAMPLE_RATE,
        lower_edge_hertz=FMIN,
        upper_edge_hertz=(FMAX if FMAX is not None else SAMPLE_RATE / 2.0),
    )
    mel = tf.matmul(power, mel_weight)  # [time, mel]
    mel = tf.transpose(mel, perm=[1, 0])  # [mel, time]

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


def scan_testset(test_data_dir, class_names):
    if not os.path.isdir(test_data_dir):
        raise ValueError(f"Test data directory not found: {test_data_dir}")

    class_map = {normalize_label_name(c): i for i, c in enumerate(class_names)}
    x_all = []
    y_all = []

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
                    x_all.append(os.path.join(root, fn))
                    y_all.append(label_idx)

    return np.array(x_all), np.array(y_all)


def build_feature_tensor(filepaths, use_stats_branch=False, stats_dim=4):
    x_mel = np.empty((len(filepaths), *INPUT_SHAPE), dtype=np.float32)
    x_stats = np.empty((len(filepaths), int(stats_dim)), dtype=np.float32) if use_stats_branch else None
    for i, p in enumerate(filepaths):
        y = load_audio_1s(p)
        feat = extract_logmel(y)
        x_mel[i] = np.expand_dims(feat, axis=-1)
        if use_stats_branch:
            x_stats[i] = extract_stats_features(y, stats_dim=stats_dim)
    return (x_mel, x_stats) if use_stats_branch else x_mel


class FinetuneDataGenerator(tf.keras.utils.Sequence):
    def __init__(
        self,
        filepaths,
        labels,
        batch_size,
        num_classes,
        seed=42,
        shuffle=True,
        use_stats_branch=False,
        stats_dim=4,
    ):
        self.filepaths = filepaths
        self.labels = labels
        self.batch_size = batch_size
        self.num_classes = num_classes
        self.shuffle = shuffle
        self.use_stats_branch = bool(use_stats_branch)
        self.stats_dim = int(stats_dim)
        self.rng = np.random.default_rng(seed)
        self.indexes = np.arange(len(self.filepaths))
        if self.shuffle:
            self.rng.shuffle(self.indexes)

    def __len__(self):
        return int(np.ceil(len(self.filepaths) / self.batch_size))

    def __getitem__(self, index):
        batch_idx = self.indexes[index * self.batch_size:(index + 1) * self.batch_size]
        bsz = len(batch_idx)

        x_mel = np.empty((bsz, *INPUT_SHAPE), dtype=np.float32)
        x_stats = np.empty((bsz, self.stats_dim), dtype=np.float32) if self.use_stats_branch else None
        y = np.empty(bsz, dtype=np.int32)

        for i, idx in enumerate(batch_idx):
            wav = load_audio_1s(self.filepaths[idx])
            feat = extract_logmel(wav)
            x_mel[i] = np.expand_dims(feat, axis=-1)
            if self.use_stats_branch:
                x_stats[i] = extract_stats_features(wav, stats_dim=self.stats_dim)
            y[i] = self.labels[idx]

        x = (x_mel, x_stats) if self.use_stats_branch else x_mel
        return x, tf.keras.utils.to_categorical(y, num_classes=self.num_classes)

    def on_epoch_end(self):
        if self.shuffle:
            self.rng.shuffle(self.indexes)


def save_eval(output_dir, y_true, y_pred, y_proba, class_names, title, meta=None):
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "classification_report.txt"), "w", encoding="utf-8") as f:
        f.write(f"{title}\n")
        f.write("=" * 60 + "\n")
        if meta:
            for k, v in meta.items():
                f.write(f"{k}: {v}\n")
            f.write("\n")
        f.write(classification_report(y_true, y_pred, target_names=[str(x) for x in class_names], digits=4))
        f.write(f"\n\nAccuracy: {accuracy_score(y_true, y_pred):.4f}\n")

    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=class_names, yticklabels=class_names)
    plt.title(f"{title} - Confusion Matrix")
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "confusion_matrix.png"), dpi=150, bbox_inches="tight")
    plt.close()

    np.savez(
        os.path.join(output_dir, "predictions.npz"),
        y_true=y_true,
        y_pred=y_pred,
        y_proba=y_proba,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--testset", default="testset")
    parser.add_argument("--encoder", default="saved_models/label_encoder.joblib")
    parser.add_argument("--weights", default="saved_models/logmel_kd/student_kd_best.weights.h5")
    parser.add_argument("--finetuned-weights", default="saved_models/logmel_kd/finetuned_best.weights.h5")
    parser.add_argument("--output", default="result/finetune/logmel_kd")
    parser.add_argument("--split-cache", default="result/finetune/logmel_kd_split_indices.npz")
    parser.add_argument("--finetune-ratio", type=float, default=0.3)
    parser.add_argument("--val-ratio", type=float, default=0.1)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--use-stats-branch", default="0")
    parser.add_argument("--stats-dim", type=int, default=4)
    parser.add_argument("--stats-mlp-units", default="32,16")
    parser.add_argument("--fuse-units", type=int, default=128)
    parser.add_argument("--fusion-mode", default="concat")
    parser.add_argument("--gate-units", type=int, default=16)
    args = parser.parse_args()

    setup_reproducibility(args.seed)
    setup_gpu()

    le = joblib.load(args.encoder)
    class_names = le.classes_
    num_classes = len(class_names)
    use_stats_branch = bool_flag(args.use_stats_branch)

    x_all, y_all = scan_testset(args.testset, class_names)
    print(f"Loaded testset: {len(x_all)} samples")
    if len(x_all) == 0:
        raise RuntimeError("No samples found in testset for known labels")

    test_ratio = 1.0 - (args.finetune_ratio + args.val_ratio)
    if test_ratio <= 0:
        raise ValueError("finetune_ratio + val_ratio must be < 1.0")

    if os.path.exists(args.split_cache):
        cache = np.load(args.split_cache, allow_pickle=True)
        idx_finetune = cache["idx_finetune"]
        idx_val = cache["idx_val"]
        idx_test = cache["idx_test"]
        print(f"Loaded cached split: {args.split_cache}")
    else:
        _, _, _, _, idx_temp, idx_test = train_test_split(
            x_all,
            y_all,
            np.arange(len(x_all)),
            test_size=test_ratio,
            stratify=y_all,
            random_state=args.seed,
        )

        val_ratio_adj = args.val_ratio / (args.finetune_ratio + args.val_ratio)
        _, _, _, _, idx_finetune, idx_val = train_test_split(
            x_all[idx_temp],
            y_all[idx_temp],
            idx_temp,
            test_size=val_ratio_adj,
            stratify=y_all[idx_temp],
            random_state=args.seed,
        )

        os.makedirs(os.path.dirname(args.split_cache), exist_ok=True)
        np.savez(args.split_cache, idx_finetune=idx_finetune, idx_val=idx_val, idx_test=idx_test)
        print(f"Saved split cache: {args.split_cache}")

    x_finetune, y_finetune = x_all[idx_finetune], y_all[idx_finetune]
    x_val, y_val = x_all[idx_val], y_all[idx_val]
    x_test, y_test = x_all[idx_test], y_all[idx_test]

    print(f"Finetune/Val/Test: {len(x_finetune)}/{len(x_val)}/{len(x_test)}")

    x_test_features = build_feature_tensor(
        x_test,
        use_stats_branch=use_stats_branch,
        stats_dim=args.stats_dim,
    )

    model_kwargs = dict(MODEL_KWARGS)
    if use_stats_branch:
        model_kwargs.update(
            use_stats_branch=True,
            stats_dim=int(args.stats_dim),
            stats_mlp_units=parse_int_tuple(args.stats_mlp_units),
            fuse_units=int(args.fuse_units),
            fusion_mode=str(args.fusion_mode).strip().lower(),
            gate_units=int(args.gate_units),
        )

    model_original = build_model(INPUT_SHAPE, num_classes, **model_kwargs)
    model_original.load_weights(args.weights)
    y_proba_original = model_original.predict(x_test_features, verbose=0)
    y_pred_original = np.argmax(y_proba_original, axis=1)
    acc_original = accuracy_score(y_test, y_pred_original)
    print(f"Original accuracy: {acc_original:.4f}")

    model_finetuned = build_model(INPUT_SHAPE, num_classes, **model_kwargs)
    model_finetuned.load_weights(args.weights)
    model_finetuned.compile(
        optimizer=Adam(learning_rate=args.lr),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    train_gen = FinetuneDataGenerator(
        x_finetune,
        y_finetune,
        args.batch_size,
        num_classes,
        seed=args.seed,
        shuffle=True,
        use_stats_branch=use_stats_branch,
        stats_dim=args.stats_dim,
    )
    val_gen = FinetuneDataGenerator(
        x_val,
        y_val,
        args.batch_size,
        num_classes,
        seed=args.seed,
        shuffle=False,
        use_stats_branch=use_stats_branch,
        stats_dim=args.stats_dim,
    )

    cls_w = class_weight.compute_class_weight("balanced", classes=np.unique(y_finetune), y=y_finetune)
    cls_w = dict(enumerate(cls_w))

    os.makedirs(os.path.dirname(args.finetuned_weights), exist_ok=True)
    callbacks = [
        ModelCheckpoint(
            args.finetuned_weights,
            save_best_only=True,
            monitor="val_accuracy",
            save_weights_only=True,
            verbose=1,
        ),
        EarlyStopping(
            patience=5,
            restore_best_weights=True,
            monitor="val_accuracy",
            verbose=1,
        ),
    ]

    model_finetuned.fit(
        train_gen,
        validation_data=val_gen,
        epochs=args.epochs,
        callbacks=callbacks,
        class_weight=cls_w,
        verbose=1,
    )

    model_finetuned.load_weights(args.finetuned_weights)
    y_proba_finetuned = model_finetuned.predict(x_test_features, verbose=0)
    y_pred_finetuned = np.argmax(y_proba_finetuned, axis=1)
    acc_finetuned = accuracy_score(y_test, y_pred_finetuned)
    print(f"Finetuned accuracy: {acc_finetuned:.4f}")
    print(f"Delta: {acc_finetuned - acc_original:+.4f}")

    out_orig = os.path.join(args.output, "original")
    out_ft = os.path.join(args.output, "finetuned")

    save_eval(
        out_orig,
        y_test,
        y_pred_original,
        y_proba_original,
        class_names,
        title="LogMel KD Original",
        meta={
            "weights": args.weights,
            "test_samples": len(x_test),
            "use_stats_branch": int(use_stats_branch),
            "stats_dim": int(args.stats_dim),
            "stats_mlp_units": list(parse_int_tuple(args.stats_mlp_units)),
            "fuse_units": int(args.fuse_units),
            "fusion_mode": str(args.fusion_mode).strip().lower(),
            "gate_units": int(args.gate_units),
        },
    )
    save_eval(
        out_ft,
        y_test,
        y_pred_finetuned,
        y_proba_finetuned,
        class_names,
        title="LogMel KD Finetuned",
        meta={
            "base_weights": args.weights,
            "finetuned_weights": args.finetuned_weights,
            "finetune_samples": len(x_finetune),
            "val_samples": len(x_val),
            "test_samples": len(x_test),
            "epochs": args.epochs,
            "lr": args.lr,
            "use_stats_branch": int(use_stats_branch),
            "stats_dim": int(args.stats_dim),
            "stats_mlp_units": list(parse_int_tuple(args.stats_mlp_units)),
            "fuse_units": int(args.fuse_units),
            "fusion_mode": str(args.fusion_mode).strip().lower(),
            "gate_units": int(args.gate_units),
        },
    )

    summary_path = os.path.join(args.output, "summary.csv")
    os.makedirs(args.output, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("frontend,acc_original,acc_finetuned,acc_delta\n")
        f.write(f"logmel_kd,{acc_original:.6f},{acc_finetuned:.6f},{(acc_finetuned - acc_original):.6f}\n")

    print(f"Saved summary: {summary_path}")


if __name__ == "__main__":
    main()
