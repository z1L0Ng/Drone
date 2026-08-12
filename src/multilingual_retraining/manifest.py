"""Frozen-manifest loader and Dataset-owner validation-receipt adapter."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

from .config import canonical_json_bytes, sha256_bytes, sha256_file
from .contracts import LABELS, MANIFEST_SCHEMA, SPLITS, VALIDATION_RECEIPT_SCHEMA


class ManifestError(ValueError):
    """Raised when a manifest or its validation receipt fails closed."""


REQUIRED_FIELDS = (
    "schema_version",
    "manifest_version",
    "sample_id",
    "relative_audio_path",
    "audio_sha256",
    "decoded_pcm_sha256",
    "source_dataset",
    "source_release",
    "language",
    "source_word",
    "label",
    "speaker_id",
    "voice_id",
    "isolation_group_id",
    "duplicate_group_id",
    "split",
    "license_id",
    "provenance_status",
    "sample_rate_hz",
    "channels",
    "num_samples",
)


@dataclass(frozen=True)
class FrozenManifest:
    path: Path
    sha256: str
    version: str
    records: Tuple[Mapping[str, Any], ...]
    validation_receipt_path: Path
    validation_receipt_sha256: str
    split_sha256: str
    selected_languages: Tuple[str, ...]
    manifest_languages: Tuple[str, ...]
    full_record_count: int
    fixture_only: bool

    def split(self, name: str) -> Tuple[Mapping[str, Any], ...]:
        return tuple(record for record in self.records if record["split"] == name)

    def support(self) -> Dict[str, int]:
        counts = Counter(
            (record["split"], record["language"], record["label"])
            for record in self.records
        )
        return {
            f"{split}|{language}|{label}": count
            for (split, language, label), count in sorted(counts.items())
        }


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()


def _validate_relative_path(value: Any, sample_id: str) -> None:
    if not isinstance(value, str) or not value:
        raise ManifestError(f"{sample_id}: relative_audio_path must be non-empty")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise ManifestError(f"{sample_id}: unsafe relative_audio_path {value!r}")


def _group_split_check(records: Sequence[Mapping[str, Any]], field: str) -> None:
    seen: Dict[str, set[str]] = defaultdict(set)
    for record in records:
        value = str(record.get(field, "")).strip()
        if value:
            seen[value].add(str(record["split"]))
    leaking = {key: sorted(value) for key, value in seen.items() if len(value) > 1}
    if leaking:
        preview = dict(list(sorted(leaking.items()))[:5])
        raise ManifestError(f"{field} crosses splits: {preview}")


def _validate_record(record: Mapping[str, Any], expected_languages: Sequence[str]) -> None:
    missing = [field for field in REQUIRED_FIELDS if field not in record]
    if missing:
        raise ManifestError(f"manifest row missing fields {missing}: {record.get('sample_id', '<unknown>')}")
    sample_id = str(record["sample_id"])
    if record["schema_version"] != MANIFEST_SCHEMA:
        raise ManifestError(f"{sample_id}: unexpected schema_version")
    if record["label"] not in LABELS:
        raise ManifestError(f"{sample_id}: invalid label {record['label']!r}")
    if record["language"] not in expected_languages:
        raise ManifestError(f"{sample_id}: language {record['language']!r} is outside lane")
    if record["split"] not in SPLITS:
        raise ManifestError(f"{sample_id}: invalid split {record['split']!r}")
    if record["provenance_status"] != "accepted":
        raise ManifestError(f"{sample_id}: provenance_status must be accepted")
    if not str(record["source_dataset"]).strip() or not str(record["source_release"]).strip():
        raise ManifestError(f"{sample_id}: source_dataset and source_release are required")
    if not str(record["license_id"]).strip():
        raise ManifestError(f"{sample_id}: license_id is required")
    if not (str(record["speaker_id"]).strip() or str(record["voice_id"]).strip()):
        raise ManifestError(f"{sample_id}: speaker_id or voice_id is required")
    if not str(record["isolation_group_id"]).strip():
        raise ManifestError(f"{sample_id}: isolation_group_id is required")
    if not str(record["duplicate_group_id"]).strip():
        raise ManifestError(f"{sample_id}: duplicate_group_id is required")
    if not str(record["source_word"]).strip():
        raise ManifestError(f"{sample_id}: source_word is required for provenance/sampling")
    if record["sample_rate_hz"] != 16000 or record["channels"] != 1 or record["num_samples"] != 16000:
        raise ManifestError(f"{sample_id}: audio metadata must be mono PCM 16 kHz / 16000 samples")
    if not _is_sha256(record["audio_sha256"]) or not _is_sha256(record["decoded_pcm_sha256"]):
        raise ManifestError(f"{sample_id}: invalid audio/PCM SHA-256")
    _validate_relative_path(record["relative_audio_path"], sample_id)


def _load_json(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"cannot load validation receipt {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ManifestError("validation receipt must be a JSON object")
    return value


def load_frozen_manifest(
    manifest_path: str | Path,
    validation_receipt_path: str | Path,
    selected_languages: Sequence[str],
    expected_manifest_languages: Sequence[str],
) -> FrozenManifest:
    path = Path(manifest_path).resolve()
    receipt_path = Path(validation_receipt_path).resolve()
    manifest_sha = sha256_file(path)
    receipt = _load_json(receipt_path)
    if receipt.get("schema_version") != VALIDATION_RECEIPT_SCHEMA:
        raise ManifestError(f"unexpected validation receipt schema: {receipt.get('schema_version')!r}")
    if receipt.get("status") != "pass" or receipt.get("frozen") is not True:
        raise ManifestError("Dataset-owner validation receipt must have status=pass and frozen=true")
    if receipt.get("owner") != "dataset" or not str(receipt.get("validator_version", "")).strip():
        raise ManifestError("validation receipt must identify owner=dataset and a validator_version")
    if receipt.get("manifest_sha256") != manifest_sha:
        raise ManifestError("manifest SHA-256 does not match validation receipt")
    if receipt.get("manifest_schema_version") != MANIFEST_SCHEMA:
        raise ManifestError("validation receipt does not attest the required manifest schema")
    attested_languages = tuple(sorted(str(value) for value in receipt.get("languages", [])))
    expected_all = tuple(sorted(str(value) for value in expected_manifest_languages))
    selected = tuple(str(value) for value in selected_languages)
    if attested_languages != expected_all:
        raise ManifestError(
            f"validation receipt languages {attested_languages} do not match expected manifest languages {expected_all}"
        )
    if not set(selected).issubset(attested_languages):
        raise ManifestError("lane languages must be a subset of the frozen manifest languages")
    isolation = receipt.get("isolation_audit", {})
    for field in ("isolation_group_overlap_count", "duplicate_group_overlap_count"):
        if isolation.get(field) != 0:
            raise ManifestError(f"validation receipt {field} must be zero")

    records: List[Mapping[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ManifestError(f"line {line_number}: row must be a JSON object")
                _validate_record(row, attested_languages)
                records.append(row)
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"cannot parse manifest {path}: {exc}") from exc
    if not records:
        raise ManifestError("manifest is empty")
    ids = [str(record["sample_id"]) for record in records]
    if len(ids) != len(set(ids)):
        raise ManifestError("sample_id values must be unique")
    versions = {str(record["manifest_version"]) for record in records}
    if len(versions) != 1:
        raise ManifestError(f"manifest rows contain multiple versions: {sorted(versions)}")

    _group_split_check(records, "isolation_group_id")
    _group_split_check(records, "duplicate_group_id")
    languages_in_manifest = sorted({str(record["language"]) for record in records})
    if languages_in_manifest != list(attested_languages):
        raise ManifestError(
            f"manifest languages {languages_in_manifest} do not equal attested languages {list(attested_languages)}"
        )
    if tuple(receipt.get("labels", ())) != LABELS:
        raise ManifestError("validation receipt must attest the ordered 3-class label encoder")

    full_record_count = len(records)
    records = [record for record in records if record["language"] in selected]
    for split in SPLITS:
        if not any(record["split"] == split for record in records):
            raise ManifestError(f"required lane split is empty after language filtering: {split}")

    split_rows = [
        {"sample_id": record["sample_id"], "split": record["split"]}
        for record in sorted(records, key=lambda item: str(item["sample_id"]))
    ]
    return FrozenManifest(
        path=path,
        sha256=manifest_sha,
        version=versions.pop(),
        records=tuple(records),
        validation_receipt_path=receipt_path,
        validation_receipt_sha256=sha256_file(receipt_path),
        split_sha256=sha256_bytes(canonical_json_bytes(split_rows)),
        selected_languages=selected,
        manifest_languages=attested_languages,
        full_record_count=full_record_count,
        fixture_only=receipt.get("fixture_only") is True,
    )


def resolve_audio_path(audio_root: str | Path, record: Mapping[str, Any]) -> Path:
    root = Path(audio_root).resolve()
    candidate = (root / str(record["relative_audio_path"])).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ManifestError(f"audio path escapes root: {record['relative_audio_path']}") from exc
    return candidate
