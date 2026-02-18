#!/usr/bin/env python3
# Batch finetune + eval for all frontends

import os
import sys
import numpy as np
import tensorflow as tf
import librosa
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.utils import class_weight
import joblib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from model import build_model
from model_config import (
    MODEL_KWARGS,
    FRONTEND_TYPES,
    SPEC_SUB_FRONTENDS,
    WIENER_FRONTENDS,
    get_input_shape,
    get_model_weights_path,
    DEFAULT_CALIB_NOISE_WAV,
    SAMPLE_RATE, DURATION, TARGET_LEN,
    N_FFT, HOP_LENGTH, CENTER,
    N_MELS, N_MFCC, FMIN, FMAX, TOP_DB,
    MAX_FRAMES, N_BINS,
    PCEN_KWARGS, SPEC_SUB_PARAMS,
)
from keras.optimizers import Adam
from keras.callbacks import ModelCheckpoint, EarlyStopping

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
TEST_DATA_DIR = "testset"
ENCODER_PATH = "saved_models/label_encoder.joblib"

FINETUNE_ENABLED = True
FINETUNE_RATIO = 0.3
VAL_RATIO = 0.1
FINETUNE_EPOCHS = 10
FINETUNE_BATCH_SIZE = 32
FINETUNE_LEARNING_RATE = 1e-5

SAVE_RESULTS = True
BASE_OUTPUT_DIR = "result/finetune"
RANDOM_SEED = 42
SPLIT_CACHE_PATH = os.path.join(BASE_OUTPUT_DIR, "split_indices.npz")


# -----------------------------------------------------------------------------
# GPU config
# -----------------------------------------------------------------------------
gpus = tf.config.list_physical_devices("GPU")
if gpus:
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)
    print(f"GPU ready: {len(gpus)} devices")
else:
    print("No GPU detected, using CPU")


# -----------------------------------------------------------------------------
# Wiener denoise helpers
# -----------------------------------------------------------------------------
NOISE_PROFILE_BASE = None


def build_noise_profile_from_wav(wav_path, seconds=1.0, method="mean"):
    ns, _ = librosa.load(wav_path, sr=SAMPLE_RATE, mono=True)
    target = int(seconds * SAMPLE_RATE)
    if len(ns) < target:
        ns = np.pad(ns, (0, target - len(ns)), mode="wrap")
    else:
        ns = ns[:target]
    N = librosa.stft(ns, n_fft=N_FFT, hop_length=HOP_LENGTH, center=CENTER)
    Pn = (np.abs(N) ** 2).astype(np.float32)
    if method == "median":
        profile = np.median(Pn, axis=1)
    else:
        profile = np.mean(Pn, axis=1)
    return profile.astype(np.float32)


def wiener_denoise_with_profile(y_mix, noise_profile, eps=1e-12):
    X = librosa.stft(y_mix, n_fft=N_FFT, hop_length=HOP_LENGTH, center=CENTER)
    Px = (np.abs(X) ** 2).astype(np.float32)
    Pn = noise_profile.astype(np.float32)[:, None]
    if Pn.shape[0] != Px.shape[0]:
        m = min(Pn.shape[0], Px.shape[0])
        Pn = Pn[:m, :]
        Px = Px[:m, :]
        X = X[:m, :]
    Ps = np.maximum(Px - Pn, 0.0)
    G = Ps / (Ps + Pn + eps)
    Y = G * X
    y_out = librosa.istft(Y, hop_length=HOP_LENGTH, center=CENTER, length=len(y_mix))
    return y_out.astype(np.float32)


