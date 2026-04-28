# Centralized model and frontend configuration

import os

# -------------------------
# Model architecture
# -------------------------
MODEL_KWARGS_PRESETS = {
    "base": dict(
        conv_filters=64,
        num_layers=1,
        head_size=32,
        num_heads=4,
        ff_dim=256,
        dropout_rate=0.15,
        fnn_units=[128],
    ),
    "large": dict(
        conv_filters=64,
        num_layers=2,
        head_size=48,
        num_heads=6,
        ff_dim=384,
        dropout_rate=0.20,
        fnn_units=[256, 128],
    ),
    "xlarge": dict(
        conv_filters=64,
        num_layers=3,
        head_size=64,
        num_heads=8,
        ff_dim=512,
        dropout_rate=0.20,
        fnn_units=[256, 128],
    ),
    "deploy_s": dict(
        conv_filters=48,
        num_layers=1,
        head_size=24,
        num_heads=3,
        ff_dim=192,
        dropout_rate=0.15,
        fnn_units=[96],
    ),
    "deploy_xs": dict(
        conv_filters=32,
        num_layers=1,
        head_size=16,
        num_heads=2,
        ff_dim=128,
        dropout_rate=0.15,
        fnn_units=[64],
    ),
    "deploy_tiny": dict(
        conv_filters=24,
        num_layers=1,
        head_size=8,
        num_heads=2,
        ff_dim=64,
        dropout_rate=0.10,
        fnn_units=[48],
    ),
    "xiao_time16": dict(
        conv_filters=64,
        num_layers=1,
        head_size=32,
        num_heads=4,
        ff_dim=256,
        dropout_rate=0.15,
        fnn_units=[128],
        branchformer_time_pool=2,
    ),
    "xiao_bottleneck256": dict(
        conv_filters=64,
        num_layers=1,
        head_size=32,
        num_heads=4,
        ff_dim=128,
        dropout_rate=0.15,
        fnn_units=[128],
        branchformer_bottleneck_dim=256,
    ),
    "xiao_bottleneck256_tflm": dict(
        conv_filters=64,
        num_layers=1,
        head_size=32,
        num_heads=4,
        ff_dim=128,
        dropout_rate=0.15,
        fnn_units=[128],
        branchformer_bottleneck_dim=256,
        branchformer_conv_impl="depthwise_conv1d",
    ),
    "xiao_time16_bottleneck256": dict(
        conv_filters=64,
        num_layers=1,
        head_size=32,
        num_heads=4,
        ff_dim=128,
        dropout_rate=0.15,
        fnn_units=[128],
        branchformer_time_pool=2,
        branchformer_bottleneck_dim=256,
    ),
}

# Backward-compatible default used by existing training/inference scripts.
MODEL_KWARGS = dict(MODEL_KWARGS_PRESETS["base"])


def get_model_kwargs(profile: str = "base"):
    name = str(profile).strip().lower()
    alias = {
        "small": "base",
        "medium": "large",
        "xl": "xlarge",
        "tiny": "deploy_tiny",
        "time16": "xiao_time16",
        "bottleneck256": "xiao_bottleneck256",
        "bottleneck256_tflm": "xiao_bottleneck256_tflm",
        "xiao_b256_tflm": "xiao_bottleneck256_tflm",
        "time16_bottleneck256": "xiao_time16_bottleneck256",
    }
    name = alias.get(name, name)
    if name not in MODEL_KWARGS_PRESETS:
        raise ValueError(
            f"Unknown model profile: {profile}. "
            f"Supported: {sorted(MODEL_KWARGS_PRESETS.keys()) + sorted(alias.keys())}"
        )
    cfg = dict(MODEL_KWARGS_PRESETS[name])
    cfg["fnn_units"] = list(cfg["fnn_units"])
    return cfg

# -------------------------
# Audio / frontend params
# -------------------------
SAMPLE_RATE = 16000
DURATION = 1.0
TARGET_LEN = int(SAMPLE_RATE * DURATION)

N_FFT = 1024
HOP_LENGTH = 512
CENTER = False
N_MELS = 256
N_MFCC = 40
FMIN = 50
FMAX = None
TOP_DB = 80.0

MAX_FRAMES = int(DURATION * SAMPLE_RATE / HOP_LENGTH) + 1
N_BINS = N_FFT // 2 + 1

PCEN_KWARGS = dict(gain=0.98, bias=2.0, power=0.5, time_constant=0.06, eps=1e-6)

SPEC_SUB_PARAMS = dict(
    alpha=1.0,
    floor=1e-6,
    noise_est_percentile=0.2,
)

DEFAULT_CALIB_NOISE_WAV = "/Users/zilongzeng/Research/DroneControl/tellonoise/20251029_190227.wav"

# -------------------------
# Frontend registry
# -------------------------
FRONTEND_TYPES = (
    "fft",
    "logmel",
    "pcen",
    "mfcc",
    "fft_specsub",
    "logmel_specsub",
    "pcen_specsub",
    "mfcc_specsub",
    "fft_wiener",
    "logmel_wiener",
    "pcen_wiener",
    "mfcc_wiener",
)

SPEC_SUB_FRONTENDS = {
    "fft_specsub",
    "logmel_specsub",
    "pcen_specsub",
    "mfcc_specsub",
}

WIENER_FRONTENDS = {
    "fft_wiener",
    "logmel_wiener",
    "pcen_wiener",
    "mfcc_wiener",
}

MODEL_WEIGHT_FILENAMES = {
    "fft": "fft_best.weights.h5",
    "logmel": "logmel_best.weights.h5",
    "pcen": "pcen_best.weights.h5",
    "mfcc": "mfcc_best.weights.h5",
    "fft_specsub": "fft_specsub_best.weights.h5",
    "logmel_specsub": "logmel_specsub_best.weights.h5",
    "pcen_specsub": "pcen_specsub_best.weights.h5",
    "mfcc_specsub": "mfcc_specsub_best.weights.h5",
    "fft_wiener": "fft_wiener_best.weights.h5",
    "logmel_wiener": "logmel_wiener_best.weights.h5",
    "pcen_wiener": "pcen_wiener_real_bias_best.weights.h5",
    "mfcc_wiener": "mfcc_wiener_best.weights.h5",
}


def get_input_shape(frontend_type: str):
    if frontend_type in {"fft", "fft_specsub", "fft_wiener"}:
        return (N_BINS, MAX_FRAMES, 1)
    if frontend_type in {"mfcc", "mfcc_specsub", "mfcc_wiener"}:
        return (N_MFCC, MAX_FRAMES, 1)
    return (N_MELS, MAX_FRAMES, 1)


def get_model_weights_path(frontend_type: str, base_dir: str = "saved_models") -> str:
    filename = MODEL_WEIGHT_FILENAMES.get(frontend_type)
    if filename is None:
        raise ValueError(f"Unknown frontend_type: {frontend_type}")
    return os.path.join(base_dir, frontend_type, filename)
