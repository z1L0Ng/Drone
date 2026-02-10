# --- MFCC + Realistic Wiener Filtering (Mild Bias), SNR -15dB to -5dB ---

import os
import numpy as np
import tensorflow as tf
import librosa
from model import build_model
from model_config import MODEL_KWARGS
from keras.optimizers import Adam
from keras.callbacks import ModelCheckpoint, EarlyStopping
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.utils import class_weight
import joblib

# ==================== GPU 配置 ====================
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)
    print(f"✅ GPU Ready: {len(gpus)} devices")

# ==================== 路径配置 ====================
NOISE_SOURCE_DIR = "dataset/raw/tellonoise"
CALIB_NOISE_WAV = "dataset/raw/tellonoise/19700101_000018.wav"

PROCESSED_DATA_PATH = "dataset/processed/data_paths.npz"
MODELS_PATH = "saved_models/mfcc_wiener/"
RESULT_PATH = "result/mfcc_wiener/"
ENCODER_PATH = "saved_models/label_encoder.joblib"

os.makedirs(MODELS_PATH, exist_ok=True)
os.makedirs(RESULT_PATH, exist_ok=True)

# ==================== 训练参数 ====================
EPOCHS = 50
BATCH_SIZE = 32
LEARNING_RATE = 1e-4

# ==================== 噪声参数 ====================
NOISE_MIX_PROB = 1.0
MIN_SNR_DB = -15.0
MAX_SNR_DB = -5.0

# ==================== 音频参数 ====================
SAMPLE_RATE = 16000
DURATION = 1.0
TARGET_LEN = int(DURATION * SAMPLE_RATE)

# ==================== 前端参数 ====================
N_MFCC = 40
N_MELS = 256
N_FFT = 1024
HOP_LENGTH = 512
CENTER = False
FMIN = 50
FMAX = None
MAX_FRAMES = int(DURATION * SAMPLE_RATE / HOP_LENGTH) + 1

# ==================== Realistic Wiener 配置 ====================
CALIB_SECONDS = 1.0
PROFILE_METHOD = "mean"

ENABLE_GLOBAL_SCALE_BIAS = True
SCALE_RANGE = (0.8, 1.2)

ENABLE_SPECTRAL_TILT_BIAS = True
TILT_DB_RANGE = (-3.0, 3.0)

ENABLE_PER_FREQ_JITTER = False
JITTER_STD_DB = 1.0


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


def apply_profile_bias(noise_profile):
    prof = noise_profile.astype(np.float32).copy()
    freq_bins = prof.shape[0]

    if ENABLE_GLOBAL_SCALE_BIAS:
        scale = np.random.uniform(*SCALE_RANGE)
        prof *= scale

    if ENABLE_SPECTRAL_TILT_BIAS:
        tilt_db = np.random.uniform(*TILT_DB_RANGE)
        tilt_db_vec = np.linspace(0.0, tilt_db, freq_bins).astype(np.float32)
        tilt_lin = (10.0 ** (tilt_db_vec / 10.0)).astype(np.float32)
        prof *= tilt_lin

    if ENABLE_PER_FREQ_JITTER:
        jitter_db = np.random.normal(loc=0.0, scale=JITTER_STD_DB, size=freq_bins).astype(np.float32)
        jitter_lin = (10.0 ** (jitter_db / 10.0)).astype(np.float32)
        prof *= jitter_lin

    prof = np.maximum(prof, 1e-12).astype(np.float32)
    return prof


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


NOISE_PROFILE_BASE = None
if os.path.exists(CALIB_NOISE_WAV):
    NOISE_PROFILE_BASE = build_noise_profile_from_wav(
        CALIB_NOISE_WAV, seconds=CALIB_SECONDS, method=PROFILE_METHOD
    )
else:
    raise FileNotFoundError(f"校准噪声文件不存在: {CALIB_NOISE_WAV}")


