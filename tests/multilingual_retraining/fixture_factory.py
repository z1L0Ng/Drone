"""Create small, license-free synthetic manifest fixtures in temporary paths."""

from __future__ import annotations

import hashlib
import json
import wave
from pathlib import Path
from typing import Dict

import numpy as np

from src.multilingual_retraining.config import sha256_file
from src.multilingual_retraining.contracts import LABELS, MANIFEST_SCHEMA, SPLITS, VALIDATION_RECEIPT_SCHEMA
from src.multilingual_retraining.frontend import load_exact_mono_pcm


def _write_wav(path: Path, frequency: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    time = np.arange(16000, dtype=np.float64) / 16000.0
    pcm = np.asarray(np.sin(2.0 * np.pi * frequency * time) * 4096.0, dtype="<i2")
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(16000)
        handle.writeframes(pcm.tobytes())


def create_fixture(root: Path) -> Dict[str, Path]:
    audio_root = root / "audio"
    manifest_path = root / "manifest.jsonl"
    receipt_path = root / "manifest_validation_receipt.json"
    records = []
    ordinal = 0
    for split in SPLITS:
        for language in ("en", "es", "de"):
            for label in LABELS:
                sample_id = f"{split}-{language}-{label}"
                relative = f"{language}/{split}/{label}.wav"
                audio_path = audio_root / relative
                _write_wav(audio_path, 180.0 + ordinal * 7.0)
                waveform = load_exact_mono_pcm(audio_path)
                pcm_hash = hashlib.sha256(
                    np.ascontiguousarray(waveform.astype("<f4")).tobytes()
                ).hexdigest()
                records.append(
                    {
                        "schema_version": MANIFEST_SCHEMA,
                        "manifest_version": "synthetic-fixture-v0",
                        "sample_id": sample_id,
                        "relative_audio_path": relative,
                        "audio_sha256": sha256_file(audio_path),
                        "decoded_pcm_sha256": pcm_hash,
                        "source_dataset": f"synthetic_fixture_{language}",
                        "source_release": "synthetic-v0",
                        "language": language,
                        "source_word": f"fixture_{label}",
                        "label": label,
                        "speaker_id": f"speaker-{sample_id}",
                        "voice_id": "",
                        "isolation_group_id": f"isolation-{sample_id}",
                        "duplicate_group_id": f"duplicate-{sample_id}",
                        "split": split,
                        "license_id": "CC0-1.0-synthetic",
                        "provenance_status": "accepted",
                        "sample_rate_hz": 16000,
                        "channels": 1,
                        "num_samples": 16000,
                    }
                )
                ordinal += 1
    manifest_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in records),
        encoding="utf-8",
    )
    receipt = {
        "schema_version": VALIDATION_RECEIPT_SCHEMA,
        "owner": "dataset",
        "validator_version": "synthetic-test-validator-v0",
        "status": "pass",
        "frozen": True,
        "fixture_only": True,
        "manifest_sha256": sha256_file(manifest_path),
        "manifest_schema_version": MANIFEST_SCHEMA,
        "languages": ["en", "es", "de"],
        "labels": list(LABELS),
        "isolation_audit": {
            "isolation_group_overlap_count": 0,
            "duplicate_group_overlap_count": 0,
        },
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "audio_root": audio_root,
        "manifest": manifest_path,
        "receipt": receipt_path,
    }