# -----------------------------------------------------------------------------
# Feature extraction
# -----------------------------------------------------------------------------
def spectral_subtract(
    y_mix,
    n_fft,
    hop_length,
    center=False,
    alpha=1.0,
    floor=1e-6,
    noise_est_percentile=0.2,
):
    X = librosa.stft(y_mix, n_fft=n_fft, hop_length=hop_length, center=center)
    mag_X = np.abs(X)
    frame_energy = np.mean(mag_X, axis=0)
    k = max(1, int(len(frame_energy) * noise_est_percentile))
    idx = np.argsort(frame_energy)[:k]
    noise_mag = np.mean(mag_X[:, idx], axis=1, keepdims=True)
    mag_sub = np.maximum(mag_X - alpha * noise_mag, floor)
    Y = mag_sub * np.exp(1j * np.angle(X))
    y_out = librosa.istft(Y, hop_length=hop_length, center=center, length=len(y_mix))
    return y_out.astype(np.float32)


def extract_fft_features(y):
    D = librosa.stft(y, n_fft=N_FFT, hop_length=HOP_LENGTH, center=CENTER)
    mag = np.abs(D).astype(np.float32)
    feat = librosa.amplitude_to_db(mag, ref=np.max, top_db=TOP_DB)
    if feat.shape[1] < MAX_FRAMES:
        feat = np.pad(feat, ((0, 0), (0, MAX_FRAMES - feat.shape[1])), mode="constant")
    else:
        feat = feat[:, :MAX_FRAMES]
    return feat.astype(np.float32)


def extract_logmel_features(y):
    mel = librosa.feature.melspectrogram(
        y=y, sr=SAMPLE_RATE,
        n_fft=N_FFT, hop_length=HOP_LENGTH, center=CENTER,
        n_mels=N_MELS, fmin=FMIN, fmax=FMAX, power=2.0
    )
    feat = librosa.power_to_db(mel, ref=np.max, top_db=TOP_DB)
    if feat.shape[1] < MAX_FRAMES:
        feat = np.pad(feat, ((0, 0), (0, MAX_FRAMES - feat.shape[1])), mode="constant")
    else:
        feat = feat[:, :MAX_FRAMES]
    return feat.astype(np.float32)


def extract_pcen_features(y):
    mel = librosa.feature.melspectrogram(
        y=y, sr=SAMPLE_RATE,
        n_fft=N_FFT, hop_length=HOP_LENGTH, center=CENTER,
        n_mels=N_MELS, fmin=FMIN, fmax=FMAX, power=2.0
    )
    feat = librosa.pcen(mel, sr=SAMPLE_RATE, hop_length=HOP_LENGTH, **PCEN_KWARGS)
    if feat.shape[1] < MAX_FRAMES:
        feat = np.pad(feat, ((0, 0), (0, MAX_FRAMES - feat.shape[1])), mode="constant")
    else:
        feat = feat[:, :MAX_FRAMES]
    return feat.astype(np.float32)


def extract_mfcc_features(y):
    mfcc = librosa.feature.mfcc(
        y=y, sr=SAMPLE_RATE,
        n_mfcc=N_MFCC, n_mels=N_MELS,
        n_fft=N_FFT, hop_length=HOP_LENGTH, center=CENTER,
        fmin=FMIN, fmax=FMAX
    )
    if mfcc.shape[1] < MAX_FRAMES:
        mfcc = np.pad(mfcc, ((0, 0), (0, MAX_FRAMES - mfcc.shape[1])), mode="constant")
    else:
        mfcc = mfcc[:, :MAX_FRAMES]
    return mfcc.astype(np.float32)


def extract_features(y, frontend_type, apply_wiener=False):
    if frontend_type in SPEC_SUB_FRONTENDS:
        y = spectral_subtract(
            y,
            n_fft=N_FFT,
            hop_length=HOP_LENGTH,
            center=CENTER,
            **SPEC_SUB_PARAMS,
        )
    if apply_wiener and NOISE_PROFILE_BASE is not None:
        y = wiener_denoise_with_profile(y, NOISE_PROFILE_BASE)
    if frontend_type in {"fft", "fft_specsub", "fft_wiener"}:
        return extract_fft_features(y)
    if frontend_type in {"logmel", "logmel_specsub", "logmel_wiener"}:
        return extract_logmel_features(y)
    if frontend_type in {"pcen", "pcen_specsub", "pcen_wiener"}:
        return extract_pcen_features(y)
    if frontend_type in {"mfcc", "mfcc_specsub", "mfcc_wiener"}:
        return extract_mfcc_features(y)
    raise ValueError(f"Unknown frontend_type: {frontend_type}")


