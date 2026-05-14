"""Tellonoise discovery and SNR mixing utilities."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal

from .audio_io import ensure_target_len, load_audio_1s
from .constants import NOISE_SOURCE_DIR, SAMPLE_RATE, TARGET_LEN


def list_noise_files(noise_source_dir: str | Path = NOISE_SOURCE_DIR) -> list[str]:
    root = Path(noise_source_dir)
    if not root.is_dir():
        return []
    return sorted(str(p) for p in root.rglob("*.wav"))


def mix_with_noise(clean: np.ndarray, noise: np.ndarray, snr_db: float) -> np.ndarray:
    clean = ensure_target_len(clean)
    noise = ensure_target_len(noise)
    clean_power = float(np.mean(np.square(clean), dtype=np.float64) + 1e-12)
    noise_power = float(np.mean(np.square(noise), dtype=np.float64) + 1e-12)
    target_noise_power = clean_power / (10.0 ** (float(snr_db) / 10.0))
    scale = np.sqrt(target_noise_power / noise_power)
    mixed = clean + scale * noise
    return np.clip(mixed, -1.0, 1.0).astype(np.float32)


def sample_noise_clip(noise_files: list[str], rng: np.random.Generator) -> np.ndarray | None:
    if not noise_files:
        return None
    path = rng.choice(noise_files)
    try:
        info = sf.info(str(path))
        if info.samplerate == SAMPLE_RATE and info.frames > TARGET_LEN:
            start = int(rng.integers(0, info.frames - TARGET_LEN + 1))
            with sf.SoundFile(str(path)) as handle:
                handle.seek(start)
                data = handle.read(TARGET_LEN, dtype="float32", always_2d=False)
            if getattr(data, "ndim", 1) > 1:
                data = np.mean(data, axis=1)
            return ensure_target_len(data)
        if info.samplerate != SAMPLE_RATE:
            data, sr = sf.read(str(path), dtype="float32", always_2d=False)
            if getattr(data, "ndim", 1) > 1:
                data = np.mean(data, axis=1)
            data = signal.resample_poly(data, SAMPLE_RATE, sr).astype(np.float32)
            return ensure_target_len(data)
        return load_audio_1s(path)
    except Exception:
        return None
