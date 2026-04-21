import os

os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/numba_cache")

import numpy as np
import librosa

from model_config import (
    CENTER,
    FMAX,
    FMIN,
    HOP_LENGTH,
    MAX_FRAMES,
    N_FFT,
    N_MELS,
    SAMPLE_RATE,
    TARGET_LEN,
    TOP_DB,
)


def ensure_target_len(y):
    y = np.asarray(y, dtype=np.float32).reshape(-1)
    if y.shape[0] < TARGET_LEN:
        y = np.pad(y, (0, TARGET_LEN - y.shape[0]))
    else:
        y = y[:TARGET_LEN]
    return y.astype(np.float32, copy=False)


def extract_logmel(y):
    y = ensure_target_len(y)
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
    return feat.astype(np.float32, copy=False)


def extract_logmel_input(y):
    feat = extract_logmel(y)
    return np.expand_dims(feat, axis=-1).astype(np.float32, copy=False)
