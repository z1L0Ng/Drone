import os
import json
import numpy as np
import tensorflow as tf
import librosa
import joblib

from keras.optimizers import Adam
from keras.callbacks import ModelCheckpoint, EarlyStopping
from sklearn.utils import class_weight
from sklearn.metrics import classification_report

from model import build_model
from model_config import get_model_kwargs
from logmel_frontend_shared import extract_logmel as shared_extract_logmel


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


def _env_optional_int(name: str):
    raw = os.getenv(name)
    if raw is None:
        return None
    value = int(raw)
    return value if value > 0 else None


def _env_int_tuple(name: str, default):
    raw = os.getenv(name)
    if raw is None:
        return tuple(int(x) for x in default)
    vals = []
    for part in raw.split(","):
        p = part.strip()
        if not p:
            continue
        vals.append(int(p))
    if not vals:
        return tuple(int(x) for x in default)
    return tuple(vals)


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
HISTORY_DIR = os.getenv("KD_HISTORY_DIR", RESULT_DIR)
os.makedirs(HISTORY_DIR, exist_ok=True)

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

# ==================== Aux stats branch ====================
USE_STATS_BRANCH = _env_bool("KD_USE_STATS_BRANCH", True)
STATS_DIM = _env_int("KD_STATS_DIM", 4)
STATS_MLP_UNITS = _env_int_tuple("KD_STATS_MLP_UNITS", (32, 16))
FUSE_UNITS = _env_int("KD_FUSE_UNITS", 128)
FUSION_MODE = os.getenv("KD_FUSION_MODE", "concat").strip().lower()
GATE_UNITS = _env_int("KD_GATE_UNITS", 16)
TEACHER_USE_STATS_BRANCH = _env_bool("KD_TEACHER_USE_STATS_BRANCH", USE_STATS_BRANCH)
TEACHER_STATS_DIM = _env_int("KD_TEACHER_STATS_DIM", STATS_DIM)
TEACHER_STATS_MLP_UNITS = _env_int_tuple("KD_TEACHER_STATS_MLP_UNITS", STATS_MLP_UNITS)
TEACHER_FUSE_UNITS = _env_int("KD_TEACHER_FUSE_UNITS", FUSE_UNITS)
TEACHER_FUSION_MODE = os.getenv("KD_TEACHER_FUSION_MODE", "concat").strip().lower()
TEACHER_GATE_UNITS = _env_int("KD_TEACHER_GATE_UNITS", GATE_UNITS)
PITCH_FMIN = _env_float("KD_STATS_PITCH_FMIN", 50.0)
PITCH_FMAX = _env_float("KD_STATS_PITCH_FMAX", 500.0)
AUX_LOSS_ALPHA = _env_float("KD_AUX_ALPHA", 0.2)
AUX_MODE = os.getenv("KD_AUX_MODE", "embed_align").strip().lower()
AUX_LOSS_TYPE = os.getenv("KD_AUX_LOSS_TYPE", "huber").strip().lower()


# ==================== Train config ====================
BATCH_SIZE = _env_int("KD_BATCH_SIZE", 32)
TEACHER_EPOCHS = _env_int("KD_TEACHER_EPOCHS", 50)
STUDENT_EPOCHS = _env_int("KD_STUDENT_EPOCHS", 50)
LEARNING_RATE = _env_float("KD_LR", 1e-4)
REUSE_TEACHER = _env_bool("KD_REUSE_TEACHER", False)
STRICT_REUSE_TEACHER_SHAPE = _env_bool("KD_STRICT_REUSE_TEACHER_SHAPE", True)
RANDOM_SEED = _env_int("KD_SEED", 42)
TEACHER_MODEL_PROFILE = os.getenv("KD_TEACHER_MODEL_PROFILE", "base").strip().lower()
STUDENT_MODEL_PROFILE = os.getenv("KD_STUDENT_MODEL_PROFILE", "base").strip().lower()
STUDENT_INIT_MODE = os.getenv("KD_STUDENT_INIT_MODE", "auto").strip().lower()
STUDENT_INIT_CKPT = os.getenv("KD_STUDENT_INIT_CKPT", "").strip() or None

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
EMERGENCY_PITCH_MIN = _env_float("KD_EMERGENCY_PITCH_MIN", 2.0)
EMERGENCY_PITCH_MAX = _env_float("KD_EMERGENCY_PITCH_MAX", 5.0)
EMERGENCY_GAIN_DB_MIN = _env_float("KD_EMERGENCY_GAIN_DB_MIN", 6.0)
EMERGENCY_GAIN_DB_MAX = _env_float("KD_EMERGENCY_GAIN_DB_MAX", 10.0)

NON_EMERGENCY_PROSODY_PROB = _env_float("KD_NON_EMERGENCY_PROSODY_PROB", 0.0)
NON_EMERGENCY_PITCH_MIN = _env_float("KD_NON_EMERGENCY_PITCH_MIN", 0.0)
NON_EMERGENCY_PITCH_MAX = _env_float("KD_NON_EMERGENCY_PITCH_MAX", 0.0)
NON_EMERGENCY_GAIN_DB_MIN = _env_float("KD_NON_EMERGENCY_GAIN_DB_MIN", 0.0)
NON_EMERGENCY_GAIN_DB_MAX = _env_float("KD_NON_EMERGENCY_GAIN_DB_MAX", 0.0)
PROSODY_LOG_SAMPLES = _env_int("KD_PROSODY_LOG_SAMPLES", 0)
TEACHER_ENABLE_PROSODY_AUG = _env_bool("KD_TEACHER_ENABLE_PROSODY_AUG", False)
STUDENT_ENABLE_PROSODY_AUG = _env_bool("KD_STUDENT_ENABLE_PROSODY_AUG", True)
FIT_VERBOSE = _env_int("KD_FIT_VERBOSE", 2)
GAMMA_LOG_VERBOSE = _env_bool("KD_GAMMA_LOG_VERBOSE", False)
EARLYSTOP_PATIENCE = _env_int("KD_EARLYSTOP_PATIENCE", 10)
TEACHER_MONITOR = os.getenv("KD_TEACHER_MONITOR", "val_accuracy")
STUDENT_MONITOR = os.getenv("KD_STUDENT_MONITOR", "val_accuracy")
TEACHER_STEPS_PER_EPOCH = _env_optional_int("KD_TEACHER_STEPS_PER_EPOCH")
TEACHER_VAL_STEPS = _env_optional_int("KD_TEACHER_VAL_STEPS")
STUDENT_STEPS_PER_EPOCH = _env_optional_int("KD_STUDENT_STEPS_PER_EPOCH")
STUDENT_VAL_STEPS = _env_optional_int("KD_STUDENT_VAL_STEPS")
EVAL_STEPS = _env_optional_int("KD_EVAL_STEPS")
SKIP_FINAL_EVAL = _env_bool("KD_SKIP_FINAL_EVAL", False)
SAVE_TRAIN_HISTORY = _env_bool("KD_SAVE_TRAIN_HISTORY", True)
SAVE_RUN_CONFIG = _env_bool("KD_SAVE_RUN_CONFIG", True)

