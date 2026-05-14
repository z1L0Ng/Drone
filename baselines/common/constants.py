"""Shared constants for Track D baselines.

The values mirror the current Drone recognizer frontend contract.
"""

SAMPLE_RATE = 16000
DURATION_SEC = 1.0
TARGET_LEN = int(SAMPLE_RATE * DURATION_SEC)

N_FFT = 1024
HOP_LENGTH = 512
CENTER = False
N_MELS = 256
N_MFCC = 40
FMIN = 50
FMAX = None
TOP_DB = 80.0
MAX_FRAMES = int(DURATION_SEC * SAMPLE_RATE / HOP_LENGTH) + 1

LABELS = ("emergency", "movement", "unknown")

PROCESSED_DATA_PATH = "dataset/processed/data_paths.npz"
ENCODER_PATH = "saved_models/label_encoder.joblib"
NOISE_SOURCE_DIR = "dataset/raw/tellonoise"

WEEKLY_TAG = "drone_2026w19"
OFFLINE_OUTPUT_ROOT = "weeklyresult/weekly_drone_2026w19/offline_baselines"
