# --- MFCC Frontend, SNR -25dB to -10dB ---

import os
import numpy as np
import tensorflow as tf
import librosa
from model import build_model
from keras.optimizers import Adam
from keras.callbacks import ModelCheckpoint, EarlyStopping
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.utils import class_weight
import joblib

# --- 0. GPU 配置 ---
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)
    print(f"✅ GPU Ready: {len(gpus)} devices")

# --- 1. 核心配置 ---
NOISE_DIR_OPEN = "dataset/raw/drone"          # 开源噪声
NOISE_DIR_OWN  = "dataset/raw/tellonoise"     # 自采噪声
NOISE_SOURCE_DIR = NOISE_DIR_OWN              # <- 统一使用 tellonoise

NOISE_MIX_PROB = 1.0
MIN_SNR_DB = -25.0
MAX_SNR_DB = -10.0

PROCESSED_DATA_PATH = "dataset/processed/data_paths.npz"
MODELS_PATH = "saved_models/mfcc/"
RESULT_PATH = "result/mfcc/"
ENCODER_PATH = "saved_models/label_encoder.joblib"

os.makedirs(MODELS_PATH, exist_ok=True)
os.makedirs(RESULT_PATH, exist_ok=True)

EPOCHS = 50
BATCH_SIZE = 32
SAMPLE_RATE = 16000
DURATION = 1

# ==================== MFCC 前端参数 ====================
# MFCC 常用阶数（n_mfcc）通常在 20~40 左右，这里取 40 兼顾细节与稳定性
N_MFCC = 40
# Mel 滤波器数量，用于构建 Mel 频谱（MFCC 的中间表示）
N_MELS = 256
# STFT 参数
N_FFT = 1024
HOP_LENGTH = 512
CENTER = False
# 频率范围（Hz），FMAX=None 表示使用 Nyquist 频率
FMIN = 50
FMAX = None

TARGET_LEN = int(DURATION * SAMPLE_RATE)  # 16000
MAX_FRAMES = int(DURATION * SAMPLE_RATE / HOP_LENGTH) + 1  # 32

# --- 2. 数据生成器 ---
class DataGenerator(tf.keras.utils.Sequence):
    def __init__(self, filepaths, labels, batch_size, num_classes, is_training=True,
                 noise_paths=None, snr_range=(-5, 5)):
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
        except:
            return None

    def _extract_features(self, y):
        # ==================== MFCC 特征提取（完整中文注释）====================
        # 1) 输入 y 是一段一维波形，采样率为 SAMPLE_RATE。
        # 2) librosa.feature.mfcc 会内部完成：
        #    - STFT：将时域波形变换为频谱
        #    - Mel 滤波器组：把频谱映射到 Mel 频率尺度
        #    - 取对数能量：获得 Log-Mel 能量
        #    - DCT：把 Mel 频谱压缩成倒谱系数（MFCC）
        # 3) 关键参数说明：
        #    - n_mfcc：输出的 MFCC 维度（倒谱系数个数）
        #    - n_mels：Mel 滤波器的数量（影响中间 Mel 频谱分辨率）
        #    - n_fft / hop_length / center：STFT 的窗口与帧移参数
        #    - fmin / fmax：Mel 频谱的频率范围（Hz）
        # 4) 输出形状为 [n_mfcc, time_frames]
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

        # 统一时间帧长度到 MAX_FRAMES，避免不同音频长度带来的维度不一致
        if mfcc.shape[1] < MAX_FRAMES:
            mfcc = np.pad(mfcc, ((0, 0), (0, MAX_FRAMES - mfcc.shape[1])), mode='constant')
        else:
            mfcc = mfcc[:, :MAX_FRAMES]

        # 转成 float32 以节省显存并提升运算速度
        return mfcc.astype(np.float32)

    def __getitem__(self, index):
        indexes = self.indexes[index*self.batch_size:(index+1)*self.batch_size]
        X = np.empty((self.batch_size, N_MFCC, MAX_FRAMES, 1), dtype=np.float32)
        y = np.empty(self.batch_size, dtype=int)

        for i, idx in enumerate(indexes):
            try:
                audio, _ = librosa.load(self.filepaths[idx], sr=SAMPLE_RATE, mono=True, duration=DURATION)
                if len(audio) < self.target_len:
                    audio = np.pad(audio, (0, self.target_len - len(audio)))
                else:
                    audio = audio[:self.target_len]
            except:
                audio = np.zeros(self.target_len, dtype=np.float32)

            if self.is_training:
                noise = self._get_noise()
                if noise is not None and np.random.rand() < NOISE_MIX_PROB:
                    snr = np.random.uniform(self.min_snr, self.max_snr)
                    sig_rms = np.sqrt(np.mean(audio**2)) + 1e-8
                    noise_rms = np.sqrt(np.mean(noise**2)) + 1e-8
                    scale = 10**(snr / 20)
                    audio = audio + noise * (sig_rms / scale / noise_rms)

                if np.random.rand() < 0.2:
                    audio = librosa.effects.time_stretch(y=audio, rate=np.random.uniform(0.9, 1.1))
                    if len(audio) > self.target_len:
                        audio = audio[:self.target_len]
                    elif len(audio) < self.target_len:
                        audio = np.pad(audio, (0, self.target_len - len(audio)))

            features = self._extract_features(audio)
            X[i] = np.expand_dims(features, axis=-1)
            y[i] = self.labels[idx]

        return X, tf.keras.utils.to_categorical(y, num_classes=self.num_classes)