# distillation config:
#   ce_only / ce_logits / ce_embed / ce_logits_embed / embed_only
DISTILL_VARIANT = os.getenv("KD_DISTILL_VARIANT", "ce_logits_embed")
ALPHA_CE = _env_float("KD_ALPHA_CE", 1.0)
LOGITS_BETA = _env_float("KD_LOGITS_BETA", 1.0)
EMBED_GAMMA_MAX = _env_float("KD_EMBED_GAMMA_MAX", 1.0)
TEMPERATURE = _env_float("KD_TEMPERATURE", 2.0)
USE_EMBED_PROJECTION = _env_bool("KD_USE_EMBED_PROJECTION", True)
EMBED_WARMUP_EPOCHS = int(STUDENT_EPOCHS * 0.3)
EMBED_RAMP_EPOCHS = max(1, STUDENT_EPOCHS - EMBED_WARMUP_EPOCHS)

# optional teacher-guided clean prewarm before noisy KD
PREWARM_EPOCHS = _env_int("KD_PREWARM_EPOCHS", 0)
PREWARM_LR = _env_float("KD_PREWARM_LR", LEARNING_RATE)
PREWARM_ALPHA_CE = _env_float("KD_PREWARM_ALPHA_CE", 1.0)
PREWARM_LOGITS_BETA = _env_float("KD_PREWARM_LOGITS_BETA", 1.0)
PREWARM_TEMPERATURE = _env_float("KD_PREWARM_TEMPERATURE", 2.0)
PREWARM_USE_CE = _env_bool("KD_PREWARM_USE_CE", True)
PREWARM_USE_LOGITS = _env_bool("KD_PREWARM_USE_LOGITS", True)
PREWARM_ENABLE_PROSODY_AUG = _env_bool("KD_PREWARM_ENABLE_PROSODY_AUG", False)
PREWARM_PATIENCE = _env_int("KD_PREWARM_PATIENCE", 5)
PREWARM_MONITOR = os.getenv("KD_PREWARM_MONITOR", "val_accuracy")
PREWARM_STEPS_PER_EPOCH = _env_optional_int("KD_PREWARM_STEPS_PER_EPOCH")
PREWARM_VAL_STEPS = _env_optional_int("KD_PREWARM_VAL_STEPS")

TEACHER_MODEL_KWARGS = get_model_kwargs(TEACHER_MODEL_PROFILE)
STUDENT_MODEL_KWARGS = get_model_kwargs(STUDENT_MODEL_PROFILE)
if STUDENT_INIT_MODE not in {"auto", "teacher", "random"}:
    raise ValueError("KD_STUDENT_INIT_MODE must be one of: auto, teacher, random")
if FUSION_MODE not in {"concat", "gated"}:
    raise ValueError("KD_FUSION_MODE must be one of: concat, gated")
if TEACHER_FUSION_MODE not in {"concat", "gated"}:
    raise ValueError("KD_TEACHER_FUSION_MODE must be one of: concat, gated")
if AUX_MODE not in {"embed_align", "stats_reg"}:
    raise ValueError("KD_AUX_MODE must be one of: embed_align, stats_reg")
if AUX_LOSS_TYPE not in {"huber", "mse"}:
    raise ValueError("KD_AUX_LOSS_TYPE must be one of: huber, mse")

np.random.seed(RANDOM_SEED)
tf.random.set_seed(RANDOM_SEED)


def resolve_distill_variant(variant: str):
    v = variant.strip().lower()
    valid = {"ce_only", "ce_logits", "ce_embed", "ce_logits_embed", "embed_only"}
    if v not in valid:
        raise ValueError(f"Unsupported DISTILL_VARIANT={variant}. Expected one of: {sorted(valid)}")

    use_ce = v in {"ce_only", "ce_logits", "ce_embed", "ce_logits_embed"}
    use_logits = v in {"ce_logits", "ce_logits_embed"}
    use_embed = v in {"ce_embed", "ce_logits_embed", "embed_only"}
    alpha = ALPHA_CE if use_ce else 0.0
    beta = LOGITS_BETA if use_logits else 0.0
    gamma_max = EMBED_GAMMA_MAX if use_embed else 0.0
    warmup_epochs = EMBED_WARMUP_EPOCHS if v != "embed_only" else 0
    return use_ce, use_logits, use_embed, alpha, beta, gamma_max, warmup_epochs


def _fmt_model_kwargs(kwargs: dict) -> str:
    keys = [
        "num_layers",
        "conv_filters",
        "head_size",
        "num_heads",
        "ff_dim",
        "dropout_rate",
        "fnn_units",
        "branchformer_time_pool",
        "branchformer_bottleneck_dim",
    ]
    parts = []
    for key in keys:
        if key in kwargs:
            parts.append(f"{key}={kwargs[key]}")
    return ", ".join(parts)


def _with_stats_kwargs(base_kwargs: dict, role: str = "student") -> dict:
    role_norm = str(role).strip().lower()
    kwargs = dict(base_kwargs)
    if role_norm == "teacher":
        kwargs["use_stats_branch"] = TEACHER_USE_STATS_BRANCH
        kwargs["stats_dim"] = TEACHER_STATS_DIM
        kwargs["stats_mlp_units"] = TEACHER_STATS_MLP_UNITS
        kwargs["fuse_units"] = TEACHER_FUSE_UNITS
        kwargs["fusion_mode"] = TEACHER_FUSION_MODE
        kwargs["gate_units"] = TEACHER_GATE_UNITS
    else:
        kwargs["use_stats_branch"] = USE_STATS_BRANCH
        kwargs["stats_dim"] = STATS_DIM
        kwargs["stats_mlp_units"] = STATS_MLP_UNITS
        kwargs["fuse_units"] = FUSE_UNITS
        kwargs["fusion_mode"] = FUSION_MODE
        kwargs["gate_units"] = GATE_UNITS
    return kwargs