class DataGenerator(tf.keras.utils.Sequence):
    def __init__(self, filepaths, labels, batch_size, num_classes,
                 is_training=True, noise_paths=None, snr_range=(-15, -5)):
        self.filepaths = filepaths
        self.labels = labels
        self.batch_size = batch_size
        self.num_classes = num_classes
        self.is_training = is_training
        self.noise_paths = noise_paths if noise_paths else []
        self.min_snr, self.max_snr = snr_range
        self.target_len = TARGET_LEN
        self.indexes = np.arange(len(self.filepaths))
        self.on_epoch_end()

    def __len__(self):
        return int(np.floor(len(self.filepaths) / self.batch_size))

    def on_epoch_end(self):
        if self.is_training:
            np.random.shuffle(self.indexes)

    def _get_noise(self):
        if not self.noise_paths:
            return None
        noise_path = np.random.choice(self.noise_paths)
        try:
            ns, _ = librosa.load(noise_path, sr=SAMPLE_RATE, mono=True)
            if len(ns) < self.target_len:
                return np.pad(ns, (0, self.target_len - len(ns)), mode='wrap')
            start = np.random.randint(0, len(ns) - self.target_len + 1)
            return ns[start:start + self.target_len]
        except Exception as e:
            print(f"加载噪声失败 {noise_path}: {e}")
            return None

    def _extract_features(self, y):
        mfcc = librosa.feature.mfcc(
            y=y,
            sr=SAMPLE_RATE,
            n_mfcc=N_MFCC,
            n_mels=N_MELS,
            n_fft=N_FFT,
            hop_length=HOP_LENGTH,
            center=CENTER,
            fmin=FMIN,
            fmax=FMAX
        )

        if mfcc.shape[1] < MAX_FRAMES:
            mfcc = np.pad(mfcc, ((0, 0), (0, MAX_FRAMES - mfcc.shape[1])), mode='constant')
        else:
            mfcc = mfcc[:, :MAX_FRAMES]
        return mfcc.astype(np.float32)

    def __getitem__(self, index):
        indexes = self.indexes[index*self.batch_size:(index+1)*self.batch_size]
        X = np.empty((self.batch_size, N_MFCC, MAX_FRAMES, 1), dtype=np.float32)
        y = np.empty(self.batch_size, dtype=int)

        for i, idx in enumerate(indexes):
            try:
                audio, _ = librosa.load(
                    self.filepaths[idx],
                    sr=SAMPLE_RATE,
                    mono=True,
                    duration=DURATION
                )
                if len(audio) < self.target_len:
                    audio = np.pad(audio, (0, self.target_len - len(audio)))
                else:
                    audio = audio[:self.target_len]
            except Exception as e:
                print(f"加载音频失败 {self.filepaths[idx]}: {e}")
                audio = np.zeros(self.target_len, dtype=np.float32)

            if self.is_training:
                noise = self._get_noise()
                if noise is not None and np.random.rand() < NOISE_MIX_PROB:
                    snr = np.random.uniform(self.min_snr, self.max_snr)
                    sig_rms = np.sqrt(np.mean(audio**2)) + 1e-8
                    noise_rms = np.sqrt(np.mean(noise**2)) + 1e-8
                    scale = 10**(snr / 20)
                    noise_scaled = noise * (sig_rms / scale / noise_rms)
                    audio_mix = audio + noise_scaled

                    prof_biased = apply_profile_bias(NOISE_PROFILE_BASE)
                    audio = wiener_denoise_with_profile(audio_mix, prof_biased)

                if np.random.rand() < 0.2:
                    audio = librosa.effects.time_stretch(
                        y=audio,
                        rate=np.random.uniform(0.9, 1.1)
                    )
                    if len(audio) > self.target_len:
                        audio = audio[:self.target_len]
                    elif len(audio) < self.target_len:
                        audio = np.pad(audio, (0, self.target_len - len(audio)))

            features = self._extract_features(audio)
            X[i] = np.expand_dims(features, axis=-1)
            y[i] = self.labels[idx]

        return X, tf.keras.utils.to_categorical(y, num_classes=self.num_classes)


