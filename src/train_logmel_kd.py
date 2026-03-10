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


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    return int(raw) if raw is not None else default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    return float(raw) if raw is not None else default


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

MODEL_DIR = os.getenv("KD_MODEL_DIR", "saved_models/logmel_kd")
RESULT_DIR = os.getenv("KD_RESULT_DIR", "result/logmel_kd")
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

TEACHER_CKPT = os.getenv("KD_TEACHER_CKPT", os.path.join(MODEL_DIR, "teacher_clean_best.weights.h5"))
STUDENT_CKPT = os.getenv("KD_STUDENT_CKPT", os.path.join(MODEL_DIR, "student_kd_best.weights.h5"))
os.makedirs(os.path.dirname(TEACHER_CKPT), exist_ok=True)
os.makedirs(os.path.dirname(STUDENT_CKPT), exist_ok=True)


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
BATCH_SIZE = _env_int("KD_BATCH_SIZE", 32)
TEACHER_EPOCHS = _env_int("KD_TEACHER_EPOCHS", 50)
STUDENT_EPOCHS = _env_int("KD_STUDENT_EPOCHS", 50)
LEARNING_RATE = _env_float("KD_LR", 1e-4)
REUSE_TEACHER = _env_bool("KD_REUSE_TEACHER", False)
RANDOM_SEED = _env_int("KD_SEED", 42)

NOISE_MIX_PROB = 1.0
MIN_SNR_DB = -15.0
MAX_SNR_DB = -5.0
EVAL_SNR_DB = -10.0

# class-conditional prosody augmentation (for training only):
# emergency -> higher pitch + higher loudness
# other classes -> normal tone by default
ENABLE_CLASS_PROSODY_AUG = _env_bool("KD_ENABLE_CLASS_PROSODY_AUG", True)
EMERGENCY_CLASS_NAME = os.getenv("KD_EMERGENCY_CLASS_NAME", "emergency").strip().lower()
EMERGENCY_PROSODY_PROB = _env_float("KD_EMERGENCY_PROSODY_PROB", 1.0)
EMERGENCY_PITCH_MIN = _env_float("KD_EMERGENCY_PITCH_MIN", 1.5)
EMERGENCY_PITCH_MAX = _env_float("KD_EMERGENCY_PITCH_MAX", 4.0)
EMERGENCY_GAIN_DB_MIN = _env_float("KD_EMERGENCY_GAIN_DB_MIN", 3.0)
EMERGENCY_GAIN_DB_MAX = _env_float("KD_EMERGENCY_GAIN_DB_MAX", 8.0)

NON_EMERGENCY_PROSODY_PROB = _env_float("KD_NON_EMERGENCY_PROSODY_PROB", 0.0)
NON_EMERGENCY_PITCH_MIN = _env_float("KD_NON_EMERGENCY_PITCH_MIN", 0.0)
NON_EMERGENCY_PITCH_MAX = _env_float("KD_NON_EMERGENCY_PITCH_MAX", 0.0)
NON_EMERGENCY_GAIN_DB_MIN = _env_float("KD_NON_EMERGENCY_GAIN_DB_MIN", 0.0)
NON_EMERGENCY_GAIN_DB_MAX = _env_float("KD_NON_EMERGENCY_GAIN_DB_MAX", 0.0)
PROSODY_LOG_SAMPLES = _env_int("KD_PROSODY_LOG_SAMPLES", 8)

# distillation config:
#   ce_only / ce_logits / ce_embed / ce_logits_embed
DISTILL_VARIANT = os.getenv("KD_DISTILL_VARIANT", "ce_logits_embed")
ALPHA_CE = _env_float("KD_ALPHA_CE", 1.0)
LOGITS_BETA = _env_float("KD_LOGITS_BETA", 1.0)
EMBED_GAMMA_MAX = _env_float("KD_EMBED_GAMMA_MAX", 1.0)
TEMPERATURE = _env_float("KD_TEMPERATURE", 2.0)
USE_EMBED_PROJECTION = _env_bool("KD_USE_EMBED_PROJECTION", True)
EMBED_WARMUP_EPOCHS = int(STUDENT_EPOCHS * 0.3)
EMBED_RAMP_EPOCHS = max(1, STUDENT_EPOCHS - EMBED_WARMUP_EPOCHS)

np.random.seed(RANDOM_SEED)
tf.random.set_seed(RANDOM_SEED)


def resolve_distill_variant(variant: str):
    v = variant.strip().lower()
    valid = {"ce_only", "ce_logits", "ce_embed", "ce_logits_embed"}
    if v not in valid:
        raise ValueError(f"Unsupported DISTILL_VARIANT={variant}. Expected one of: {sorted(valid)}")
    use_logits = v in {"ce_logits", "ce_logits_embed"}
    use_embed = v in {"ce_embed", "ce_logits_embed"}
    beta = LOGITS_BETA if use_logits else 0.0
    gamma_max = EMBED_GAMMA_MAX if use_embed else 0.0
    return use_logits, use_embed, beta, gamma_max


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