def initialize_student_weights(student_model: tf.keras.Model) -> str:
    if STUDENT_INIT_CKPT:
        if os.path.exists(STUDENT_INIT_CKPT):
            student_model.load_weights(STUDENT_INIT_CKPT)
            return f"student_ckpt:{STUDENT_INIT_CKPT}"
        raise FileNotFoundError(f"KD_STUDENT_INIT_CKPT does not exist: {STUDENT_INIT_CKPT}")

    same_profile = TEACHER_MODEL_PROFILE == STUDENT_MODEL_PROFILE

    if STUDENT_INIT_MODE == "random":
        return "random_init"

    if STUDENT_INIT_MODE == "teacher":
        if not same_profile:
            raise ValueError(
                "KD_STUDENT_INIT_MODE=teacher requires same teacher/student profile. "
                f"Got teacher={TEACHER_MODEL_PROFILE}, student={STUDENT_MODEL_PROFILE}"
            )
        student_model.load_weights(TEACHER_CKPT)
        return f"teacher_ckpt:{TEACHER_CKPT}"

    # auto
    if same_profile and os.path.exists(TEACHER_CKPT):
        try:
            student_model.load_weights(TEACHER_CKPT)
            return f"teacher_ckpt:{TEACHER_CKPT}"
        except Exception as exc:
            print(f"[Stage 2] Auto teacher init failed, fallback to random init: {exc}")
    return "random_init"


# ==================== Helpers ====================
def _save_history_csv(history_obj, out_path: str):
    if history_obj is None:
        return
    hist = getattr(history_obj, "history", None)
    if not hist:
        return
    keys = sorted(hist.keys())
    n = max(len(hist[k]) for k in keys)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("epoch," + ",".join(keys) + "\n")
        for i in range(n):
            vals = []
            for k in keys:
                v = hist[k][i] if i < len(hist[k]) else ""
                vals.append(str(float(v)) if v != "" else "")
            f.write(f"{i + 1}," + ",".join(vals) + "\n")


def _dump_run_config(out_path: str):
    config = {
        "paths": {
            "processed_data_path": PROCESSED_DATA_PATH,
            "encoder_path": ENCODER_PATH,
            "noise_source_dir": NOISE_SOURCE_DIR,
            "model_dir": MODEL_DIR,
            "result_dir": RESULT_DIR,
            "history_dir": HISTORY_DIR,
            "teacher_ckpt": TEACHER_CKPT,
            "student_ckpt": STUDENT_CKPT,
        },
        "train": {
            "batch_size": BATCH_SIZE,
            "teacher_epochs": TEACHER_EPOCHS,
            "student_epochs": STUDENT_EPOCHS,
            "learning_rate": LEARNING_RATE,
            "reuse_teacher": REUSE_TEACHER,
            "strict_reuse_teacher_shape": STRICT_REUSE_TEACHER_SHAPE,
            "random_seed": RANDOM_SEED,
            "teacher_model_profile": TEACHER_MODEL_PROFILE,
            "student_model_profile": STUDENT_MODEL_PROFILE,
            "student_init_mode": STUDENT_INIT_MODE,
            "student_init_ckpt": STUDENT_INIT_CKPT,
            "earlystop_patience": EARLYSTOP_PATIENCE,
            "teacher_monitor": TEACHER_MONITOR,
            "student_monitor": STUDENT_MONITOR,
        },
        "stats_branch": {
            "teacher": {
                "use_stats_branch": TEACHER_USE_STATS_BRANCH,
                "stats_dim": TEACHER_STATS_DIM,
                "stats_mlp_units": list(TEACHER_STATS_MLP_UNITS),
                "fuse_units": TEACHER_FUSE_UNITS,
                "fusion_mode": TEACHER_FUSION_MODE,
                "gate_units": TEACHER_GATE_UNITS,
            },
            "student": {
                "use_stats_branch": USE_STATS_BRANCH,
                "stats_dim": STATS_DIM,
                "stats_mlp_units": list(STATS_MLP_UNITS),
                "fuse_units": FUSE_UNITS,
                "fusion_mode": FUSION_MODE,
                "gate_units": GATE_UNITS,
            },
            "pitch_fmin": PITCH_FMIN,
            "pitch_fmax": PITCH_FMAX,
        },
        "noise": {
            "noise_mix_prob": NOISE_MIX_PROB,
            "min_snr_db": MIN_SNR_DB,
            "max_snr_db": MAX_SNR_DB,
            "eval_snr_db": EVAL_SNR_DB,
        },
        "prosody": {
            "enable_class_prosody_aug": ENABLE_CLASS_PROSODY_AUG,
            "teacher_enable_prosody_aug": TEACHER_ENABLE_PROSODY_AUG,
            "student_enable_prosody_aug": STUDENT_ENABLE_PROSODY_AUG,
            "emergency_class_name": EMERGENCY_CLASS_NAME,
            "emergency_prob": EMERGENCY_PROSODY_PROB,
            "emergency_pitch_min": EMERGENCY_PITCH_MIN,
            "emergency_pitch_max": EMERGENCY_PITCH_MAX,
            "emergency_gain_db_min": EMERGENCY_GAIN_DB_MIN,
            "emergency_gain_db_max": EMERGENCY_GAIN_DB_MAX,
            "non_emergency_prob": NON_EMERGENCY_PROSODY_PROB,
            "non_emergency_pitch_min": NON_EMERGENCY_PITCH_MIN,
            "non_emergency_pitch_max": NON_EMERGENCY_PITCH_MAX,
            "non_emergency_gain_db_min": NON_EMERGENCY_GAIN_DB_MIN,
            "non_emergency_gain_db_max": NON_EMERGENCY_GAIN_DB_MAX,
        },
        "distillation": {
            "variant": DISTILL_VARIANT,
            "alpha_ce": ALPHA_CE,
            "logits_beta": LOGITS_BETA,
            "embed_gamma_max": EMBED_GAMMA_MAX,
            "temperature": TEMPERATURE,
            "use_embed_projection": USE_EMBED_PROJECTION,
            "embed_warmup_epochs": EMBED_WARMUP_EPOCHS,
            "embed_ramp_epochs": EMBED_RAMP_EPOCHS,
        },
        "aux_loss": {
            "aux_alpha": AUX_LOSS_ALPHA,
            "aux_mode": AUX_MODE,
            "aux_loss_type": AUX_LOSS_TYPE,
        },
        "prewarm": {
            "prewarm_epochs": PREWARM_EPOCHS,
            "prewarm_lr": PREWARM_LR,
            "prewarm_alpha_ce": PREWARM_ALPHA_CE,
            "prewarm_logits_beta": PREWARM_LOGITS_BETA,
            "prewarm_temperature": PREWARM_TEMPERATURE,
            "prewarm_use_ce": PREWARM_USE_CE,
            "prewarm_use_logits": PREWARM_USE_LOGITS,
            "prewarm_enable_prosody_aug": PREWARM_ENABLE_PROSODY_AUG,
            "prewarm_patience": PREWARM_PATIENCE,
            "prewarm_monitor": PREWARM_MONITOR,
        },
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=True, indent=2)


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


