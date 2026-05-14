"""Audio loading and 1 s / 16 kHz normalization."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal

from .constants import SAMPLE_RATE, TARGET_LEN


def ensure_target_len(y: np.ndarray, target_len: int = TARGET_LEN) -> np.ndarray:
    """Pad or crop a waveform to the project 1 s contract."""
    wav = np.asarray(y, dtype=np.float32).reshape(-1)
    if wav.shape[0] < target_len:
        wav = np.pad(wav, (0, target_len - wav.shape[0]))
    else:
        wav = wav[:target_len]
    return wav.astype(np.float32, copy=False)


def load_audio_1s(path: str | Path, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """Load mono audio, resample when needed, and return exactly 1 s."""
    wav, sr = sf.read(str(path), dtype="float32")
    if wav.ndim > 1:
        wav = np.mean(wav, axis=1)
    if sr != sample_rate:
        wav = signal.resample_poly(wav, sample_rate, sr).astype(np.float32)
    return ensure_target_len(wav)


def synthetic_audio(seed: int = 42) -> np.ndarray:
    """Generate a deterministic low-amplitude waveform for smoke checks."""
    rng = np.random.default_rng(seed)
    return rng.normal(0.0, 0.01, size=(TARGET_LEN,)).astype(np.float32)
