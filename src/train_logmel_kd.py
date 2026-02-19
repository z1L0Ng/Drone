import os
import numpy as np
import tensorflow as tf
import librosa
import joblib

from keras.optimizers import Adam
from keras.callbacks import ModelCheckpoint, EarlyStopping
from sklearn.utils import class_weight
from sklearn.metrics import classification_report

from model import build_model
from model_config import MODEL_KWARGS


# ==================== GPU ====================
gpus = tf.config.list_physical_devices("GPU")
if gpus:
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)
    print(f"GPU Ready: {len(gpus)} devices")


# ==================== Paths ====================
PROCESSED_DATA_PATH = "dataset/processed/data_paths.npz"
ENCODER_PATH = "saved_models/label_encoder.joblib"

NOISE_SOURCE_DIR = "dataset/raw/tellonoise"

MODEL_DIR = "saved_models/logmel_kd"
RESULT_DIR = "result/logmel_kd"
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

TEACHER_CKPT = os.path.join(MODEL_DIR, "teacher_clean_best.weights.h5")
STUDENT_CKPT = os.path.join(MODEL_DIR, "student_kd_best.weights.h5")


# ==================== Audio / frontend ====================
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


# ==================== Train config ====================
BATCH_SIZE = 32
TEACHER_EPOCHS = 50
STUDENT_EPOCHS = 50
LEARNING_RATE = 1e-4

NOISE_MIX_PROB = 1.0
MIN_SNR_DB = -15.0
MAX_SNR_DB = -5.0
EVAL_SNR_DB = -10.0

# distillation weights
ALPHA_CE = 1.0      # supervised classification loss
BETA_LOGITS = 1.0   # logits KD loss
GAMMA_EMBED = 5.0   # embedding KD loss
TEMPERATURE = 2.0


# ==================== Helpers ====================
def load_audio_1s(path: str) -> np.ndarray:
    try:
        audio, _ = librosa.load(path, sr=SAMPLE_RATE, mono=True, duration=DURATION)
        if len(audio) < TARGET_LEN:
            audio = np.pad(audio, (0, TARGET_LEN - len(audio)))
        else:
            audio = audio[:TARGET_LEN]
        return audio.astype(np.float32)
    except Exception:
        return np.zeros(TARGET_LEN, dtype=np.float32)


def sample_noise_clip(noise_paths, target_len=TARGET_LEN):
    if not noise_paths:
        return None
    noise_path = np.random.choice(noise_paths)
    try:
        ns, _ = librosa.load(noise_path, sr=SAMPLE_RATE, mono=True)
        if len(ns) < target_len:
            return np.pad(ns, (0, target_len - len(ns)), mode="wrap").astype(np.float32)
        start = np.random.randint(0, len(ns) - target_len + 1)
        return ns[start:start + target_len].astype(np.float32)
    except Exception:
        return None


def mix_with_noise(clean, noise, snr_db):
    if noise is None:
        return clean
    sig_rms = np.sqrt(np.mean(clean ** 2)) + 1e-8
    noise_rms = np.sqrt(np.mean(noise ** 2)) + 1e-8
    scale = 10 ** (snr_db / 20.0)
    noisy = clean + noise * (sig_rms / scale / noise_rms)
    return noisy.astype(np.float32)