def apply_class_conditional_prosody(
    audio: np.ndarray,
    label_idx: int,
    class_names,
    is_training: bool,
    enable_aug: bool = True,
):
    audio = _ensure_target_len(audio)
    class_name = ""
    if class_names is not None and 0 <= int(label_idx) < len(class_names):
        class_name = _normalize_label_name(class_names[int(label_idx)])
    is_emergency = class_name == EMERGENCY_CLASS_NAME

    if (not is_training) or (not ENABLE_CLASS_PROSODY_AUG) or (not enable_aug):
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
    return shared_extract_logmel(y)


def extract_stats_features(y):
    y = _ensure_target_len(y)
    rms = librosa.feature.rms(
        y=y,
        frame_length=N_FFT,
        hop_length=HOP_LENGTH,
        center=CENTER,
    )[0].astype(np.float32)
    energy_env_std = float(np.std(rms)) if rms.size > 0 else 0.0

    try:
        pitch = librosa.yin(
            y=y,
            fmin=max(1.0, float(PITCH_FMIN)),
            fmax=max(float(PITCH_FMIN) + 1.0, float(PITCH_FMAX)),
            sr=SAMPLE_RATE,
            frame_length=N_FFT,
            hop_length=HOP_LENGTH,
            center=CENTER,
        ).astype(np.float32)
    except Exception:
        pitch = np.full_like(rms, np.nan, dtype=np.float32)

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
    if int(STATS_DIM) == stats.shape[0]:
        return stats
    out = np.zeros((int(STATS_DIM),), dtype=np.float32)
    n = min(out.shape[0], stats.shape[0])
    out[:n] = stats[:n]
    return out


# ==================== Generators ====================
class CleanDataGenerator(tf.keras.utils.Sequence):
    def __init__(
        self,
        filepaths,
        labels,
        batch_size,
        num_classes,
        class_names=None,
        is_training=True,
        enable_prosody_aug=True,
    ):
        self.filepaths = filepaths
        self.labels = labels
        self.batch_size = batch_size
        self.num_classes = num_classes
        self.class_names = class_names
        self.is_training = is_training
        self.enable_prosody_aug = enable_prosody_aug
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
        x_mel = np.empty((self.batch_size, N_MELS, MAX_FRAMES, 1), dtype=np.float32)
        x_stats = np.empty((self.batch_size, STATS_DIM), dtype=np.float32) if USE_STATS_BRANCH else None
        y = np.empty(self.batch_size, dtype=np.int32)

        for i, idx in enumerate(idxs):
            clean = load_audio_1s(self.filepaths[idx])
            label_idx = int(self.labels[idx])
            clean, cls_name, is_emergency, pitch_steps, gain_db = apply_class_conditional_prosody(
                clean,
                label_idx,
                self.class_names,
                is_training=self.is_training,
                enable_aug=self.enable_prosody_aug,
            )
            if self.is_training and self._prosody_log_budget > 0 and (not np.isclose(pitch_steps, 0.0) or not np.isclose(gain_db, 0.0)):
                print(
                    "[ProsodyAug][Teacher] "
                    f"class={cls_name or 'unknown'} emergency={is_emergency} "
                    f"pitch_steps={pitch_steps:.2f} gain_db={gain_db:.2f}"
                )
                self._prosody_log_budget -= 1
            feat = extract_logmel(clean)
            x_mel[i] = np.expand_dims(feat, axis=-1)
            if USE_STATS_BRANCH:
                x_stats[i] = extract_stats_features(clean)
            y[i] = label_idx

        x = (x_mel, x_stats) if USE_STATS_BRANCH else x_mel
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
        enable_prosody_aug=True,
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
        self.enable_prosody_aug = enable_prosody_aug
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

        x_clean_mel = np.empty((self.batch_size, N_MELS, MAX_FRAMES, 1), dtype=np.float32)
        x_noisy_mel = np.empty((self.batch_size, N_MELS, MAX_FRAMES, 1), dtype=np.float32)
        x_clean_stats = np.empty((self.batch_size, STATS_DIM), dtype=np.float32) if USE_STATS_BRANCH else None
        x_noisy_stats = np.empty((self.batch_size, STATS_DIM), dtype=np.float32) if USE_STATS_BRANCH else None
        y = np.empty(self.batch_size, dtype=np.int32)

        for i, idx in enumerate(idxs):
            clean = load_audio_1s(self.filepaths[idx])
            label_idx = int(self.labels[idx])
            # Apply prosody once, then derive both teacher-clean and student-noisy from it
            # to keep teacher/student aligned on the same underlying utterance.
            clean, cls_name, is_emergency, pitch_steps, gain_db = apply_class_conditional_prosody(
                clean,
                label_idx,
                self.class_names,
                is_training=self.is_training,
                enable_aug=self.enable_prosody_aug,
            )
            if self.is_training and self._prosody_log_budget > 0 and (not np.isclose(pitch_steps, 0.0) or not np.isclose(gain_db, 0.0)):
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

            x_clean_mel[i] = np.expand_dims(clean_feat, axis=-1)
            x_noisy_mel[i] = np.expand_dims(noisy_feat, axis=-1)
            if USE_STATS_BRANCH:
                x_clean_stats[i] = extract_stats_features(clean)
                x_noisy_stats[i] = extract_stats_features(noisy)
            y[i] = label_idx

        if USE_STATS_BRANCH:
            x = {
                "clean": (x_clean_mel, x_clean_stats),
                "noisy": (x_noisy_mel, x_noisy_stats),
            }
        else:
            x = {"clean": x_clean_mel, "noisy": x_noisy_mel}
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
        x_mel = np.empty((self.batch_size, N_MELS, MAX_FRAMES, 1), dtype=np.float32)
        x_stats = np.empty((self.batch_size, STATS_DIM), dtype=np.float32) if USE_STATS_BRANCH else None
        y = np.empty(self.batch_size, dtype=np.int32)

        for i, idx in enumerate(idxs):
            clean = load_audio_1s(self.filepaths[idx])
            noise = sample_noise_clip(self.noise_paths)
            noisy = mix_with_noise(clean, noise, self.snr_db) if noise is not None else clean

            feat = extract_logmel(noisy)
            x_mel[i] = np.expand_dims(feat, axis=-1)
            if USE_STATS_BRANCH:
                x_stats[i] = extract_stats_features(noisy)
            y[i] = self.labels[idx]

        x = (x_mel, x_stats) if USE_STATS_BRANCH else x_mel
        return x, tf.keras.utils.to_categorical(y, num_classes=self.num_classes)


# ==================== Distiller ====================
def build_probe_model(base_model: tf.keras.Model) -> tf.keras.Model:
    # Main probability output + embeddings used by KD and auxiliary branch loss.
    probs = base_model.output
    fused_embed = base_model.get_layer("fused_embed").output if "fused_embed" in [l.name for l in base_model.layers] else base_model.layers[-1].input
    mel_embed = base_model.get_layer("mel_embed").output if "mel_embed" in [l.name for l in base_model.layers] else fused_embed
    outputs = [probs, fused_embed, mel_embed]
    if "stats_embed" in [l.name for l in base_model.layers]:
        outputs.append(base_model.get_layer("stats_embed").output)
    return tf.keras.Model(base_model.input, outputs, name=f"{base_model.name}_probe")