def load_audio(filepath, sr=SAMPLE_RATE, duration=DURATION):
    try:
        audio, _ = librosa.load(filepath, sr=sr, mono=True, duration=duration)
        target_len = int(duration * sr)
        if len(audio) < target_len:
            audio = np.pad(audio, (0, target_len - len(audio)))
        else:
            audio = audio[:target_len]
        return audio
    except Exception:
        return np.zeros(int(duration * sr), dtype=np.float32)


class FinetuneDataGenerator(tf.keras.utils.Sequence):
    def __init__(self, filepaths, labels, batch_size, num_classes, input_shape, frontend_type):
        self.filepaths = filepaths
        self.labels = labels
        self.batch_size = batch_size
        self.num_classes = num_classes
        self.input_shape = input_shape
        self.frontend_type = frontend_type
        self.indexes = np.arange(len(self.filepaths))
        np.random.shuffle(self.indexes)

    def __len__(self):
        return int(np.ceil(len(self.filepaths) / self.batch_size))

    def __getitem__(self, index):
        batch_indexes = self.indexes[index * self.batch_size:(index + 1) * self.batch_size]
        batch_size = len(batch_indexes)
        X = np.empty((batch_size, *self.input_shape), dtype=np.float32)
        y = np.empty(batch_size, dtype=int)
        apply_wiener = self.frontend_type in WIENER_FRONTENDS
        for i, idx in enumerate(batch_indexes):
            audio = load_audio(self.filepaths[idx])
            feat = extract_features(audio, self.frontend_type, apply_wiener=apply_wiener)
            X[i] = np.expand_dims(feat, axis=-1)
            y[i] = self.labels[idx]
        return X, tf.keras.utils.to_categorical(y, num_classes=self.num_classes)


def save_evaluation_results(y_true, y_pred, y_proba, output_dir, model_name, class_names, meta=None):
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, "classification_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"{model_name} - Classification Report\n")
        f.write("=" * 60 + "\n\n")
        if meta:
            for k, v in meta.items():
                f.write(f"{k}: {v}\n")
            f.write("\n")
        f.write(classification_report(y_true, y_pred, target_names=[str(n) for n in class_names]))
        f.write(f"\n\nAccuracy: {accuracy_score(y_true, y_pred):.4f}\n")

    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues",
        xticklabels=[str(n) for n in class_names],
        yticklabels=[str(n) for n in class_names]
    )
    plt.title(f"{model_name} - Confusion Matrix")
    plt.ylabel("True")
    plt.xlabel("Predicted")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "confusion_matrix.png"), dpi=150, bbox_inches="tight")
    plt.close()

    np.savez(
        os.path.join(output_dir, "predictions.npz"),
        y_true=y_true,
        y_pred=y_pred,
        y_proba=y_proba,
        filepaths=X_test_paths,
    )


# -----------------------------------------------------------------------------
# Load labels and testset filepaths
# -----------------------------------------------------------------------------
if not os.path.isdir(TEST_DATA_DIR):
    raise ValueError(f"Test data directory not found: {TEST_DATA_DIR}")

le = joblib.load(ENCODER_PATH)
class_names = le.classes_

X_all_paths = []
y_all = []
for item in os.listdir(TEST_DATA_DIR):
    item_path = os.path.join(TEST_DATA_DIR, item)
    if os.path.isdir(item_path):
        if item in class_names:
            class_idx = le.transform([item])[0]
            for root, _, files in os.walk(item_path):
                for f in files:
                    if f.lower().endswith(".wav"):
                        X_all_paths.append(os.path.join(root, f))
                        y_all.append(class_idx)

X_all_paths = np.array(X_all_paths)
y_all = np.array(y_all)
print(f"Loaded testset: {len(X_all_paths)} samples")

