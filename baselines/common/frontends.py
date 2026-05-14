"""Frontend extraction for Track D baselines.

This scaffold uses SciPy/NumPy implementations to keep smoke tests independent
from local librosa/numba cache behavior. Before full training, compare numeric
outputs against the current project frontend on a small probe set.
"""

from __future__ import annotations

import numpy as np
from scipy import signal
from scipy.fftpack import dct

from .audio_io import ensure_target_len, synthetic_audio
from .constants import (
    CENTER,
    FMAX,
    FMIN,
    HOP_LENGTH,
    MAX_FRAMES,
    N_FFT,
    N_MELS,
    N_MFCC,
    SAMPLE_RATE,
    TOP_DB,
)


def _hz_to_mel(hz: np.ndarray | float) -> np.ndarray | float:
    return 2595.0 * np.log10(1.0 + np.asarray(hz) / 700.0)


def _mel_to_hz(mel: np.ndarray | float) -> np.ndarray | float:
    return 700.0 * (10.0 ** (np.asarray(mel) / 2595.0) - 1.0)


def _mel_filterbank(n_mels: int = N_MELS) -> np.ndarray:
    fmax = FMAX if FMAX is not None else SAMPLE_RATE / 2.0
    mel_points = np.linspace(_hz_to_mel(FMIN), _hz_to_mel(fmax), n_mels + 2)
    hz_points = _mel_to_hz(mel_points)
    bins = np.floor((N_FFT + 1) * hz_points / SAMPLE_RATE).astype(int)
    bins = np.clip(bins, 0, N_FFT // 2)

    filters = np.zeros((n_mels, N_FFT // 2 + 1), dtype=np.float32)
    for i in range(1, n_mels + 1):
        left, center, right = int(bins[i - 1]), int(bins[i]), int(bins[i + 1])
        if center <= left:
            center = min(left + 1, N_FFT // 2)
        if right <= center:
            right = min(center + 1, N_FFT // 2)
        if center > left:
            filters[i - 1, left:center] = (np.arange(left, center) - left) / float(center - left)
        if right > center:
            filters[i - 1, center:right] = (right - np.arange(center, right)) / float(right - center)
    return filters


_MEL_FILTERBANK = _mel_filterbank(N_MELS)


def _fix_frames(feat: np.ndarray, max_frames: int = MAX_FRAMES) -> np.ndarray:
    if feat.shape[1] < max_frames:
        feat = np.pad(feat, ((0, 0), (0, max_frames - feat.shape[1])), mode="constant")
    else:
        feat = feat[:, :max_frames]
    return feat.astype(np.float32, copy=False)


def _power_spectrogram(y: np.ndarray) -> np.ndarray:
    wav = ensure_target_len(y)
    _, _, zxx = signal.stft(
        wav,
        fs=SAMPLE_RATE,
        window="hann",
        nperseg=N_FFT,
        noverlap=N_FFT - HOP_LENGTH,
        nfft=N_FFT,
        detrend=False,
        return_onesided=True,
        boundary=None,
        padded=False,
    )
    return np.abs(zxx).astype(np.float32) ** 2


def _logmel_db(y: np.ndarray) -> np.ndarray:
    power = _power_spectrogram(y)
    mel = np.maximum(_MEL_FILTERBANK @ power, 1e-10)
    log_mel = 10.0 * np.log10(mel)
    ref = float(np.max(log_mel)) if log_mel.size else 0.0
    return np.maximum(log_mel - ref, -TOP_DB).astype(np.float32)


def extract_logmel(y: np.ndarray) -> np.ndarray:
    feat = _logmel_db(y)
    return _fix_frames(feat)


def extract_mfcc(y: np.ndarray) -> np.ndarray:
    logmel = _logmel_db(y)
    mfcc = dct(logmel, type=2, axis=0, norm="ortho")[:N_MFCC]
    return _fix_frames(mfcc)


def extract_feature(y: np.ndarray, frontend_type: str) -> np.ndarray:
    name = str(frontend_type).strip().lower()
    if name == "logmel":
        return extract_logmel(y)
    if name == "mfcc":
        return extract_mfcc(y)
    raise ValueError(f"Unsupported frontend_type={frontend_type!r}")


def extract_feature_input(y: np.ndarray, frontend_type: str) -> np.ndarray:
    feat = extract_feature(y, frontend_type)
    return np.expand_dims(feat, axis=-1).astype(np.float32, copy=False)


def expected_shape(frontend_type: str) -> tuple[int, int, int]:
    name = str(frontend_type).strip().lower()
    if name == "logmel":
        return (N_MELS, MAX_FRAMES, 1)
    if name == "mfcc":
        return (N_MFCC, MAX_FRAMES, 1)
    raise ValueError(f"Unsupported frontend_type={frontend_type!r}")


def smoke_check_frontends() -> dict[str, tuple[int, int, int]]:
    wav = synthetic_audio()
    return {
        "logmel": extract_feature_input(wav, "logmel").shape,
        "mfcc": extract_feature_input(wav, "mfcc").shape,
    }
