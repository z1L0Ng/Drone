"""Audited project log-mel contract with strict exact-audio loading."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any, Mapping, Tuple

import numpy as np

from .config import canonical_json_bytes, sha256_bytes, sha256_file


class FrontendError(ValueError):
    """Raised when audio or features violate the frozen contract."""


def load_exact_mono_pcm(path: str | Path, expected_sha256: str | None = None) -> np.ndarray:
    import soundfile as sf

    audio_path = Path(path)
    if expected_sha256 is not None and sha256_file(audio_path) != expected_sha256:
        raise FrontendError(f"audio file SHA-256 mismatch: {audio_path}")
    info = sf.info(audio_path)
    if not str(info.subtype).startswith("PCM_"):
        raise FrontendError(f"expected PCM audio subtype, got {info.subtype}: {audio_path}")
    if info.channels != 1 or info.samplerate != 16000 or info.frames != 16000:
        raise FrontendError(
            f"expected mono PCM 16 kHz / 16000 frames, got "
            f"channels={info.channels}, rate={info.samplerate}, frames={info.frames}: {audio_path}"
        )
    waveform, sample_rate = sf.read(audio_path, dtype="float32", always_2d=False)
    waveform = np.asarray(waveform)
    if sample_rate != 16000:
        raise FrontendError(f"expected 16000 Hz, got {sample_rate}: {audio_path}")
    if waveform.ndim != 1:
        raise FrontendError(f"expected mono audio, got shape {waveform.shape}: {audio_path}")
    if waveform.shape != (16000,):
        raise FrontendError(f"expected exactly 16000 samples, got {waveform.shape}: {audio_path}")
    if not np.all(np.isfinite(waveform)):
        raise FrontendError(f"audio contains NaN/Inf: {audio_path}")
    return waveform.astype(np.float32, copy=False)


def extract_logmel_input(waveform: np.ndarray, contract: Mapping[str, Any]) -> np.ndarray:
    os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/numba_cache")
    import librosa

    y = np.asarray(waveform, dtype=np.float32).reshape(-1)
    if y.shape != (16000,):
        raise FrontendError(f"frontend requires exactly 16000 samples, got {y.shape}")
    mel = librosa.feature.melspectrogram(
        y=y,
        sr=16000,
        n_fft=int(contract["n_fft"]),
        hop_length=int(contract["hop_length"]),
        center=bool(contract["center"]),
        n_mels=int(contract["n_mels"]),
        fmin=float(contract["fmin_hz"]),
        fmax=contract["fmax_hz"],
        power=float(contract["power"]),
    )
    feature = librosa.power_to_db(
        mel,
        ref=np.max,
        top_db=float(contract["top_db"]),
    )
    max_frames = int(contract["max_frames"])
    if feature.shape[1] < max_frames:
        feature = np.pad(
            feature,
            ((0, 0), (0, max_frames - feature.shape[1])),
            mode="constant",
            constant_values=float(contract["pad_value_db"]),
        )
    else:
        feature = feature[:, :max_frames]
    tensor = np.expand_dims(feature, axis=-1).astype(np.float32, copy=False)
    expected = (int(contract["n_mels"]), max_frames, 1)
    if tensor.shape != expected or not np.all(np.isfinite(tensor)):
        raise FrontendError(f"invalid feature tensor shape/values: {tensor.shape}")
    return tensor


def tensor_sha256(tensor: np.ndarray) -> str:
    canonical = np.ascontiguousarray(np.asarray(tensor, dtype="<f4"))
    return hashlib.sha256(canonical.tobytes(order="C")).hexdigest()


def frontend_contract_sha256(contract: Mapping[str, Any]) -> str:
    return sha256_bytes(canonical_json_bytes(dict(contract)))


def audited_contract_summary(contract: Mapping[str, Any]) -> Tuple[Tuple[int, int, int], str]:
    shape = (int(contract["n_mels"]), int(contract["max_frames"]), 1)
    return shape, frontend_contract_sha256(contract)