if FINETUNE_ENABLED:
    # Split into adapt/val/test, with test taking the largest share.
    # Cache the split to keep results comparable across runs.
    test_ratio = 1.0 - (FINETUNE_RATIO + VAL_RATIO)
    if test_ratio <= 0:
        raise ValueError("Invalid ratios: FINETUNE_RATIO + VAL_RATIO must be < 1.0")

    if os.path.exists(SPLIT_CACHE_PATH):
        cache = np.load(SPLIT_CACHE_PATH, allow_pickle=True)
        idx_finetune = cache["idx_finetune"]
        idx_val = cache["idx_val"]
        idx_test = cache["idx_test"]
        X_finetune_paths, y_finetune = X_all_paths[idx_finetune], y_all[idx_finetune]
        X_val_paths, y_val = X_all_paths[idx_val], y_all[idx_val]
        X_test_paths, y_test = X_all_paths[idx_test], y_all[idx_test]
        print(f"Loaded cached split: {SPLIT_CACHE_PATH}")
    else:
        # First, split out test
        X_temp, X_test_paths, y_temp, y_test, idx_temp, idx_test = train_test_split(
            X_all_paths, y_all, np.arange(len(X_all_paths)),
            test_size=test_ratio,
            stratify=y_all,
            random_state=RANDOM_SEED
        )
        # Then split temp into adapt/val
        val_ratio_adj = VAL_RATIO / (FINETUNE_RATIO + VAL_RATIO)
        X_finetune_paths, X_val_paths, y_finetune, y_val, idx_finetune, idx_val = train_test_split(
            X_temp, y_temp, idx_temp,
            test_size=val_ratio_adj,
            stratify=y_temp,
            random_state=RANDOM_SEED
        )
        os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)
        np.savez(
            SPLIT_CACHE_PATH,
            idx_finetune=idx_finetune,
            idx_val=idx_val,
            idx_test=idx_test,
        )
        print(f"Saved split cache: {SPLIT_CACHE_PATH}")
else:
    X_test_paths, y_test = X_all_paths, y_all
    X_finetune_paths, y_finetune = np.array([]), np.array([])
    X_val_paths, y_val = np.array([]), np.array([])

summary_rows = []


def ensure_noise_profile():
    global NOISE_PROFILE_BASE
    if NOISE_PROFILE_BASE is None:
        if os.path.exists(DEFAULT_CALIB_NOISE_WAV):
            NOISE_PROFILE_BASE = build_noise_profile_from_wav(DEFAULT_CALIB_NOISE_WAV, seconds=1.0)
            print(f"Built noise profile: {NOISE_PROFILE_BASE.shape}")
        else:
            print(f"Warning: noise profile wav missing: {DEFAULT_CALIB_NOISE_WAV}")


