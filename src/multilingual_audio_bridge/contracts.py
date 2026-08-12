"""Frozen code-level contracts for DATA-20260812-03."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from src.multilingual_retraining.contracts import LABELS, LANGUAGES, SPLITS


ACQUISITION_PLAN_SCHEMA = "drone.multilingual_acquisition_plan.v0"
ACQUISITION_RECEIPT_SCHEMA = "drone.multilingual_acquisition_receipt.v0"
METADATA_BOOTSTRAP_RECEIPT_SCHEMA = "drone.multilingual_metadata_bootstrap_receipt.v0"
MATERIALIZATION_INDEX_SCHEMA = "drone.multilingual_materialization_index.v0"
LINEAGE_SCHEMA = "drone.multilingual_audio_lineage.v0"
STAGE_RECEIPT_SCHEMA = "drone.multilingual_materialization_stage_receipt.v0"
ABORT_RECEIPT_SCHEMA = "drone.multilingual_materialization_abort_receipt.v0"
BRIDGE_VALIDATOR_VERSION = "dataset-audio-bridge-v0"
PROPOSAL_SCHEMA = "talk-to-me-drone.metadata-feasibility-report.v1"
PROPOSAL_RECEIPT_SCHEMA = "drone.multilingual_metadata_proposal_freeze_receipt.v0"

HEX64 = re.compile(r"^[0-9a-f]{64}$")
TARGET_SAMPLE_RATE = 16000
TARGET_NUM_SAMPLES = 16000
TARGET_CHANNELS = 1
TARGET_SUBTYPE = "PCM_16"


class BridgeError(ValueError):
    """Raised when a bridge stage must fail closed."""


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_sha256(value: Any, context: str) -> str:
    if not isinstance(value, str) or not HEX64.fullmatch(value):
        raise BridgeError(f"{context} must be a lowercase SHA-256")
    return value


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("wb") as handle:
        handle.write(payload)
        handle.flush()
    temporary.replace(path)


def atomic_json(path: Path, value: Any) -> None:
    atomic_write(path, canonical_json_bytes(value) + b"\n")


def validate_shared_contract() -> None:
    if tuple(LABELS) != ("emergency", "movement", "unknown"):
        raise BridgeError("Baseline ordered labels changed")
    if tuple(LANGUAGES) != ("en", "es", "de"):
        raise BridgeError("Baseline language contract changed")
    if tuple(SPLITS) != (
        "train",
        "validation_selection",
        "validation_calibration",
        "test",
    ):
        raise BridgeError("Baseline four-split contract changed")
