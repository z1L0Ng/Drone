# --- Log-Mel + Wiener, SNR -30dB to -20dB ---

import os
import numpy as np
import tensorflow as tf
import librosa
from model import build_model
from keras.optimizers import Adam
from keras.callbacks import ModelCheckpoint, EarlyStopping
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.utils import class_weight
import joblib

gpus = tf.config.list_physical_devices('GPU')
if gpus:
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)
    print(f"✅ GPU Ready: {len(gpus)} devices")

NOISE_DIR_OPEN = "dataset/raw/drone"
NOISE_DIR_OWN  = "dataset/raw/tellonoise"
NOISE_SOURCE_DIR = NOISE_DIR_OPEN   # <- 切换

NOISE_MIX_PROB = 1.0
MIN_SNR_DB = -30.0
MAX_SNR_DB = -20.0

PROCESSED_DATA_PATH = "dataset/processed/data_paths.npz"
MODELS_PATH = "saved_models/"
RESULT_PATH = "result/logmel_wiener/"
ENCODER_PATH = os.path.join(MODELS_PATH, "label_encoder.joblib")

os.makedirs(MODELS_PATH, exist_ok=True)
os.makedirs(RESULT_PATH, exist_ok=True)

EPOCHS = 20
BATCH_SIZE = 32
SAMPLE_RATE = 16000
DURATION = 1

N_MELS = 256
N_FFT = 1024
HOP_LENGTH = 512
CENTER = False
FMIN = 50
FMAX = None

TARGET_LEN = int(DURATION * SAMPLE_RATE)
MAX_FRAMES = int(DURATION * SAMPLE_RATE / HOP_LENGTH) + 1

def wiener_denoise_with_noise_ref(y_mix, y_noise_ref, eps=1e-12):
    X = librosa.stft(y_mix, n_fft=N_FFT, hop_length=HOP_LENGTH, center=CENTER)
    N = librosa.stft(y_noise_ref, n_fft=N_FFT, hop_length=HOP_LENGTH, center=CENTER)

    Px = np.abs(X) ** 2
    Pn = np.abs(N) ** 2
    T = min(Px.shape[1], Pn.shape[1])

    Px, Pn, X = Px[:, :T], Pn[:, :T], X[:, :T]
    Ps = np.maximum(Px - Pn, 0.0)
    G = Ps / (Ps + Pn + eps)

    Y = G * X
    y_out = librosa.istft(Y, hop_length=HOP_LENGTH, center=CENTER, length=len(y_mix))
    return y_out.astype(np.float32)

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
        mel = librosa.feature.melspectrogram(
            y=y, sr=SAMPLE_RATE,
            n_fft=N_FFT, hop_length=HOP_LENGTH, center=CENTER,
            n_mels=N_MELS, fmin=FMIN, fmax=FMAX, power=2.0
        )
        feat = librosa.power_to_db(mel, ref=np.max, top_db=80.0)

        if feat.shape[1] < MAX_FRAMES:
            feat = np.pad(feat, ((0, 0), (0, MAX_FRAMES - feat.shape[1])), mode='constant')
        else:
            feat = feat[:, :MAX_FRAMES]
        return feat.astype(np.float32)

    def __getitem__(self, index):
        indexes = self.indexes[index*self.batch_size:(index+1)*self.batch_size]
        X = np.empty((self.batch_size, N_MELS, MAX_FRAMES, 1), dtype=np.float32)
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

                    noise_scaled = noise * (sig_rms / scale / noise_rms)
                    audio_mix = audio + noise_scaled

                    # Wiener enhancement
                    audio = wiener_denoise_with_noise_ref(audio_mix, noise_scaled)

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

model = build_model((N_MELS, MAX_FRAMES, 1), NUM_CLASSES)
model.compile(optimizer=Adam(1e-4), loss='categorical_crossentropy', metrics=['accuracy'])

ckpt_path = os.path.join(MODELS_PATH, "logmel_wiener_best.weights.h5")
callbacks = [
    ModelCheckpoint(ckpt_path, save_best_only=True, monitor='val_accuracy', save_weights_only=True, verbose=1),
    EarlyStopping(patience=10, restore_best_weights=True, verbose=1)
]

print("🚀 Start Log-Mel + Wiener Training...")
history = model.fit(train_gen, validation_data=val_gen, epochs=EPOCHS,
                    callbacks=callbacks, class_weight=class_weight_dict)

print(f"\n📊 Generating Report in {RESULT_PATH}...")
plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
plt.plot(history.history['accuracy'], label='Train')
plt.plot(history.history['val_accuracy'], label='Val')
plt.title('Log-Mel+Wiener Accuracy')
plt.legend()
plt.subplot(1, 2, 2)
plt.plot(history.history['loss'], label='Train')
plt.plot(history.history['val_loss'], label='Val')
plt.title('Log-Mel+Wiener Loss')
plt.legend()
plt.savefig(os.path.join(RESULT_PATH, "training_history.png"))
plt.close()

model.load_weights(ckpt_path)
y_pred = np.argmax(model.predict(test_gen), axis=1)
y_true = []
for i in range(len(test_gen)):
    _, y_batch = test_gen[i]
    y_true.extend(np.argmax(y_batch, axis=1))

cm = confusion_matrix(y_true, y_pred)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=class_names, yticklabels=class_names)
plt.title('Log-Mel+Wiener Confusion Matrix')
plt.ylabel('True')
plt.xlabel('Predicted')
plt.savefig(os.path.join(RESULT_PATH, "confusion_matrix.png")) 
plt.close()

with open(os.path.join(RESULT_PATH, "classification_report.txt"), "w") as f:
    f.write(classification_report(y_true, y_pred, target_names=class_names))

print("✅ Log-Mel+Wiener Done.")