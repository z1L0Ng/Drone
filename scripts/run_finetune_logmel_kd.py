#!/usr/bin/env python3

import os
import argparse
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


def setup_gpu():
    gpus = tf.config.list_physical_devices("GPU")
    if gpus:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        print(f"GPU ready: {len(gpus)} devices")
    else:
        print("No GPU detected, using CPU")


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


def build_feature_tensor(filepaths):
    x = np.empty((len(filepaths), *INPUT_SHAPE), dtype=np.float32)
    for i, p in enumerate(filepaths):
        feat = extract_logmel(load_audio_1s(p))
        x[i] = np.expand_dims(feat, axis=-1)
    return x


class FinetuneDataGenerator(tf.keras.utils.Sequence):
    def __init__(self, filepaths, labels, batch_size, num_classes):
        self.filepaths = filepaths
        self.labels = labels
        self.batch_size = batch_size
        self.num_classes = num_classes
        self.indexes = np.arange(len(self.filepaths))
        np.random.shuffle(self.indexes)

    def __len__(self):
        return int(np.ceil(len(self.filepaths) / self.batch_size))

    def __getitem__(self, index):
        batch_idx = self.indexes[index * self.batch_size:(index + 1) * self.batch_size]
        bsz = len(batch_idx)

        x = np.empty((bsz, *INPUT_SHAPE), dtype=np.float32)
        y = np.empty(bsz, dtype=np.int32)

        for i, idx in enumerate(batch_idx):
            feat = extract_logmel(load_audio_1s(self.filepaths[idx]))
            x[i] = np.expand_dims(feat, axis=-1)
            y[i] = self.labels[idx]

        return x, tf.keras.utils.to_categorical(y, num_classes=self.num_classes)

    def on_epoch_end(self):
        np.random.shuffle(self.indexes)


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
    args = parser.parse_args()

    setup_gpu()

    le = joblib.load(args.encoder)
    class_names = le.classes_
    num_classes = len(class_names)

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

    x_test_features = build_feature_tensor(x_test)

    model_original = build_model(INPUT_SHAPE, num_classes, **MODEL_KWARGS)
    model_original.load_weights(args.weights)
    y_proba_original = model_original.predict(x_test_features, verbose=0)
    y_pred_original = np.argmax(y_proba_original, axis=1)
    acc_original = accuracy_score(y_test, y_pred_original)
    print(f"Original accuracy: {acc_original:.4f}")

    model_finetuned = build_model(INPUT_SHAPE, num_classes, **MODEL_KWARGS)
    model_finetuned.load_weights(args.weights)
    model_finetuned.compile(
        optimizer=Adam(learning_rate=args.lr),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    train_gen = FinetuneDataGenerator(x_finetune, y_finetune, args.batch_size, num_classes)
    val_gen = FinetuneDataGenerator(x_val, y_val, args.batch_size, num_classes)

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
