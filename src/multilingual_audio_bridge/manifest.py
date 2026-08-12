"""Producer and Dataset-owner validator for the Baseline frozen manifest."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

import numpy as np

from src.multilingual_retraining.contracts import (
    LABELS,
    LANGUAGES,
    MANIFEST_SCHEMA,
    SPLITS,
    VALIDATION_RECEIPT_SCHEMA,
)
from src.multilingual_retraining.frontend import load_exact_mono_pcm
from src.multilingual_retraining.manifest import (
    REQUIRED_FIELDS,
    load_frozen_manifest,
    resolve_audio_path,
)

from .contracts import (
    BRIDGE_VALIDATOR_VERSION,
    MATERIALIZATION_INDEX_SCHEMA,
    BridgeError,
    atomic_json,
    atomic_write,
    canonical_json_bytes,
    require_sha256,
    sha256_bytes,
    sha256_file,
    validate_shared_contract,
)


def _load_json(path: str | Path, context: str) -> Dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BridgeError(f"cannot load {context}: {exc}") from exc
    if not isinstance(value, dict):
        raise BridgeError(f"{context} must be a JSON object")
    return value


def _load_jsonl(path: str | Path) -> List[Dict[str, Any]]:
    rows = []
    try:
        with Path(path).open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise BridgeError(f"line {line_number}: JSONL row must be an object")
                rows.append(row)
    except (OSError, json.JSONDecodeError) as exc:
        raise BridgeError(f"cannot load JSONL {path}: {exc}") from exc
    if not rows:
        raise BridgeError(f"JSONL is empty: {path}")
    return rows


def _pcm_sha(waveform: np.ndarray) -> str:
    return sha256_bytes(np.asarray(waveform, dtype="<f4").tobytes(order="C"))


def _group_overlap(records: Sequence[Mapping[str, Any]], field: str) -> Dict[str, List[str]]:
    groups: Dict[str, set[str]] = defaultdict(set)
    for record in records:
        groups[str(record[field])].add(str(record["split"]))
    return {key: sorted(splits) for key, splits in groups.items() if len(splits) > 1}


def _support(records: Sequence[Mapping[str, Any]]) -> Dict[str, int]:
    counts = Counter(
        (record["split"], record["language"], record["label"])
        for record in records
    )
    missing = [
        f"{split}|{language}|{label}"
        for split in SPLITS
        for language in LANGUAGES
        for label in LABELS
        if counts[(split, language, label)] == 0
    ]
    if missing:
        raise BridgeError(f"frozen manifest has empty language/class/split cells: {missing[:8]}")
    return {
        f"{split}|{language}|{label}": counts[(split, language, label)]
        for split in SPLITS
        for language in LANGUAGES
        for label in LABELS
    }


def _source_archive_hashes(acquisition: Mapping[str, Any]) -> Dict[str, str]:
    result = {}
    for asset in acquisition.get("assets", []):
        asset_id = str(asset["asset_id"])
        result[asset_id] = require_sha256(
            asset["download"]["archive_sha256"], f"{asset_id}.archive_sha256"
        )
    if not result:
        raise BridgeError("acquisition receipt has no source archive receipts")
    return dict(sorted(result.items()))


def produce_frozen_manifest(
    materialization_index_path: str | Path,
    lineage_path: str | Path,
    acquisition_receipt_path: str | Path,
    audio_root: str | Path,
    output_dir: str | Path,
    config_sha256: str,
    proposal_sha256: str,
    fixture_only: bool = False,
) -> Dict[str, Any]:
    validate_shared_contract()
    if len(REQUIRED_FIELDS) != 21:
        raise BridgeError(
            f"Baseline consumer field contract changed: expected audited 21, got {len(REQUIRED_FIELDS)}"
        )
    config_sha = require_sha256(config_sha256, "config_sha256")
    proposal_sha = require_sha256(proposal_sha256, "proposal_sha256")
    index_rows = _load_jsonl(materialization_index_path)
    lineage_rows = _load_jsonl(lineage_path)
    acquisition = _load_json(acquisition_receipt_path, "acquisition receipt")
    if acquisition.get("status") != "pass" or acquisition.get("no_reidentification_performed") is not True:
        raise BridgeError("acquisition receipt does not pass provenance gates")
    acquisition_plan_sha = require_sha256(
        acquisition.get("plan_sha256"), "acquisition plan_sha256"
    )
    records: List[Dict[str, Any]] = []
    for row in index_rows:
        if row.get("schema_version") != MATERIALIZATION_INDEX_SCHEMA:
            raise BridgeError("unexpected materialization index schema")
        record = row.get("manifest_record")
        if not isinstance(record, dict) or set(record) != set(REQUIRED_FIELDS):
            raise BridgeError(
                "materialization manifest_record must contain exactly the 21-field consumer contract"
            )
        records.append({field: record[field] for field in REQUIRED_FIELDS})
    if len({record["sample_id"] for record in records}) != len(records):
        raise BridgeError("materialization index sample IDs are not unique")
    if {row.get("sample_id") for row in lineage_rows} != {record["sample_id"] for record in records}:
        raise BridgeError("lineage and materialization sample sets differ")

    isolation_overlap = _group_overlap(records, "isolation_group_id")
    duplicate_overlap = _group_overlap(records, "duplicate_group_id")
    if isolation_overlap or duplicate_overlap:
        raise BridgeError(
            "manifest isolation/duplicate overlap: "
            f"isolation={dict(list(isolation_overlap.items())[:3])}, "
            f"duplicate={dict(list(duplicate_overlap.items())[:3])}"
        )
    support = _support(records)
    root = Path(audio_root).resolve()
    for record in records:
        path = resolve_audio_path(root, record)
        waveform = load_exact_mono_pcm(path, expected_sha256=record["audio_sha256"])
        if _pcm_sha(waveform) != record["decoded_pcm_sha256"]:
            raise BridgeError(f"decoded PCM SHA mismatch: {record['sample_id']}")

    records.sort(key=lambda record: str(record["sample_id"]))
    manifest_payload = b"".join(canonical_json_bytes(record) + b"\n" for record in records)
    destination = Path(output_dir).resolve()
    manifest_path = destination / "multilingual_audio_manifest_v0.jsonl"
    receipt_path = destination / "multilingual_manifest_validation_receipt_v0.json"
    atomic_write(manifest_path, manifest_payload)
    manifest_sha = sha256_file(manifest_path)
    manifest_versions = sorted({str(record["manifest_version"]) for record in records})
    if len(manifest_versions) != 1:
        raise BridgeError(f"materialization rows have multiple manifest versions: {manifest_versions}")
    receipt = {
        "schema_version": VALIDATION_RECEIPT_SCHEMA,
        "owner": "dataset",
        "validator_version": BRIDGE_VALIDATOR_VERSION,
        "status": "pass",
        "frozen": True,
        "fixture_only": bool(fixture_only),
        "manifest_schema_version": MANIFEST_SCHEMA,
        "manifest_version": manifest_versions[0],
        "manifest_sha256": manifest_sha,
        "manifest_field_count": len(REQUIRED_FIELDS),
        "manifest_required_fields": list(REQUIRED_FIELDS),
        "labels": list(LABELS),
        "languages": list(LANGUAGES),
        "splits": list(SPLITS),
        "record_count": len(records),
        "support": support,
        "isolation_audit": {
            "isolation_group_overlap_count": 0,
            "duplicate_group_overlap_count": 0,
        },
        "source_archive_sha256": _source_archive_hashes(acquisition),
        "acquisition_plan_sha256": acquisition_plan_sha,
        "config_sha256": config_sha,
        "proposal_sha256": proposal_sha,
        "materialization_index_sha256": sha256_file(materialization_index_path),
        "lineage_sha256": sha256_file(lineage_path),
        "audio_root": str(root),
        "license_and_attribution_receipts_preserved": True,
        "no_reidentification_performed": True,
        "redistribution_authorized": False,
    }
    atomic_json(receipt_path, receipt)

    consumer = load_frozen_manifest(
        manifest_path,
        receipt_path,
        selected_languages=LANGUAGES,
        expected_manifest_languages=LANGUAGES,
    )
    if consumer.full_record_count != len(records):
        raise BridgeError("Baseline consumer returned an unexpected record count")
    return {
        "status": "pass",
        "manifest": str(manifest_path),
        "manifest_sha256": manifest_sha,
        "validation_receipt": str(receipt_path),
        "validation_receipt_sha256": sha256_file(receipt_path),
        "record_count": len(records),
        "support": support,
        "consumer_compatibility": {
            "consumer": "src.multilingual_retraining.manifest.load_frozen_manifest",
            "consumer_commit_source": "1a261df80ac12729d0820cb089372c01e39b1c2e",
            "loaded": True,
            "required_field_count": len(REQUIRED_FIELDS),
            "split_sha256": consumer.split_sha256,
            "manifest_languages": list(consumer.manifest_languages),
        },
    }