class Distiller(tf.keras.Model):
    def __init__(
        self,
        student_probe,
        teacher_probe,
        alpha,
        beta,
        gamma_max,
        temperature,
        use_ce=True,
        use_logits_kd=True,
        use_embed_kd=True,
        use_embed_projection=True,
        aux_alpha=0.0,
        aux_mode="embed_align",
        aux_loss_type="huber",
        stats_dim=4,
    ):
        super().__init__()
        self.student_probe = student_probe
        self.teacher_probe = teacher_probe
        self.alpha = float(alpha)
        self.beta = float(beta)
        self.gamma_max = float(gamma_max)
        self.temperature = float(temperature)
        self.use_ce = bool(use_ce)
        self.use_logits_kd = bool(use_logits_kd)
        self.use_embed_kd = bool(use_embed_kd)
        self.aux_alpha = float(max(0.0, aux_alpha))
        self.aux_mode = str(aux_mode).strip().lower()
        self.aux_loss_type = str(aux_loss_type).strip().lower()
        self.stats_dim = int(stats_dim)
        if self.aux_mode not in {"embed_align", "stats_reg"}:
            raise ValueError(f"Unsupported aux_mode={self.aux_mode}, expected one of: embed_align, stats_reg")
        if self.aux_loss_type not in {"huber", "mse"}:
            raise ValueError(f"Unsupported aux_loss_type={self.aux_loss_type}, expected one of: huber, mse")

        teacher_embed_dim = teacher_probe.output_shape[1][-1] if len(teacher_probe.output_shape) > 1 else None
        student_embed_dim = student_probe.output_shape[1][-1] if len(student_probe.output_shape) > 1 else None
        self.student_embed_proj = None
        if (
            self.use_embed_kd
            and use_embed_projection
            and teacher_embed_dim is not None
            and student_embed_dim is not None
            and int(student_embed_dim) != int(teacher_embed_dim)
        ):
            self.student_embed_proj = tf.keras.layers.Dense(
                int(teacher_embed_dim),
                use_bias=False,
                name="student_embed_proj",
            )

        self.stats_to_mel_proj = None
        has_stats_student = len(student_probe.output_shape) > 3
        if self.aux_mode == "embed_align" and has_stats_student:
            mel_dim = student_probe.output_shape[2][-1]
            stats_dim = student_probe.output_shape[3][-1]
            if mel_dim is not None and stats_dim is not None and int(mel_dim) != int(stats_dim):
                self.stats_to_mel_proj = tf.keras.layers.Dense(
                    int(mel_dim),
                    use_bias=False,
                    name="stats_to_mel_proj",
                )
        self.stats_reg_head = None
        if self.aux_mode == "stats_reg":
            self.stats_reg_head = tf.keras.layers.Dense(self.stats_dim, activation="linear", name="stats_reg_head")

        self.current_gamma = tf.Variable(0.0, trainable=False, dtype=tf.float32, name="gamma_embed_weight")

        self.loss_tracker = tf.keras.metrics.Mean(name="loss")
        self.cls_loss_tracker = tf.keras.metrics.Mean(name="cls_loss")
        self.ce_tracker = tf.keras.metrics.Mean(name="ce_loss")
        self.kd_logits_tracker = tf.keras.metrics.Mean(name="kd_logits")
        self.kd_embed_tracker = tf.keras.metrics.Mean(name="kd_embed")
        self.aux_tracker = tf.keras.metrics.Mean(name="aux_loss")
        self.gamma_tracker = tf.keras.metrics.Mean(name="gamma_embed_weight")
        self.acc_metric = tf.keras.metrics.CategoricalAccuracy(name="accuracy")

        self.ce_fn = tf.keras.losses.CategoricalCrossentropy()
        self.kld_fn = tf.keras.losses.KLDivergence()
        self.mse_fn = tf.keras.losses.MeanSquaredError()
        self.huber_fn = tf.keras.losses.Huber()

    @property
    def metrics(self):
        return [
            self.loss_tracker,
            self.cls_loss_tracker,
            self.ce_tracker,
            self.kd_logits_tracker,
            self.kd_embed_tracker,
            self.aux_tracker,
            self.gamma_tracker,
            self.acc_metric,
        ]

    def _temperature_soften(self, probs):
        probs = tf.clip_by_value(probs, 1e-7, 1.0)
        logits = tf.math.log(probs)
        return tf.nn.softmax(logits / self.temperature, axis=-1)

    def _unpack_probe_outputs(self, outputs):
        if not isinstance(outputs, (list, tuple)):
            return outputs, outputs, outputs, None
        probs = outputs[0]
        embed = outputs[1] if len(outputs) > 1 else probs
        mel_embed = outputs[2] if len(outputs) > 2 else embed
        stats_embed = outputs[3] if len(outputs) > 3 else None
        return probs, embed, mel_embed, stats_embed

    def _extract_stats_target(self, x_input):
        if isinstance(x_input, (list, tuple)) and len(x_input) >= 2:
            return tf.cast(x_input[1], tf.float32)
        if isinstance(x_input, dict):
            for key in ("stats", "x_stats"):
                if key in x_input:
                    return tf.cast(x_input[key], tf.float32)
        return None

    def _adapt_input_for_model(self, x_input, model_obj):
        # Teacher and student may expose different input arity (e.g. teacher mel-only, student mel+stats).
        expected_inputs = len(tf.nest.flatten(model_obj.inputs))
        if expected_inputs <= 1:
            if isinstance(x_input, (list, tuple)):
                return x_input[0]
            return x_input
        if isinstance(x_input, (list, tuple)):
            return tuple(x_input[:expected_inputs])
        return x_input

    def _calc_aux_loss(self, mel_embed, stats_embed, stats_target):
        if self.aux_alpha <= 0.0:
            return tf.constant(0.0, dtype=tf.float32)
        if self.aux_mode == "stats_reg":
            if stats_target is None or self.stats_reg_head is None:
                return tf.constant(0.0, dtype=tf.float32)
            stats_hat = self.stats_reg_head(mel_embed)
            target = tf.stop_gradient(tf.cast(stats_target, tf.float32))
            if self.aux_loss_type == "huber":
                return self.huber_fn(target, stats_hat)
            return self.mse_fn(target, stats_hat)
        if stats_embed is None:
            return tf.constant(0.0, dtype=tf.float32)
        mel_norm = tf.math.l2_normalize(mel_embed, axis=-1)
        stats_aligned = stats_embed
        if self.stats_to_mel_proj is not None:
            stats_aligned = self.stats_to_mel_proj(stats_aligned)
        stats_norm = tf.math.l2_normalize(stats_aligned, axis=-1)
        return self.mse_fn(mel_norm, stats_norm)

    def train_step(self, data):
        x, y = data
        if isinstance(x, dict):
            x_clean = x.get("clean", x.get("noisy"))
            x_noisy = x["noisy"]
        else:
            x_clean = x
            x_noisy = x
        teacher_x = self._adapt_input_for_model(x_clean, self.teacher_probe)
        student_x = self._adapt_input_for_model(x_noisy, self.student_probe)
        stats_target = self._extract_stats_target(student_x)

        t_out = self.teacher_probe(teacher_x, training=False)
        t_probs, t_embed, _, _ = self._unpack_probe_outputs(t_out)

        with tf.GradientTape() as tape:
            s_out = self.student_probe(student_x, training=True)
            s_probs, s_embed, s_mel_embed, s_stats_embed = self._unpack_probe_outputs(s_out)

            ce_loss = tf.constant(0.0, dtype=tf.float32)
            if self.use_ce and self.alpha > 0.0:
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

            aux_loss = self._calc_aux_loss(s_mel_embed, s_stats_embed, stats_target)
            cls_loss = self.alpha * ce_loss + self.beta * kd_logits + self.current_gamma * kd_embed
            total_loss = cls_loss + self.aux_alpha * aux_loss

        train_vars = list(self.student_probe.trainable_variables)
        if self.student_embed_proj is not None:
            train_vars.extend(self.student_embed_proj.trainable_variables)
        if self.stats_to_mel_proj is not None:
            train_vars.extend(self.stats_to_mel_proj.trainable_variables)
        if self.stats_reg_head is not None:
            train_vars.extend(self.stats_reg_head.trainable_variables)
        grads = tape.gradient(total_loss, train_vars)
        grads_and_vars = [(g, v) for g, v in zip(grads, train_vars) if g is not None]
        if grads_and_vars:
            self.optimizer.apply_gradients(grads_and_vars)

        self.loss_tracker.update_state(total_loss)
        self.cls_loss_tracker.update_state(cls_loss)
        self.ce_tracker.update_state(ce_loss)
        self.kd_logits_tracker.update_state(kd_logits)
        self.kd_embed_tracker.update_state(kd_embed)
        self.aux_tracker.update_state(aux_loss)
        self.gamma_tracker.update_state(self.current_gamma)
        self.acc_metric.update_state(y, s_probs)

        return {m.name: m.result() for m in self.metrics}

    def test_step(self, data):
        x, y = data
        if isinstance(x, dict):
            x_clean = x.get("clean", x.get("noisy"))
            x_noisy = x["noisy"]
        else:
            x_clean = x
            x_noisy = x
        teacher_x = self._adapt_input_for_model(x_clean, self.teacher_probe)
        student_x = self._adapt_input_for_model(x_noisy, self.student_probe)
        stats_target = self._extract_stats_target(student_x)

        t_out = self.teacher_probe(teacher_x, training=False)
        s_out = self.student_probe(student_x, training=False)
        t_probs, t_embed, _, _ = self._unpack_probe_outputs(t_out)
        s_probs, s_embed, s_mel_embed, s_stats_embed = self._unpack_probe_outputs(s_out)

        ce_loss = tf.constant(0.0, dtype=tf.float32)
        if self.use_ce and self.alpha > 0.0:
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

        aux_loss = self._calc_aux_loss(s_mel_embed, s_stats_embed, stats_target)
        cls_loss = self.alpha * ce_loss + self.beta * kd_logits + self.current_gamma * kd_embed
        total_loss = cls_loss + self.aux_alpha * aux_loss

        self.loss_tracker.update_state(total_loss)
        self.cls_loss_tracker.update_state(cls_loss)
        self.ce_tracker.update_state(ce_loss)
        self.kd_logits_tracker.update_state(kd_logits)
        self.kd_embed_tracker.update_state(kd_embed)
        self.aux_tracker.update_state(aux_loss)
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
        if GAMMA_LOG_VERBOSE:
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
    "[Model] "
    f"teacher_profile={TEACHER_MODEL_PROFILE} ({_fmt_model_kwargs(TEACHER_MODEL_KWARGS)}), "
    f"student_profile={STUDENT_MODEL_PROFILE} ({_fmt_model_kwargs(STUDENT_MODEL_KWARGS)}), "
    f"student_init_mode={STUDENT_INIT_MODE}, "
    f"student_init_ckpt={STUDENT_INIT_CKPT or 'None'}"
)
print(
    "[StatsBranch/Teacher] "
    f"enabled={TEACHER_USE_STATS_BRANCH}, "
    f"stats_dim={TEACHER_STATS_DIM}, "
    f"stats_mlp_units={list(TEACHER_STATS_MLP_UNITS)}, "
    f"fuse_units={TEACHER_FUSE_UNITS}, "
    f"fusion_mode={TEACHER_FUSION_MODE}, "
    f"gate_units={TEACHER_GATE_UNITS}, "
    f"strict_reuse_shape={STRICT_REUSE_TEACHER_SHAPE}, "
    f"pitch_range=[{PITCH_FMIN},{PITCH_FMAX}]"
)
print(
    "[StatsBranch/Student] "
    f"enabled={USE_STATS_BRANCH}, "
    f"stats_dim={STATS_DIM}, "
    f"stats_mlp_units={list(STATS_MLP_UNITS)}, "
    f"fuse_units={FUSE_UNITS}, "
    f"fusion_mode={FUSION_MODE}, "
    f"gate_units={GATE_UNITS}, "
    f"pitch_range=[{PITCH_FMIN},{PITCH_FMAX}]"
)
print(f"[AuxLoss] mode={AUX_MODE}, loss_type={AUX_LOSS_TYPE}, alpha={AUX_LOSS_ALPHA}")
print(
    "[Prosody] "
    f"enabled={ENABLE_CLASS_PROSODY_AUG}, "
    f"teacher={TEACHER_ENABLE_PROSODY_AUG}, "
    f"student={STUDENT_ENABLE_PROSODY_AUG}, "
    f"class={EMERGENCY_CLASS_NAME}, "
    f"e_prob={EMERGENCY_PROSODY_PROB}, "
    f"e_pitch=[{EMERGENCY_PITCH_MIN},{EMERGENCY_PITCH_MAX}], "
    f"e_gain_db=[{EMERGENCY_GAIN_DB_MIN},{EMERGENCY_GAIN_DB_MAX}]"
)
print(f"[Train] fit_verbose={FIT_VERBOSE}, gamma_log_verbose={GAMMA_LOG_VERBOSE}")
print(
    "[EarlyStop] "
    f"patience={EARLYSTOP_PATIENCE}, "
    f"teacher_monitor={TEACHER_MONITOR}, "
    f"student_monitor={STUDENT_MONITOR}"
)
print(
    "[Smoke knobs] "
    f"teacher_steps={TEACHER_STEPS_PER_EPOCH or 'full'}, "
    f"teacher_val_steps={TEACHER_VAL_STEPS or 'full'}, "
    f"student_steps={STUDENT_STEPS_PER_EPOCH or 'full'}, "
    f"student_val_steps={STUDENT_VAL_STEPS or 'full'}, "
    f"eval_steps={EVAL_STEPS or 'full'}, "
    f"skip_final_eval={SKIP_FINAL_EVAL}"
)
print(
    "[Prewarm] "
    f"epochs={PREWARM_EPOCHS}, "
    f"use_ce={PREWARM_USE_CE}, "
    f"use_logits={PREWARM_USE_LOGITS}, "
    f"alpha={PREWARM_ALPHA_CE}, "
    f"beta={PREWARM_LOGITS_BETA}, "
    f"temperature={PREWARM_TEMPERATURE}, "
    f"lr={PREWARM_LR}, "
    f"prosody_aug={PREWARM_ENABLE_PROSODY_AUG}"
)
print(
    "[Artifacts] "
    f"save_run_config={SAVE_RUN_CONFIG}, "
    f"save_train_history={SAVE_TRAIN_HISTORY}, "
    f"history_dir={HISTORY_DIR}"
)