def extract_logmel(y):
    mel = librosa.feature.melspectrogram(
        y=y,
        sr=SAMPLE_RATE,
        n_fft=N_FFT,
        hop_length=HOP_LENGTH,
        center=CENTER,
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


# ==================== Generators ====================
class CleanDataGenerator(tf.keras.utils.Sequence):
    def __init__(self, filepaths, labels, batch_size, num_classes, is_training=True):
        self.filepaths = filepaths
        self.labels = labels
        self.batch_size = batch_size
        self.num_classes = num_classes
        self.is_training = is_training
        self.indexes = np.arange(len(self.filepaths))
        self.on_epoch_end()

    def __len__(self):
        return int(np.floor(len(self.filepaths) / self.batch_size))

    def on_epoch_end(self):
        if self.is_training:
            np.random.shuffle(self.indexes)

    def __getitem__(self, index):
        idxs = self.indexes[index * self.batch_size:(index + 1) * self.batch_size]
        x = np.empty((self.batch_size, N_MELS, MAX_FRAMES, 1), dtype=np.float32)
        y = np.empty(self.batch_size, dtype=np.int32)

        for i, idx in enumerate(idxs):
            clean = load_audio_1s(self.filepaths[idx])
            feat = extract_logmel(clean)
            x[i] = np.expand_dims(feat, axis=-1)
            y[i] = self.labels[idx]

        return x, tf.keras.utils.to_categorical(y, num_classes=self.num_classes)


class PairedKDGenerator(tf.keras.utils.Sequence):
    """
    Returns paired clean/noisy features from the same utterance.
    x = {"clean": clean_feat, "noisy": noisy_feat}, y = one-hot label
    """

    def __init__(
        self,
        filepaths,
        labels,
        batch_size,
        num_classes,
        noise_paths,
        is_training=True,
        snr_range=(-15.0, -5.0),
        eval_snr_db=-10.0,
    ):
        self.filepaths = filepaths
        self.labels = labels
        self.batch_size = batch_size
        self.num_classes = num_classes
        self.noise_paths = noise_paths
        self.is_training = is_training
        self.min_snr, self.max_snr = snr_range
        self.eval_snr_db = eval_snr_db
        self.indexes = np.arange(len(self.filepaths))
        self.on_epoch_end()

    def __len__(self):
        return int(np.floor(len(self.filepaths) / self.batch_size))

    def on_epoch_end(self):
        if self.is_training:
            np.random.shuffle(self.indexes)

    def __getitem__(self, index):
        idxs = self.indexes[index * self.batch_size:(index + 1) * self.batch_size]

        x_clean = np.empty((self.batch_size, N_MELS, MAX_FRAMES, 1), dtype=np.float32)
        x_noisy = np.empty((self.batch_size, N_MELS, MAX_FRAMES, 1), dtype=np.float32)
        y = np.empty(self.batch_size, dtype=np.int32)

        for i, idx in enumerate(idxs):
            clean = load_audio_1s(self.filepaths[idx])

            noise = sample_noise_clip(self.noise_paths)
            if noise is not None:
                if self.is_training and np.random.rand() < NOISE_MIX_PROB:
                    snr_db = np.random.uniform(self.min_snr, self.max_snr)
                    noisy = mix_with_noise(clean, noise, snr_db)
                else:
                    noisy = mix_with_noise(clean, noise, self.eval_snr_db)
            else:
                noisy = clean

            clean_feat = extract_logmel(clean)
            noisy_feat = extract_logmel(noisy)

            x_clean[i] = np.expand_dims(clean_feat, axis=-1)
            x_noisy[i] = np.expand_dims(noisy_feat, axis=-1)
            y[i] = self.labels[idx]

        x = {"clean": x_clean, "noisy": x_noisy}
        y_onehot = tf.keras.utils.to_categorical(y, num_classes=self.num_classes)
        return x, y_onehot


class NoisyEvalGenerator(tf.keras.utils.Sequence):
    def __init__(self, filepaths, labels, batch_size, num_classes, noise_paths, snr_db=-10.0):
        self.filepaths = filepaths
        self.labels = labels
        self.batch_size = batch_size
        self.num_classes = num_classes
        self.noise_paths = noise_paths
        self.snr_db = snr_db
        self.indexes = np.arange(len(self.filepaths))

    def __len__(self):
        return int(np.floor(len(self.filepaths) / self.batch_size))

    def __getitem__(self, index):
        idxs = self.indexes[index * self.batch_size:(index + 1) * self.batch_size]
        x = np.empty((self.batch_size, N_MELS, MAX_FRAMES, 1), dtype=np.float32)
        y = np.empty(self.batch_size, dtype=np.int32)

        for i, idx in enumerate(idxs):
            clean = load_audio_1s(self.filepaths[idx])
            noise = sample_noise_clip(self.noise_paths)
            noisy = mix_with_noise(clean, noise, self.snr_db) if noise is not None else clean

            feat = extract_logmel(noisy)
            x[i] = np.expand_dims(feat, axis=-1)
            y[i] = self.labels[idx]

        return x, tf.keras.utils.to_categorical(y, num_classes=self.num_classes)


# ==================== Distiller ====================
def build_probe_model(base_model: tf.keras.Model) -> tf.keras.Model:
    # Use the tensor right before the final softmax classifier as embedding.
    embedding_tensor = base_model.layers[-1].input
    return tf.keras.Model(base_model.input, [base_model.output, embedding_tensor], name=f"{base_model.name}_probe")


class Distiller(tf.keras.Model):
    def __init__(self, student_probe, teacher_probe, alpha, beta, gamma, temperature):
        super().__init__()
        self.student_probe = student_probe
        self.teacher_probe = teacher_probe
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.temperature = temperature

        self.loss_tracker = tf.keras.metrics.Mean(name="loss")
        self.ce_tracker = tf.keras.metrics.Mean(name="ce_loss")
        self.kd_logits_tracker = tf.keras.metrics.Mean(name="kd_logits")
        self.kd_embed_tracker = tf.keras.metrics.Mean(name="kd_embed")
        self.acc_metric = tf.keras.metrics.CategoricalAccuracy(name="accuracy")

        self.ce_fn = tf.keras.losses.CategoricalCrossentropy()
        self.kld_fn = tf.keras.losses.KLDivergence()
        self.mse_fn = tf.keras.losses.MeanSquaredError()

    @property
    def metrics(self):
        return [
            self.loss_tracker,
            self.ce_tracker,
            self.kd_logits_tracker,
            self.kd_embed_tracker,
            self.acc_metric,
        ]

    def _temperature_soften(self, probs):
        probs = tf.clip_by_value(probs, 1e-7, 1.0)
        logits = tf.math.log(probs)
        return tf.nn.softmax(logits / self.temperature, axis=-1)

    def train_step(self, data):
        x, y = data
        x_clean = x["clean"]
        x_noisy = x["noisy"]

        t_probs, t_embed = self.teacher_probe(x_clean, training=False)

        with tf.GradientTape() as tape:
            s_probs, s_embed = self.student_probe(x_noisy, training=True)

            ce_loss = self.ce_fn(y, s_probs)

            t_soft = self._temperature_soften(t_probs)
            s_soft = self._temperature_soften(s_probs)
            kd_logits = self.kld_fn(t_soft, s_soft) * (self.temperature ** 2)

            t_norm = tf.math.l2_normalize(t_embed, axis=-1)
            s_norm = tf.math.l2_normalize(s_embed, axis=-1)
            kd_embed = self.mse_fn(t_norm, s_norm)

            total_loss = self.alpha * ce_loss + self.beta * kd_logits + self.gamma * kd_embed

        grads = tape.gradient(total_loss, self.student_probe.trainable_variables)
        self.optimizer.apply_gradients(zip(grads, self.student_probe.trainable_variables))

        self.loss_tracker.update_state(total_loss)
        self.ce_tracker.update_state(ce_loss)
        self.kd_logits_tracker.update_state(kd_logits)
        self.kd_embed_tracker.update_state(kd_embed)
        self.acc_metric.update_state(y, s_probs)

        return {m.name: m.result() for m in self.metrics}

    def test_step(self, data):
        x, y = data
        x_noisy = x["noisy"]

        s_probs, _ = self.student_probe(x_noisy, training=False)
        ce_loss = self.ce_fn(y, s_probs)

        self.loss_tracker.update_state(ce_loss)
        self.ce_tracker.update_state(ce_loss)
        self.kd_logits_tracker.update_state(0.0)
        self.kd_embed_tracker.update_state(0.0)
        self.acc_metric.update_state(y, s_probs)

        return {m.name: m.result() for m in self.metrics}


# ==================== Main ====================
print("Loading dataset...")
data = np.load(PROCESSED_DATA_PATH, allow_pickle=True)
le = joblib.load(ENCODER_PATH)
class_names = le.classes_
num_classes = len(class_names)

noise_files = []
if os.path.exists(NOISE_SOURCE_DIR):
    for root, _, files in os.walk(NOISE_SOURCE_DIR):
        noise_files.extend([os.path.join(root, f) for f in files if f.lower().endswith(".wav")])
print(f"Noise dir: {NOISE_SOURCE_DIR}, files={len(noise_files)}")

# ---------- Stage 1: train clean teacher ----------
print("\n[Stage 1] Train clean teacher...")
teacher = build_model((N_MELS, MAX_FRAMES, 1), num_classes, **MODEL_KWARGS)
teacher.compile(optimizer=Adam(LEARNING_RATE), loss="categorical_crossentropy", metrics=["accuracy"])

teacher_train_gen = CleanDataGenerator(data["X_train"], data["y_train"], BATCH_SIZE, num_classes, is_training=True)
teacher_val_gen = CleanDataGenerator(data["X_val"], data["y_val"], BATCH_SIZE, num_classes, is_training=False)

class_weights = class_weight.compute_class_weight(
    class_weight="balanced",
    classes=np.unique(data["y_train"]),
    y=data["y_train"],
)
class_weight_dict = dict(enumerate(class_weights))

teacher_callbacks = [
    ModelCheckpoint(TEACHER_CKPT, save_best_only=True, monitor="val_accuracy", save_weights_only=True, verbose=1),
    EarlyStopping(patience=10, restore_best_weights=True, verbose=1),
]

teacher.fit(
    teacher_train_gen,
    validation_data=teacher_val_gen,
    epochs=TEACHER_EPOCHS,
    callbacks=teacher_callbacks,
    class_weight=class_weight_dict,
)

teacher.load_weights(TEACHER_CKPT)

# ---------- Stage 2: distill noisy student ----------
print("\n[Stage 2] Distill noisy student from clean teacher...")
student = build_model((N_MELS, MAX_FRAMES, 1), num_classes, **MODEL_KWARGS)

student.load_weights(TEACHER_CKPT)

teacher_probe = build_probe_model(teacher)
teacher_probe.trainable = False

student_probe = build_probe_model(student)

distiller = Distiller(
    student_probe=student_probe,
    teacher_probe=teacher_probe,
    alpha=ALPHA_CE,
    beta=BETA_LOGITS,
    gamma=GAMMA_EMBED,
    temperature=TEMPERATURE,
)
distiller.compile(optimizer=Adam(LEARNING_RATE))

student_train_gen = PairedKDGenerator(
    data["X_train"],
    data["y_train"],
    BATCH_SIZE,
    num_classes,
    noise_paths=noise_files,
    is_training=True,
    snr_range=(MIN_SNR_DB, MAX_SNR_DB),
    eval_snr_db=EVAL_SNR_DB,
)

student_val_gen = PairedKDGenerator(
    data["X_val"],
    data["y_val"],
    BATCH_SIZE,
    num_classes,
    noise_paths=noise_files,
    is_training=False,
    snr_range=(MIN_SNR_DB, MAX_SNR_DB),
    eval_snr_db=EVAL_SNR_DB,
)

student_callbacks = [
    EarlyStopping(patience=10, restore_best_weights=True, verbose=1),
]

_ = distiller.fit(
    student_train_gen,
    validation_data=student_val_gen,
    epochs=STUDENT_EPOCHS,
    callbacks=student_callbacks,
)

student.save_weights(STUDENT_CKPT)

# ---------- Final evaluation ----------
# ---------- Final evaluation ----------
print("\n[Evaluation] Student on clean and noisy test sets...")
clean_test_gen = CleanDataGenerator(data["X_test"], data["y_test"], BATCH_SIZE, num_classes, is_training=False)
noisy_test_gen = NoisyEvalGenerator(data["X_test"], data["y_test"], BATCH_SIZE, num_classes, noise_files, snr_db=EVAL_SNR_DB)

# 【核心修改】：在 evaluate 之前，给 student 随便配一个优化器（评估时其实用不到），但必须指定准确的 loss 和 metrics
student.compile(
    optimizer="adam", 
    loss="categorical_crossentropy", 
    metrics=["accuracy"]
)

# 现在 evaluate 就可以正常运行了
clean_metrics = student.evaluate(clean_test_gen, verbose=0)
noisy_metrics = student.evaluate(noisy_test_gen, verbose=0)
print(f"Student clean test - loss: {clean_metrics[0]:.4f}, acc: {clean_metrics[1]:.4f}")
print(f"Student noisy test (SNR={EVAL_SNR_DB}dB) - loss: {noisy_metrics[0]:.4f}, acc: {noisy_metrics[1]:.4f}")

# Classification report on noisy test
y_pred = np.argmax(student.predict(noisy_test_gen, verbose=0), axis=1)
y_true = []
for i in range(len(noisy_test_gen)):
    _, yb = noisy_test_gen[i]
    y_true.extend(np.argmax(yb, axis=1))

report = classification_report(y_true, y_pred, target_names=class_names)
report_path = os.path.join(RESULT_DIR, "classification_report_noisy.txt")
with open(report_path, "w") as f:
    f.write(report)

print(f"Saved: {TEACHER_CKPT}")
print(f"Saved: {STUDENT_CKPT}")
print(f"Saved: {report_path}")
print("Done.")