for frontend in FRONTEND_TYPES:
    print("\n" + "=" * 60)
    print(f"Frontend: {frontend}")
    print("=" * 60)

    if frontend in WIENER_FRONTENDS:
        ensure_noise_profile()

    model_weight_path = get_model_weights_path(frontend, base_dir="saved_models")
    if not os.path.exists(model_weight_path):
        print(f"Skip: weights not found: {model_weight_path}")
        continue

    input_shape = get_input_shape(frontend)
    num_classes = len(class_names)

    # Extract test features
    apply_wiener = frontend in WIENER_FRONTENDS and NOISE_PROFILE_BASE is not None
    X_test_features = []
    for path in X_test_paths:
        audio = load_audio(path)
        feat = extract_features(audio, frontend, apply_wiener=apply_wiener)
        X_test_features.append(feat)
    X_test_features = np.array(X_test_features)
    X_test_features = np.expand_dims(X_test_features, axis=-1)

    # Original model inference
    model_original = build_model(input_shape, num_classes, **MODEL_KWARGS)
    model_original.load_weights(model_weight_path)
    y_pred_original = np.argmax(model_original.predict(X_test_features, verbose=0), axis=1)
    y_pred_proba_original = model_original.predict(X_test_features, verbose=0)
    acc_original = accuracy_score(y_test, y_pred_original)
    print(f"Original accuracy: {acc_original:.4f}")

    # Finetune
    model_finetuned = None
    acc_finetuned = None
    finetune_ckpt_path = None
    if FINETUNE_ENABLED and len(X_finetune_paths) > 0:
        train_gen = FinetuneDataGenerator(
            X_finetune_paths, y_finetune, FINETUNE_BATCH_SIZE, num_classes, input_shape, frontend
        )
        val_gen = FinetuneDataGenerator(
            X_val_paths, y_val, FINETUNE_BATCH_SIZE, num_classes, input_shape, frontend
        )
        class_weights = class_weight.compute_class_weight(
            "balanced", classes=np.unique(y_finetune), y=y_finetune
        )
        class_weight_dict = dict(enumerate(class_weights))

        model_finetuned = build_model(input_shape, num_classes, **MODEL_KWARGS)
        model_finetuned.load_weights(model_weight_path)
        model_finetuned.compile(
            optimizer=Adam(learning_rate=FINETUNE_LEARNING_RATE),
            loss="categorical_crossentropy",
            metrics=["accuracy"],
        )

        finetune_ckpt_path = os.path.join(
            "saved_models", frontend, "finetuned_best.weights.h5"
        )
        os.makedirs(os.path.dirname(finetune_ckpt_path), exist_ok=True)
        callbacks = [
            ModelCheckpoint(
                finetune_ckpt_path,
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
            epochs=FINETUNE_EPOCHS,
            callbacks=callbacks,
            class_weight=class_weight_dict,
            verbose=1,
        )
        model_finetuned.load_weights(finetune_ckpt_path)
        y_pred_finetuned = np.argmax(model_finetuned.predict(X_test_features, verbose=0), axis=1)
        y_pred_proba_finetuned = model_finetuned.predict(X_test_features, verbose=0)
        acc_finetuned = accuracy_score(y_test, y_pred_finetuned)
        print(f"Finetuned accuracy: {acc_finetuned:.4f}")
    else:
        y_pred_finetuned = None
        y_pred_proba_finetuned = None
        print("Finetune skipped")

    # Save results
    if SAVE_RESULTS:
        output_dir_original = os.path.join(BASE_OUTPUT_DIR, frontend, "original")
        output_dir_finetuned = os.path.join(BASE_OUTPUT_DIR, frontend, "finetuned")
        meta = {
            "frontend": frontend,
            "model_weights": model_weight_path,
            "test_samples": len(X_test_paths),
        }
        save_evaluation_results(
            y_test, y_pred_original, y_pred_proba_original,
            output_dir_original, "Original Model", class_names, meta=meta
        )
        if model_finetuned is not None:
            meta_ft = dict(meta)
            meta_ft["finetune_samples"] = len(X_finetune_paths)
            meta_ft["val_samples"] = len(X_val_paths)
            meta_ft["finetune_epochs"] = FINETUNE_EPOCHS
            meta_ft["finetune_lr"] = FINETUNE_LEARNING_RATE
            if finetune_ckpt_path:
                meta_ft["finetune_weights"] = finetune_ckpt_path
            save_evaluation_results(
                y_test, y_pred_finetuned, y_pred_proba_finetuned,
                output_dir_finetuned, "Finetuned Model", class_names, meta=meta_ft
            )

    summary_rows.append({
        "frontend": frontend,
        "acc_original": acc_original,
        "acc_finetuned": acc_finetuned,
        "acc_delta": None if acc_finetuned is None else acc_finetuned - acc_original,
    })


# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
if SAVE_RESULTS and summary_rows:
    os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)
    summary_path = os.path.join(BASE_OUTPUT_DIR, "summary.csv")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("frontend,acc_original,acc_finetuned,acc_delta\n")
        for r in summary_rows:
            acc_ft = "" if r["acc_finetuned"] is None else f"{r['acc_finetuned']:.6f}"
            acc_delta = "" if r["acc_delta"] is None else f"{r['acc_delta']:.6f}"
            f.write(f"{r['frontend']},{r['acc_original']:.6f},{acc_ft},{acc_delta}\n")
    print(f"Summary saved: {summary_path}")