if __name__ == '__main__':
    print("=" * 70)
    print("实验: MFCC + Realistic Wiener Filtering (Mild Bias)")
    print("=" * 70)

    print("\n>>> 加载数据...")
    data = np.load(PROCESSED_DATA_PATH, allow_pickle=True)
    le = joblib.load(ENCODER_PATH)
    class_names = le.classes_
    NUM_CLASSES = len(class_names)

    noise_files = []
    if os.path.exists(NOISE_SOURCE_DIR):
        for r, _, fs in os.walk(NOISE_SOURCE_DIR):
            noise_files.extend([
                os.path.join(r, f) for f in fs
                if f.lower().endswith('.wav')
            ])

    class_weights = class_weight.compute_class_weight(
        'balanced',
        classes=np.unique(data['y_train']),
        y=data['y_train']
    )
    class_weight_dict = dict(enumerate(class_weights))

    train_gen = DataGenerator(
        data['X_train'], data['y_train'],
        BATCH_SIZE, NUM_CLASSES,
        is_training=True,
        noise_paths=noise_files,
        snr_range=(MIN_SNR_DB, MAX_SNR_DB)
    )

    val_gen = DataGenerator(
        data['X_val'], data['y_val'],
        BATCH_SIZE, NUM_CLASSES,
        is_training=False
    )

    test_gen = DataGenerator(
        data['X_test'], data['y_test'],
        BATCH_SIZE, NUM_CLASSES,
        is_training=False
    )

    model = build_model((N_MFCC, MAX_FRAMES, 1), NUM_CLASSES, **MODEL_KWARGS)
    model.compile(
        optimizer=Adam(LEARNING_RATE),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )

    ckpt_path = os.path.join(MODELS_PATH, "mfcc_wiener_best.weights.h5")
    callbacks = [
        ModelCheckpoint(
            ckpt_path,
            save_best_only=True,
            monitor='val_accuracy',
            save_weights_only=True,
            verbose=1
        ),
        EarlyStopping(
            monitor='val_accuracy',
            patience=10,
            restore_best_weights=True,
            verbose=1
        )
    ]

    print(f"\n🚀 开始训练 (EPOCHS={EPOCHS})...\n")
    history = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=EPOCHS,
        callbacks=callbacks,
        class_weight=class_weight_dict
    )

    print(f"\n📊 生成评估报告...")
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns

        plt.figure(figsize=(12, 5))
        plt.subplot(1, 2, 1)
        plt.plot(history.history['accuracy'], label='Train')
        plt.plot(history.history['val_accuracy'], label='Val')
        plt.title('MFCC+Wiener Accuracy')
        plt.xlabel('Epoch')
        plt.ylabel('Accuracy')
        plt.legend()
        plt.grid(True)

        plt.subplot(1, 2, 2)
        plt.plot(history.history['loss'], label='Train')
        plt.plot(history.history['val_loss'], label='Val')
        plt.title('MFCC+Wiener Loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.legend()
        plt.grid(True)

        plt.tight_layout()
        plt.savefig(os.path.join(RESULT_PATH, "training_history.png"), dpi=150)
        plt.close()
    except Exception as e:
        print(f"⚠️ Plotting skipped: {e}")

    print("\n>>> 在测试集上评估...")
    model.load_weights(ckpt_path)
    y_pred = np.argmax(model.predict(test_gen), axis=1)
    y_true = []
    for i in range(len(test_gen)):
        _, y_batch = test_gen[i]
        y_true.extend(np.argmax(y_batch, axis=1))
    y_true = np.array(y_true, dtype=int)

    cm = confusion_matrix(y_true, y_pred)
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns

        plt.figure(figsize=(8, 6))
        sns.heatmap(
            cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=class_names, yticklabels=class_names
        )
        plt.title('MFCC+Wiener Confusion Matrix')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.tight_layout()
        plt.savefig(os.path.join(RESULT_PATH, "confusion_matrix.png"), dpi=150)
        plt.close()
    except Exception as e:
        print(f"⚠️ Confusion matrix plot skipped: {e}")

    report = classification_report(y_true, y_pred, target_names=class_names)
    print("\n" + "=" * 70)
    print("测试集分类报告:")
    print("=" * 70)
    print(report)

    with open(os.path.join(RESULT_PATH, "classification_report.txt"), "w") as f:
        f.write(report)

    print("\n" + "=" * 70)
    print("✅ MFCC + Realistic Wiener 训练完成")
    print("=" * 70)