def _normalize_label_name(name) -> str:
    return str(name).strip().lower()


def _ensure_target_len(audio: np.ndarray) -> np.ndarray:
    if len(audio) < TARGET_LEN:
        audio = np.pad(audio, (0, TARGET_LEN - len(audio)))
    elif len(audio) > TARGET_LEN:
        audio = audio[:TARGET_LEN]
    return audio.astype(np.float32)


def _sample_uniform(min_v: float, max_v: float) -> float:
    lo = float(min(min_v, max_v))
    hi = float(max(min_v, max_v))
    if np.isclose(lo, hi):
        return lo
    return float(np.random.uniform(lo, hi))


def apply_class_conditional_prosody(audio: np.ndarray, label_idx: int, class_names, is_training: bool):
    audio = _ensure_target_len(audio)
    class_name = ""
    if class_names is not None and 0 <= int(label_idx) < len(class_names):
        class_name = _normalize_label_name(class_names[int(label_idx)])
    is_emergency = class_name == EMERGENCY_CLASS_NAME

    if (not is_training) or (not ENABLE_CLASS_PROSODY_AUG):
        return audio, class_name, is_emergency, 0.0, 0.0

    if is_emergency:
        aug_prob = EMERGENCY_PROSODY_PROB
        pitch_min, pitch_max = EMERGENCY_PITCH_MIN, EMERGENCY_PITCH_MAX
        gain_min, gain_max = EMERGENCY_GAIN_DB_MIN, EMERGENCY_GAIN_DB_MAX
    else:
        aug_prob = NON_EMERGENCY_PROSODY_PROB
        pitch_min, pitch_max = NON_EMERGENCY_PITCH_MIN, NON_EMERGENCY_PITCH_MAX
        gain_min, gain_max = NON_EMERGENCY_GAIN_DB_MIN, NON_EMERGENCY_GAIN_DB_MAX

    if np.random.rand() > float(aug_prob):
        return audio, class_name, is_emergency, 0.0, 0.0

    pitch_steps = _sample_uniform(pitch_min, pitch_max)
    gain_db = _sample_uniform(gain_min, gain_max)

    augmented = audio
    if not np.isclose(pitch_steps, 0.0):
        augmented = librosa.effects.pitch_shift(y=augmented, sr=SAMPLE_RATE, n_steps=pitch_steps)

    if not np.isclose(gain_db, 0.0):
        gain_scale = float(10 ** (gain_db / 20.0))
        augmented = augmented * gain_scale

    augmented = np.clip(augmented, -1.0, 1.0)
    augmented = _ensure_target_len(augmented)
    return augmented, class_name, is_emergency, pitch_steps, gain_db


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
    def __init__(self, filepaths, labels, batch_size, num_classes, class_names=None, is_training=True):
        self.filepaths = filepaths
        self.labels = labels
        self.batch_size = batch_size
        self.num_classes = num_classes
        self.class_names = class_names
        self.is_training = is_training
        self.indexes = np.arange(len(self.filepaths))
        self._prosody_log_budget = max(0, PROSODY_LOG_SAMPLES)
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
            label_idx = int(self.labels[idx])
            clean, cls_name, is_emergency, pitch_steps, gain_db = apply_class_conditional_prosody(
                clean,
                label_idx,
                self.class_names,
                is_training=self.is_training,
            )
            if self.is_training and self._prosody_log_budget > 0 and (is_emergency or not np.isclose(pitch_steps, 0.0) or not np.isclose(gain_db, 0.0)):
                print(
                    "[ProsodyAug][Teacher] "
                    f"class={cls_name or 'unknown'} emergency={is_emergency} "
                    f"pitch_steps={pitch_steps:.2f} gain_db={gain_db:.2f}"
                )
                self._prosody_log_budget -= 1
            feat = extract_logmel(clean)
            x[i] = np.expand_dims(feat, axis=-1)
            y[i] = label_idx

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
        class_names,
        noise_paths,
        is_training=True,
        snr_range=(-15.0, -5.0),
        eval_snr_db=-10.0,
    ):
        self.filepaths = filepaths
        self.labels = labels
        self.batch_size = batch_size
        self.num_classes = num_classes
        self.class_names = class_names
        self.noise_paths = noise_paths
        self.is_training = is_training
        self.min_snr, self.max_snr = snr_range
        self.eval_snr_db = eval_snr_db
        self.indexes = np.arange(len(self.filepaths))
        self._prosody_log_budget = max(0, PROSODY_LOG_SAMPLES)
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
            label_idx = int(self.labels[idx])
            clean, cls_name, is_emergency, pitch_steps, gain_db = apply_class_conditional_prosody(
                clean,
                label_idx,
                self.class_names,
                is_training=self.is_training,
            )
            if self.is_training and self._prosody_log_budget > 0 and (is_emergency or not np.isclose(pitch_steps, 0.0) or not np.isclose(gain_db, 0.0)):
                print(
                    "[ProsodyAug][Student] "
                    f"class={cls_name or 'unknown'} emergency={is_emergency} "
                    f"pitch_steps={pitch_steps:.2f} gain_db={gain_db:.2f}"
                )
                self._prosody_log_budget -= 1

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
            y[i] = label_idx

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
    def __init__(
        self,
        student_probe,
        teacher_probe,
        alpha,
        beta,
        gamma_max,
        temperature,
        use_logits_kd=True,
        use_embed_kd=True,
        use_embed_projection=True,
    ):
        super().__init__()
        self.student_probe = student_probe
        self.teacher_probe = teacher_probe
        self.alpha = float(alpha)
        self.beta = float(beta)
        self.gamma_max = float(gamma_max)
        self.temperature = float(temperature)
        self.use_logits_kd = bool(use_logits_kd)
        self.use_embed_kd = bool(use_embed_kd)

        teacher_embed_dim = teacher_probe.output_shape[1][-1]
        self.student_embed_proj = None
        if self.use_embed_kd and use_embed_projection and teacher_embed_dim is not None:
            self.student_embed_proj = tf.keras.layers.Dense(
                int(teacher_embed_dim),
                use_bias=False,
                name="student_embed_proj",
            )

        self.current_gamma = tf.Variable(0.0, trainable=False, dtype=tf.float32, name="gamma_embed_weight")

        self.loss_tracker = tf.keras.metrics.Mean(name="loss")
        self.ce_tracker = tf.keras.metrics.Mean(name="ce_loss")
        self.kd_logits_tracker = tf.keras.metrics.Mean(name="kd_logits")
        self.kd_embed_tracker = tf.keras.metrics.Mean(name="kd_embed")
        self.gamma_tracker = tf.keras.metrics.Mean(name="gamma_embed_weight")
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
            self.gamma_tracker,
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

            kd_logits = tf.constant(0.0, dtype=tf.float32)
            if self.use_logits_kd and self.beta > 0.0:
                t_soft = self._temperature_soften(t_probs)
                s_soft = self._temperature_soften(s_probs)
                kd_logits = self.kld_fn(t_soft, s_soft) * (self.temperature ** 2)

            kd_embed = tf.constant(0.0, dtype=tf.float32)
            if self.use_embed_kd and self.gamma_max > 0.0:
                t_norm = tf.math.l2_normalize(tf.stop_gradient(t_embed), axis=-1)
                s_aligned = s_embed
                if self.student_embed_proj is not None:
                    s_aligned = self.student_embed_proj(s_aligned)
                s_norm = tf.math.l2_normalize(s_aligned, axis=-1)
                kd_embed = self.mse_fn(t_norm, s_norm)

            total_loss = self.alpha * ce_loss + self.beta * kd_logits + self.current_gamma * kd_embed

        train_vars = list(self.student_probe.trainable_variables)
        if self.student_embed_proj is not None:
            train_vars.extend(self.student_embed_proj.trainable_variables)
        grads = tape.gradient(total_loss, train_vars)
        grads_and_vars = [(g, v) for g, v in zip(grads, train_vars) if g is not None]
        if grads_and_vars:
            self.optimizer.apply_gradients(grads_and_vars)

        self.loss_tracker.update_state(total_loss)
        self.ce_tracker.update_state(ce_loss)
        self.kd_logits_tracker.update_state(kd_logits)
        self.kd_embed_tracker.update_state(kd_embed)
        self.gamma_tracker.update_state(self.current_gamma)
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
        self.gamma_tracker.update_state(self.current_gamma)
        self.acc_metric.update_state(y, s_probs)

        return {m.name: m.result() for m in self.metrics}