if SAVE_RUN_CONFIG:
    _dump_run_config(os.path.join(RESULT_DIR, "run_config.json"))

teacher_history = None
prewarm_history = None
student_history = None

# ---------- Stage 1: train clean teacher ----------
print("\n[Stage 1] Train clean teacher...")
teacher = build_model((N_MELS, MAX_FRAMES, 1), num_classes, **_with_stats_kwargs(TEACHER_MODEL_KWARGS, role="teacher"))
print(f"[Stage 1] teacher_params={teacher.count_params():,}")
teacher_loaded = False
if REUSE_TEACHER and os.path.exists(TEACHER_CKPT):
    print(f"[Stage 1] Reusing existing teacher checkpoint: {TEACHER_CKPT}")
    try:
        teacher.load_weights(TEACHER_CKPT)
        teacher_loaded = True
    except Exception as exc:
        msg = (
            "[Stage 1] Reuse teacher failed due to shape/config mismatch.\n"
            f"  teacher_ckpt={TEACHER_CKPT}\n"
            "  expected_action=align teacher branch knobs with checkpoint "
            "(KD_TEACHER_USE_STATS_BRANCH, KD_TEACHER_STATS_MLP_UNITS, "
            "KD_TEACHER_FUSE_UNITS, KD_TEACHER_FUSION_MODE, KD_TEACHER_GATE_UNITS)\n"
            f"  error={exc}"
        )
        if STRICT_REUSE_TEACHER_SHAPE:
            raise RuntimeError(msg) from exc
        print(msg)
        print("[Stage 1] strict_reuse_teacher_shape=0, fallback to train teacher")