# --- 3. 运行流程 ---
print(">>> Loading Data...")
data = np.load(PROCESSED_DATA_PATH, allow_pickle=True)
le = joblib.load(ENCODER_PATH)
class_names = le.classes_
NUM_CLASSES = len(class_names)

noise_files = []
if os.path.exists(NOISE_SOURCE_DIR):
    for r, _, fs in os.walk(NOISE_SOURCE_DIR):
        noise_files.extend([os.path.join(r, f) for f in fs if f.lower().endswith('.wav')])
print(f"Noise Source: {NOISE_SOURCE_DIR} ({len(noise_files)} files) | SNR: {MIN_SNR_DB} ~ {MAX_SNR_DB} dB")

class_weights = class_weight.compute_class_weight('balanced', classes=np.unique(data['y_train']), y=data['y_train'])
class_weight_dict = dict(enumerate(class_weights))

train_gen = DataGenerator(data['X_train'], data['y_train'], BATCH_SIZE, NUM_CLASSES,
                          noise_paths=noise_files, snr_range=(MIN_SNR_DB, MAX_SNR_DB))
val_gen = DataGenerator(data['X_val'], data['y_val'], BATCH_SIZE, NUM_CLASSES, is_training=False)
test_gen = DataGenerator(data['X_test'], data['y_test'], BATCH_SIZE, NUM_CLASSES, is_training=False)

model = build_model((N_MFCC, MAX_FRAMES, 1), NUM_CLASSES)
model.compile(optimizer=Adam(1e-4), loss='categorical_crossentropy', metrics=['accuracy'])

ckpt_path = os.path.join(MODELS_PATH, "mfcc_best.weights.h5")
callbacks = [
    ModelCheckpoint(ckpt_path, save_best_only=True, monitor='val_accuracy', save_weights_only=True, verbose=1),
    EarlyStopping(patience=10, restore_best_weights=True, verbose=1)
]

print("🚀 Start MFCC Training...")
history = model.fit(train_gen, validation_data=val_gen, epochs=EPOCHS,
                    callbacks=callbacks, class_weight=class_weight_dict)

# --- 4. 绘图与评估 ---
print(f"\n📊 Generating Report in {RESULT_PATH}...")
try:
    import matplotlib.pyplot as plt
    import seaborn as sns

    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.plot(history.history['accuracy'], label='Train')
    plt.plot(history.history['val_accuracy'], label='Val')
    plt.title('MFCC Accuracy')
    plt.legend()
    plt.subplot(1, 2, 2)
    plt.plot(history.history['loss'], label='Train')
    plt.plot(history.history['val_loss'], label='Val')
    plt.title('MFCC Loss')
    plt.legend()
    plt.savefig(os.path.join(RESULT_PATH, "training_history.png"))
    plt.close()
except Exception as e:
    print(f"⚠️ Plotting skipped: {e}")

model.load_weights(ckpt_path)
y_pred = np.argmax(model.predict(test_gen), axis=1)
y_true = []
for i in range(len(test_gen)):
    _, y_batch = test_gen[i]
    y_true.extend(np.argmax(y_batch, axis=1))

cm = confusion_matrix(y_true, y_pred)
try:
    import matplotlib.pyplot as plt
    import seaborn as sns

    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=class_names, yticklabels=class_names)
    plt.title('MFCC Confusion Matrix')
    plt.ylabel('True')
    plt.xlabel('Predicted')
    plt.savefig(os.path.join(RESULT_PATH, "confusion_matrix.png"))
    plt.close()
except Exception as e:
    print(f"⚠️ Confusion matrix plot skipped: {e}")

with open(os.path.join(RESULT_PATH, "classification_report.txt"), "w") as f:
    f.write(classification_report(y_true, y_pred, target_names=class_names))

print("✅ MFCC Done.")