class EmbedWeightScheduler(tf.keras.callbacks.Callback):
    def __init__(self, distiller, enabled, gamma_max, warmup_epochs, ramp_epochs):
        super().__init__()
        self.distiller = distiller
        self.enabled = bool(enabled)
        self.gamma_max = float(gamma_max)
        self.warmup_epochs = int(max(0, warmup_epochs))
        self.ramp_epochs = int(max(1, ramp_epochs))

    def _calc_gamma(self, epoch):
        if (not self.enabled) or self.gamma_max <= 0.0:
            return 0.0
        if epoch < self.warmup_epochs:
            return 0.0
        progress = (epoch - self.warmup_epochs + 1) / float(self.ramp_epochs)
        progress = np.clip(progress, 0.0, 1.0)
        return self.gamma_max * progress

    def on_train_begin(self, logs=None):
        self.distiller.current_gamma.assign(0.0)

    def on_epoch_begin(self, epoch, logs=None):
        gamma = self._calc_gamma(epoch)
        self.distiller.current_gamma.assign(gamma)
        print(f"[KD] epoch={epoch + 1}, gamma_embed={gamma:.4f}")


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
print(
    "[Paths] "
    f"MODEL_DIR={MODEL_DIR}, RESULT_DIR={RESULT_DIR}, "
    f"TEACHER_CKPT={TEACHER_CKPT}, STUDENT_CKPT={STUDENT_CKPT}"
)
print(
    "[Seed] "
    f"KD_SEED={RANDOM_SEED}"
)
print(
    "[Prosody config] "
    f"enabled={ENABLE_CLASS_PROSODY_AUG}, "
    f"emergency_class={EMERGENCY_CLASS_NAME}, "
    f"emergency_prob={EMERGENCY_PROSODY_PROB}, "
    f"emergency_pitch=[{EMERGENCY_PITCH_MIN}, {EMERGENCY_PITCH_MAX}], "
    f"emergency_gain_db=[{EMERGENCY_GAIN_DB_MIN}, {EMERGENCY_GAIN_DB_MAX}], "
    f"non_emergency_prob={NON_EMERGENCY_PROSODY_PROB}, "
    f"non_emergency_pitch=[{NON_EMERGENCY_PITCH_MIN}, {NON_EMERGENCY_PITCH_MAX}], "
    f"non_emergency_gain_db=[{NON_EMERGENCY_GAIN_DB_MIN}, {NON_EMERGENCY_GAIN_DB_MAX}]"
)