if not teacher_loaded:
    teacher.compile(optimizer=Adam(LEARNING_RATE), loss="categorical_crossentropy", metrics=["accuracy"])

    teacher_train_gen = CleanDataGenerator(
        data["X_train"],
        data["y_train"],
        BATCH_SIZE,
        num_classes,
        class_names=class_names,
        is_training=True,
        enable_prosody_aug=TEACHER_ENABLE_PROSODY_AUG,
    )
    teacher_val_gen = CleanDataGenerator(
        data["X_val"],
        data["y_val"],
        BATCH_SIZE,
        num_classes,
        class_names=class_names,
        is_training=False,
        enable_prosody_aug=False,
    )

    class_weights = class_weight.compute_class_weight(
        class_weight="balanced",
        classes=np.unique(data["y_train"]),
        y=data["y_train"],
    )
    class_weight_dict = dict(enumerate(class_weights))

    teacher_callbacks = [
        ModelCheckpoint(TEACHER_CKPT, save_best_only=True, monitor=TEACHER_MONITOR, save_weights_only=True, verbose=0),
        EarlyStopping(monitor=TEACHER_MONITOR, patience=EARLYSTOP_PATIENCE, restore_best_weights=True, verbose=0),
    ]

    teacher_fit_kwargs = {}
    if TEACHER_STEPS_PER_EPOCH is not None:
        teacher_fit_kwargs["steps_per_epoch"] = TEACHER_STEPS_PER_EPOCH
    if TEACHER_VAL_STEPS is not None:
        teacher_fit_kwargs["validation_steps"] = TEACHER_VAL_STEPS

    teacher_history = teacher.fit(
        teacher_train_gen,
        validation_data=teacher_val_gen,
        epochs=TEACHER_EPOCHS,
        callbacks=teacher_callbacks,
        class_weight=class_weight_dict,
        verbose=FIT_VERBOSE,
        **teacher_fit_kwargs,
    )

    teacher.load_weights(TEACHER_CKPT)

# ---------- Stage 2: student warm start + noisy KD ----------
print("\n[Stage 2] Prepare student for distillation...")
student = build_model((N_MELS, MAX_FRAMES, 1), num_classes, **_with_stats_kwargs(STUDENT_MODEL_KWARGS))
print(f"[Stage 2] student_params={student.count_params():,}")
student_init_source = initialize_student_weights(student)
print(f"[Stage 2] student_init={student_init_source}")

teacher_probe = build_probe_model(teacher)
teacher_probe.trainable = False

student_probe = build_probe_model(student)

