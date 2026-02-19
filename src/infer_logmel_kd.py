import os
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/numba_cache")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import argparse
import numpy as np
import tensorflow as tf
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import soundfile as sf
from scipy import signal

from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

from model import build_model
from model_config import MODEL_KWARGS


SAMPLE_RATE = 16000
DURATION = 1.0
TARGET_LEN = int(SAMPLE_RATE * DURATION)

N_MELS = 256
N_FFT = 1024
HOP_LENGTH = 512
CENTER = False
FMIN = 50
FMAX = None
TOP_DB = 80.0
MAX_FRAMES = int(DURATION * SAMPLE_RATE / HOP_LENGTH) + 1


def setup_gpu():
    gpus = tf.config.list_physical_devices("GPU")
    if gpus:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        print(f"GPU ready: {len(gpus)} devices")


def load_audio(filepath):
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


def normalize_label_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def scan_testset(test_data_dir, class_names):
    class_map = {normalize_label_name(c): i for i, c in enumerate(class_names)}
    x_paths = []
    y = []
    skipped = []

    if not os.path.isdir(test_data_dir):
        raise FileNotFoundError(f"Testset dir not found: {test_data_dir}")

    # Expected label space: testset/<label>/<...>/*.wav
    # Label is the first-level directory, and wavs may live in deeper subfolders.
    for label_name in sorted(os.listdir(test_data_dir)):
        label_dir = os.path.join(test_data_dir, label_name)
        if not os.path.isdir(label_dir):
            continue

        label_key = normalize_label_name(label_name)
        if label_key not in class_map:
            skipped.append((label_name, "ALL"))
            continue

        label_idx = class_map[label_key]
        for root, _, files in os.walk(label_dir):
            for fn in files:
                if fn.lower().endswith(".wav"):
                    x_paths.append(os.path.join(root, fn))
                    y.append(label_idx)

    return np.array(x_paths), np.array(y), skipped


def build_feature_tensor(filepaths):
    n = len(filepaths)
    x = np.empty((n, N_MELS, MAX_FRAMES, 1), dtype=np.float32)
    for i, fp in enumerate(filepaths):
        y = load_audio(fp)
        feat = extract_logmel(y)
        x[i] = np.expand_dims(feat, axis=-1)
    return x


def save_results(y_true, y_pred, class_names, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    acc = accuracy_score(y_true, y_pred)
    report = classification_report(y_true, y_pred, target_names=[str(c) for c in class_names], digits=4)

    report_path = os.path.join(output_dir, "classification_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("LogMel KD Student - Testset Inference\n")
        f.write("=" * 60 + "\n")
        f.write(f"Accuracy: {acc:.4f}\n\n")
        f.write(report)

    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=class_names, yticklabels=class_names)
    plt.title("Confusion Matrix - LogMel KD Student")
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.tight_layout()
    cm_path = os.path.join(output_dir, "confusion_matrix.png")
    plt.savefig(cm_path, dpi=200)
    plt.close()

    return acc, report_path, cm_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--testset", default="testset", help="Path to local testset root")
    parser.add_argument("--encoder", default="saved_models/label_encoder.joblib", help="Path to label encoder")
    parser.add_argument("--weights", default="saved_models/logmel_kd/student_kd_best.weights.h5", help="Path to student weights")
    parser.add_argument("--output", default="result/inference_logmel_kd", help="Output directory")
    args = parser.parse_args()

    setup_gpu()

    le = joblib.load(args.encoder)
    class_names = le.classes_
    num_classes = len(class_names)

    print(f"Loading testset from: {args.testset}")
    x_paths, y_true, skipped = scan_testset(args.testset, class_names)
    if len(x_paths) == 0:
        raise RuntimeError("No valid wav files found for known labels in testset.")

    print(f"Samples: {len(x_paths)}")
    if skipped:
        skipped_unique = sorted(set(skipped))
        print(f"Skipped unknown labels: {len(skipped_unique)}")
        for g, l in skipped_unique[:20]:
            print(f"  - {g}/{l}")

    x = build_feature_tensor(x_paths)

    model = build_model((N_MELS, MAX_FRAMES, 1), num_classes, **MODEL_KWARGS)
    model.load_weights(args.weights)
    model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])

    probs = model.predict(x, batch_size=32, verbose=1)
    y_pred = np.argmax(probs, axis=1)

    acc, report_path, cm_path = save_results(y_true, y_pred, class_names, args.output)
    print(f"Accuracy: {acc:.4f}")
    print(f"Saved report: {report_path}")
    print(f"Saved confusion matrix: {cm_path}")


if __name__ == "__main__":
    main()