# ---------- Stage 1: train clean teacher ----------
print("\n[Stage 1] Train clean teacher...")
teacher = build_model((N_MELS, MAX_FRAMES, 1), num_classes, **MODEL_KWARGS)
if REUSE_TEACHER and os.path.exists(TEACHER_CKPT):
    print(f"[Stage 1] Reusing existing teacher checkpoint: {TEACHER_CKPT}")
    teacher.load_weights(TEACHER_CKPT)
else:
    teacher.compile(optimizer=Adam(LEARNING_RATE), loss="categorical_crossentropy", metrics=["accuracy"])

    teacher_train_gen = CleanDataGenerator(
        data["X_train"],
        data["y_train"],
        BATCH_SIZE,
        num_classes,
        class_names=class_names,
        is_training=True,
    )
    teacher_val_gen = CleanDataGenerator(
        data["X_val"],
        data["y_val"],
        BATCH_SIZE,
        num_classes,
        class_names=class_names,
        is_training=False,
    )

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

use_logits_kd, use_embed_kd, beta_logits, gamma_embed_max = resolve_distill_variant(DISTILL_VARIANT)
print(
    "[KD config] "
    f"variant={DISTILL_VARIANT}, "
    f"use_logits={use_logits_kd}, "
    f"use_embed={use_embed_kd}, "
    f"beta={beta_logits}, "
    f"gamma_max={gamma_embed_max}, "
    f"embed_proj={USE_EMBED_PROJECTION}, "
    f"warmup_epochs={EMBED_WARMUP_EPOCHS}, "
    f"ramp_epochs={EMBED_RAMP_EPOCHS}"
)

distiller = Distiller(
    student_probe=student_probe,
    teacher_probe=teacher_probe,
    alpha=ALPHA_CE,
    beta=beta_logits,
    gamma_max=gamma_embed_max,
    temperature=TEMPERATURE,
    use_logits_kd=use_logits_kd,
    use_embed_kd=use_embed_kd,
    use_embed_projection=USE_EMBED_PROJECTION,
)
distiller.compile(optimizer=Adam(LEARNING_RATE))

student_train_gen = PairedKDGenerator(
    data["X_train"],
    data["y_train"],
    BATCH_SIZE,
    num_classes,
    class_names=class_names,
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
    class_names=class_names,
    noise_paths=noise_files,
    is_training=False,
    snr_range=(MIN_SNR_DB, MAX_SNR_DB),
    eval_snr_db=EVAL_SNR_DB,
)

student_callbacks = [
    EmbedWeightScheduler(
        distiller=distiller,
        enabled=use_embed_kd,
        gamma_max=gamma_embed_max,
        warmup_epochs=EMBED_WARMUP_EPOCHS,
        ramp_epochs=EMBED_RAMP_EPOCHS,
    ),
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
clean_test_gen = CleanDataGenerator(
    data["X_test"],
    data["y_test"],
    BATCH_SIZE,
    num_classes,
    class_names=class_names,
    is_training=False,
)
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