# ---------- Stage 2A: teacher-guided clean prewarm ----------
if PREWARM_EPOCHS > 0 and (PREWARM_USE_CE or PREWARM_USE_LOGITS):
    print("\n[Stage 2A] Teacher-guided clean prewarm...")
    prewarm_distiller = Distiller(
        student_probe=student_probe,
        teacher_probe=teacher_probe,
        alpha=PREWARM_ALPHA_CE if PREWARM_USE_CE else 0.0,
        beta=PREWARM_LOGITS_BETA if PREWARM_USE_LOGITS else 0.0,
        gamma_max=0.0,
        temperature=PREWARM_TEMPERATURE,
        use_ce=PREWARM_USE_CE,
        use_logits_kd=PREWARM_USE_LOGITS,
        use_embed_kd=False,
        use_embed_projection=False,
        aux_alpha=AUX_LOSS_ALPHA,
        aux_mode=AUX_MODE,
        aux_loss_type=AUX_LOSS_TYPE,
        stats_dim=STATS_DIM,
    )
    prewarm_distiller.compile(optimizer=Adam(PREWARM_LR))

    prewarm_train_gen = CleanDataGenerator(
        data["X_train"],
        data["y_train"],
        BATCH_SIZE,
        num_classes,
        class_names=class_names,
        is_training=True,
        enable_prosody_aug=PREWARM_ENABLE_PROSODY_AUG,
    )
    prewarm_val_gen = CleanDataGenerator(
        data["X_val"],
        data["y_val"],
        BATCH_SIZE,
        num_classes,
        class_names=class_names,
        is_training=False,
        enable_prosody_aug=False,
    )

    prewarm_callbacks = [
        EarlyStopping(monitor=PREWARM_MONITOR, patience=PREWARM_PATIENCE, restore_best_weights=True, verbose=0),
    ]

    prewarm_fit_kwargs = {}
    if PREWARM_STEPS_PER_EPOCH is not None:
        prewarm_fit_kwargs["steps_per_epoch"] = PREWARM_STEPS_PER_EPOCH
    if PREWARM_VAL_STEPS is not None:
        prewarm_fit_kwargs["validation_steps"] = PREWARM_VAL_STEPS

    prewarm_history = prewarm_distiller.fit(
        prewarm_train_gen,
        validation_data=prewarm_val_gen,
        epochs=PREWARM_EPOCHS,
        callbacks=prewarm_callbacks,
        verbose=FIT_VERBOSE,
        **prewarm_fit_kwargs,
    )
    print("[Stage 2A] Prewarm completed.")
else:
    print("\n[Stage 2A] Skipped clean prewarm.")

# ---------- Stage 2B: distill noisy student ----------
print("\n[Stage 2B] Distill noisy student from clean teacher...")
use_ce_kd, use_logits_kd, use_embed_kd, alpha_ce, beta_logits, gamma_embed_max, embed_warmup_epochs = resolve_distill_variant(DISTILL_VARIANT)
embed_ramp_epochs = max(1, STUDENT_EPOCHS - embed_warmup_epochs)
print(
    "[KD config] "
    f"variant={DISTILL_VARIANT}, "
    f"use_ce={use_ce_kd}, "
    f"use_logits={use_logits_kd}, "
    f"use_embed={use_embed_kd}, "
    f"alpha={alpha_ce}, "
    f"beta={beta_logits}, "
    f"gamma_max={gamma_embed_max}, "
    f"aux_mode={AUX_MODE}, "
    f"aux_loss_type={AUX_LOSS_TYPE}, "
    f"aux_alpha={AUX_LOSS_ALPHA}, "
    f"embed_proj={USE_EMBED_PROJECTION}, "
    f"warmup_epochs={embed_warmup_epochs}, "
    f"ramp_epochs={embed_ramp_epochs}"
)

distiller = Distiller(
    student_probe=student_probe,
    teacher_probe=teacher_probe,
    alpha=alpha_ce,
    beta=beta_logits,
    gamma_max=gamma_embed_max,
    temperature=TEMPERATURE,
    use_ce=use_ce_kd,
    use_logits_kd=use_logits_kd,
    use_embed_kd=use_embed_kd,
    use_embed_projection=USE_EMBED_PROJECTION,
    aux_alpha=AUX_LOSS_ALPHA,
    aux_mode=AUX_MODE,
    aux_loss_type=AUX_LOSS_TYPE,
    stats_dim=STATS_DIM,
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
    enable_prosody_aug=STUDENT_ENABLE_PROSODY_AUG,
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
    enable_prosody_aug=False,
    snr_range=(MIN_SNR_DB, MAX_SNR_DB),
    eval_snr_db=EVAL_SNR_DB,
)

student_callbacks = [
    EmbedWeightScheduler(
        distiller=distiller,
        enabled=use_embed_kd,
        gamma_max=gamma_embed_max,
        warmup_epochs=embed_warmup_epochs,
        ramp_epochs=embed_ramp_epochs,
    ),
    EarlyStopping(monitor=STUDENT_MONITOR, patience=EARLYSTOP_PATIENCE, restore_best_weights=True, verbose=0),
]

student_fit_kwargs = {}
if STUDENT_STEPS_PER_EPOCH is not None:
    student_fit_kwargs["steps_per_epoch"] = STUDENT_STEPS_PER_EPOCH
if STUDENT_VAL_STEPS is not None:
    student_fit_kwargs["validation_steps"] = STUDENT_VAL_STEPS

student_history = distiller.fit(
    student_train_gen,
    validation_data=student_val_gen,
    epochs=STUDENT_EPOCHS,
    callbacks=student_callbacks,
    verbose=FIT_VERBOSE,
    **student_fit_kwargs,
)

if SAVE_TRAIN_HISTORY:
    _save_history_csv(teacher_history, os.path.join(HISTORY_DIR, "teacher_history.csv"))
    _save_history_csv(prewarm_history, os.path.join(HISTORY_DIR, "prewarm_history.csv"))
    _save_history_csv(student_history, os.path.join(HISTORY_DIR, "student_history.csv"))

student.save_weights(STUDENT_CKPT)

# ---------- Final evaluation ----------
# ---------- Final evaluation ----------
if SKIP_FINAL_EVAL:
    report_path = os.path.join(RESULT_DIR, "classification_report_noisy.txt")
    with open(report_path, "w") as f:
        f.write("Skipped final evaluation because KD_SKIP_FINAL_EVAL=true\n")
    print("\n[Evaluation] Skipped final evaluation (KD_SKIP_FINAL_EVAL=true).")
else:
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

    # compile with explicit loss/metrics before evaluate()
    student.compile(
        optimizer="adam",
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )

    clean_eval_kwargs = {"verbose": 0}
    noisy_eval_kwargs = {"verbose": 0}
    predict_kwargs = {"verbose": 0}
    if EVAL_STEPS is not None:
        clean_eval_kwargs["steps"] = EVAL_STEPS
        noisy_eval_kwargs["steps"] = EVAL_STEPS
        predict_kwargs["steps"] = EVAL_STEPS

    clean_metrics = student.evaluate(clean_test_gen, **clean_eval_kwargs)
    noisy_metrics = student.evaluate(noisy_test_gen, **noisy_eval_kwargs)
    print(f"Student clean test - loss: {clean_metrics[0]:.4f}, acc: {clean_metrics[1]:.4f}")
    print(f"Student noisy test (SNR={EVAL_SNR_DB}dB) - loss: {noisy_metrics[0]:.4f}, acc: {noisy_metrics[1]:.4f}")

    # Classification report on noisy test
    y_pred = np.argmax(student.predict(noisy_test_gen, **predict_kwargs), axis=1)
    y_true = []
    max_batches = len(noisy_test_gen) if EVAL_STEPS is None else min(EVAL_STEPS, len(noisy_test_gen))
    for i in range(max_batches):
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
