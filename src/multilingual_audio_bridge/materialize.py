"""Deterministic audio materialization with raw-to-derived lineage receipts."""

from __future__ import annotations

import csv
import json
import math
import wave
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

import numpy as np

from src.multilingual_retraining.contracts import LABELS, LANGUAGES, SPLITS
from src.multilingual_retraining.frontend import load_exact_mono_pcm

from .contracts import (
    LINEAGE_SCHEMA,
    MATERIALIZATION_INDEX_SCHEMA,
    PROPOSAL_RECEIPT_SCHEMA,
    TARGET_CHANNELS,
    TARGET_NUM_SAMPLES,
    TARGET_SAMPLE_RATE,
    TARGET_SUBTYPE,
    BridgeError,
    atomic_write,
    canonical_json_bytes,
    require_sha256,
    sha256_bytes,
    sha256_file,
    validate_shared_contract,
)


SPLIT_FREEZE_APPROVAL_ENV = "DRONE_W33_SPLIT_FREEZE_APPROVED"
PCM16_CLIP_LIMIT = 32767.0 / 32768.0


PROPOSAL_REQUIRED_FIELDS = (
    "source_record_id",
    "dataset_key",
    "dataset_version",
    "language",
    "source_word",
    "canonical_class",
    "mapping_role",
    "mapping_status",
    "mapping_admitted",
    "speaker_id",
    "source_clip_family",
    "source_audio_relpath",
    "isolation_component_id",
    "proposed_split",
    "original_split",
    "metadata_entry_id",
    "metadata_row",
    "crop_start_sample",
    "speech_start_sample",
    "speech_end_sample",
)

PROPOSAL_NONEMPTY_FIELDS = tuple(
    field
    for field in PROPOSAL_REQUIRED_FIELDS
    if field not in {"crop_start_sample", "speech_start_sample", "speech_end_sample"}
)


def _load_json(path: Path, context: str) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BridgeError(f"cannot load {context} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BridgeError(f"{context} must be a JSON object")
    return value


def load_frozen_proposal(
    proposal_path: str | Path, receipt_path: str | Path
) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
    from src.multilingual_retraining.contracts import LABELS, LANGUAGES, SPLITS

    proposal = Path(proposal_path).resolve()
    receipt = _load_json(Path(receipt_path).resolve(), "proposal freeze receipt")
    if receipt.get("schema_version") != PROPOSAL_RECEIPT_SCHEMA:
        raise BridgeError("unexpected proposal freeze receipt schema")
    if receipt.get("owner") != "dataset" or receipt.get("status") != "pass":
        raise BridgeError("proposal receipt must identify owner=dataset and status=pass")
    if receipt.get("frozen") is not True or receipt.get("canonical_manifest_created") is not False:
        raise BridgeError("input proposal must be frozen but not claim a canonical manifest")
    if receipt.get("proposal_sha256") != sha256_file(proposal):
        raise BridgeError("frozen proposal SHA-256 mismatch")
    require_sha256(receipt.get("config_sha256"), "proposal receipt config_sha256")
    if tuple(receipt.get("labels", ())) != tuple(LABELS):
        raise BridgeError("proposal receipt ordered labels do not match Baseline")
    if tuple(receipt.get("languages", ())) != tuple(LANGUAGES):
        raise BridgeError("proposal receipt languages do not match Baseline")
    if tuple(receipt.get("splits", ())) != tuple(SPLITS):
        raise BridgeError("proposal receipt four splits do not match Baseline")
    audit = receipt.get("isolation_audit", {})
    if audit.get("speaker_overlap_count") != 0 or audit.get("source_family_overlap_count") != 0:
        raise BridgeError("proposal receipt reports identity overlap")

    with proposal.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or tuple(reader.fieldnames) != PROPOSAL_REQUIRED_FIELDS:
            raise BridgeError(
                f"proposal fields must be exact and ordered: {list(PROPOSAL_REQUIRED_FIELDS)}"
            )
        rows = [dict(row) for row in reader]
    if not rows:
        raise BridgeError("proposal is empty")
    identities = set()
    component_splits: Dict[str, set[str]] = defaultdict(set)
    family_splits: Dict[Tuple[str, str], set[str]] = defaultdict(set)
    speaker_splits: Dict[Tuple[str, str], set[str]] = defaultdict(set)
    for row in rows:
        if any(not row[field].strip() for field in PROPOSAL_NONEMPTY_FIELDS):
            raise BridgeError(f"proposal row has empty required field: {row.get('source_record_id')}")
        if row["mapping_admitted"].casefold() != "true":
            raise BridgeError(f"non-admitted row cannot be materialized: {row['source_record_id']}")
        if row["canonical_class"] not in LABELS or row["language"] not in LANGUAGES:
            raise BridgeError(f"proposal row is outside the shared label/language contract")
        if row["proposed_split"] not in SPLITS:
            raise BridgeError(f"invalid proposed split {row['proposed_split']!r}")
        identity = (row["dataset_key"], row["source_record_id"])
        if identity in identities:
            raise BridgeError(f"duplicate proposal source record: {identity}")
        identities.add(identity)
        split = row["proposed_split"]
        component_splits[row["isolation_component_id"]].add(split)
        family_splits[(row["dataset_key"], row["source_clip_family"])].add(split)
        speaker_splits[(row["dataset_key"], row["speaker_id"])].add(split)
    for field, values in (
        ("isolation_component", component_splits),
        ("source_clip_family", family_splits),
        ("speaker", speaker_splits),
    ):
        leaking = [key for key, splits in values.items() if len(splits) > 1]
        if leaking:
            raise BridgeError(f"{field} crosses proposal splits: {leaking[:3]}")
    return rows, receipt


def freeze_metadata_proposal(
    config_path: str | Path,
    proposal_path: str | Path,
    feasibility_report_path: str | Path,
    output_path: str | Path,
    execute: bool = False,
) -> Dict[str, Any]:
    """Validate and attest a metadata proposal without creating audio or a canonical manifest."""

    import os

    from src.multilingual_retraining.contracts import LABELS, LANGUAGES, SPLITS
    from src.multilingual_three_class_intake import load_json_yaml, validate_config, validate_report

    config = load_json_yaml(Path(config_path))
    validate_config(config)
    report = _load_json(Path(feasibility_report_path), "feasibility report")
    validate_report(report, config)
    proposal = Path(proposal_path).resolve()
    config_sha = sha256_file(config_path)
    proposal_sha = sha256_file(proposal)
    report_sha = sha256_file(feasibility_report_path)
    if report.get("hashes", {}).get("proposal_manifest_sha256") != proposal_sha:
        raise BridgeError("feasibility report does not attest the proposal bytes")

    with proposal.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or tuple(reader.fieldnames) != PROPOSAL_REQUIRED_FIELDS:
            raise BridgeError("proposal fields do not match the frozen bridge contract")
        rows = [dict(row) for row in reader]
    if not rows:
        raise BridgeError("proposal is empty")
    cells = Counter()
    speakers: Dict[Tuple[str, str], set[str]] = defaultdict(set)
    families: Dict[Tuple[str, str], set[str]] = defaultdict(set)
    components: Dict[str, set[str]] = defaultdict(set)
    for row in rows:
        if row["mapping_admitted"].casefold() != "true":
            raise BridgeError(f"proposal contains non-admitted mapping: {row['source_record_id']}")
        if row["language"] not in LANGUAGES or row["canonical_class"] not in LABELS:
            raise BridgeError("proposal contains an invalid language or class")
        if row["proposed_split"] not in SPLITS:
            raise BridgeError("proposal contains a non-canonical four-split value")
        cells[(row["proposed_split"], row["language"], row["canonical_class"])] += 1
        speakers[(row["dataset_key"], row["speaker_id"])].add(row["proposed_split"])
        families[(row["dataset_key"], row["source_clip_family"])].add(row["proposed_split"])
        components[row["isolation_component_id"]].add(row["proposed_split"])
    missing = [
        f"{split}|{language}|{label}"
        for split in SPLITS
        for language in LANGUAGES
        for label in LABELS
        if cells[(split, language, label)] == 0
    ]
    if missing:
        raise BridgeError(f"proposal is not trainable across all 36 cells: {missing[:8]}")
    speaker_overlap = sum(len(value) > 1 for value in speakers.values())
    family_overlap = sum(len(value) > 1 for value in families.values())
    component_overlap = sum(len(value) > 1 for value in components.values())
    if speaker_overlap or family_overlap or component_overlap:
        raise BridgeError("proposal identity/component isolation failed")
    preview = {
        "schema_version": PROPOSAL_RECEIPT_SCHEMA,
        "owner": "dataset",
        "status": "pass",
        "frozen": True,
        "canonical_manifest_created": False,
        "proposal_sha256": proposal_sha,
        "config_sha256": config_sha,
        "feasibility_report_sha256": report_sha,
        "labels": list(LABELS),
        "languages": list(LANGUAGES),
        "splits": list(SPLITS),
        "record_count": len(rows),
        "support": {
            f"{split}|{language}|{label}": cells[(split, language, label)]
            for split in SPLITS
            for language in LANGUAGES
            for label in LABELS
        },
        "isolation_audit": {
            "speaker_overlap_count": 0,
            "source_family_overlap_count": 0,
            "component_overlap_count": 0,
        },
        "real_audio_opened": False,
        "canonical_audio_manifest_created": False,
    }
    if not execute:
        return {**preview, "dry_run": True, "receipt_written": False}
    if os.environ.get(SPLIT_FREEZE_APPROVAL_ENV) != "YES":
        raise BridgeError(
            f"proposal freeze requires --execute and {SPLIT_FREEZE_APPROVAL_ENV}=YES"
        )
    destination = Path(output_path).resolve()
    payload = canonical_json_bytes(preview) + b"\n"
    if destination.exists():
        if destination.read_bytes() != payload:
            raise BridgeError(
                f"existing proposal freeze receipt differs from deterministic output: {destination}"
            )
    else:
        atomic_write(destination, payload)
    return {**preview, "dry_run": False, "receipt_written": True, "path": str(destination)}


def _load_acquisition_receipt(path: str | Path) -> Dict[str, Any]:
    receipt = _load_json(Path(path).resolve(), "acquisition receipt")
    if receipt.get("schema_version") != "drone.multilingual_acquisition_receipt.v0":
        raise BridgeError("unexpected acquisition receipt schema")
    if receipt.get("status") != "pass" or receipt.get("no_reidentification_performed") is not True:
        raise BridgeError("acquisition receipt must pass and attest no re-identification")
    if receipt.get("redistribution_authorized") is not False:
        raise BridgeError("acquisition receipt must not authorize redistribution")
    require_sha256(receipt.get("plan_sha256"), "acquisition receipt plan_sha256")
    return receipt


def _asset_roots(receipt: Mapping[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    roots: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for asset in receipt.get("assets", []):
        if asset.get("asset_role", "audio_archive") != "audio_archive":
            continue
        destination = Path(asset["extraction"]["destination"]).resolve()
        if not destination.is_dir():
            raise BridgeError(f"acquired source root missing: {destination}")
        archive_sha = require_sha256(
            asset["download"]["archive_sha256"], f"{asset['asset_id']}.archive_sha256"
        )
        roots[str(asset["dataset_key"])].append(
            {
                "asset_id": str(asset["asset_id"]),
                "root": destination,
                "archive_sha256": archive_sha,
                "release": str(asset["release"]),
                "language": str(
                    asset.get("language")
                    or ("en" if asset.get("dataset_key") == "gsc_v2" else "")
                ),
            }
        )
    return roots


def _safe_relative(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise BridgeError(f"unsafe source_audio_relpath {value!r}")
    return path


def _build_audio_locator(
    rows: Sequence[Mapping[str, str]], roots: Mapping[str, Sequence[Mapping[str, Any]]]
) -> Dict[Tuple[str, str, str], Tuple[Path, Mapping[str, Any]]]:
    targets: Dict[Tuple[str, str], Dict[str, List[PurePosixPath]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for row in rows:
        dataset = row["dataset_key"]
        language = row["language"]
        relative = _safe_relative(row["source_audio_relpath"])
        targets[(dataset, language)][relative.name].append(relative)
    matches: Dict[Tuple[str, str, str], List[Tuple[Path, Mapping[str, Any]]]] = defaultdict(list)
    for (dataset, language), by_name in targets.items():
        if dataset not in roots:
            raise BridgeError(f"no acquired root for dataset {dataset}")
        for asset in roots[dataset]:
            if asset["language"] != language:
                continue
            for candidate in asset["root"].rglob("*.wav"):
                options = by_name.get(candidate.name, ())
                for relative in options:
                    if tuple(candidate.parts[-len(relative.parts) :]) == relative.parts:
                        matches[(dataset, language, relative.as_posix())].append(
                            (candidate.resolve(), asset)
                        )
    result = {}
    for (dataset, language), by_name in targets.items():
        for options in by_name.values():
            for relative in options:
                key = (dataset, language, relative.as_posix())
                unique = {
                    (str(path), str(asset["asset_id"])): (path, asset)
                    for path, asset in matches.get(key, [])
                }
                if len(unique) != 1:
                    raise BridgeError(
                        f"audio locator must resolve exactly once for {dataset}:{language}:{relative}; "
                        f"found {len(unique)}"
                    )
                result[key] = next(iter(unique.values()))
    return result


def _decode_and_convert(
    path: Path, row: Mapping[str, str]
) -> Tuple[np.ndarray, Dict[str, Any]]:
    import scipy
    import scipy.signal
    import soundfile as sf

    info = sf.info(path)
    if info.format != "WAV" or not str(info.subtype).startswith("PCM_"):
        raise BridgeError(f"source audio must be WAV PCM: {path} ({info.format}/{info.subtype})")
    waveform, sample_rate = sf.read(path, dtype="float64", always_2d=True)
    waveform = np.asarray(waveform, dtype=np.float64)
    if waveform.shape[0] != info.frames or waveform.shape[1] != info.channels:
        raise BridgeError(f"decoder/header frame or channel mismatch: {path}")
    if not np.all(np.isfinite(waveform)):
        raise BridgeError(f"decode produced NaN/Inf: {path}")
    source_peak = float(np.max(np.abs(waveform))) if waveform.size else 0.0
    if waveform.size == 0 or source_peak >= PCM16_CLIP_LIMIT:
        raise BridgeError(f"empty or full-scale/clipped source audio: {path}")

    mono = waveform.mean(axis=1, dtype=np.float64)
    downmix = "none" if info.channels == 1 else "arithmetic_mean_float64"
    if sample_rate != TARGET_SAMPLE_RATE:
        divisor = math.gcd(int(sample_rate), TARGET_SAMPLE_RATE)
        up = TARGET_SAMPLE_RATE // divisor
        down = int(sample_rate) // divisor
        mono = scipy.signal.resample_poly(mono, up, down).astype(np.float64, copy=False)
        resample = {
            "applied": True,
            "implementation": "scipy.signal.resample_poly",
            "scipy_version": scipy.__version__,
            "up": up,
            "down": down,
        }
    else:
        resample = {"applied": False, "implementation": "identity"}
    if not np.all(np.isfinite(mono)) or (
        mono.size and float(np.max(np.abs(mono))) >= PCM16_CLIP_LIMIT
    ):
        raise BridgeError(f"resampling/downmix produced invalid or clipped values: {path}")

    crop_start = 0
    crop_end = len(mono)
    pad_right = 0
    if len(mono) > TARGET_NUM_SAMPLES:
        start_text = row.get("crop_start_sample", "").strip()
        speech_start_text = row.get("speech_start_sample", "").strip()
        speech_end_text = row.get("speech_end_sample", "").strip()
        if not start_text or not speech_start_text or not speech_end_text:
            raise BridgeError(f"overlength audio requires explicit speech/crop boundaries: {path}")
        crop_start = int(start_text)
        crop_end = crop_start + TARGET_NUM_SAMPLES
        speech_start = int(speech_start_text)
        speech_end = int(speech_end_text)
        if not (0 <= crop_start < crop_end <= len(mono)):
            raise BridgeError(f"crop boundary is outside decoded audio: {path}")
        if not (crop_start <= speech_start < speech_end <= crop_end):
            raise BridgeError(f"crop would remove an admitted word boundary: {path}")
        mono = mono[crop_start:crop_end]
    elif len(mono) < TARGET_NUM_SAMPLES:
        pad_right = TARGET_NUM_SAMPLES - len(mono)
        mono = np.pad(mono, (0, pad_right), mode="constant", constant_values=0.0)
    if mono.shape != (TARGET_NUM_SAMPLES,) or not np.all(np.isfinite(mono)):
        raise BridgeError(f"canonical waveform contract failed: {path}")
    return mono, {
        "decoder": "soundfile",
        "input_container": info.format,
        "input_codec": info.subtype,
        "input_sample_rate_hz": int(sample_rate),
        "input_channels": int(info.channels),
        "input_frames": int(info.frames),
        "input_peak_abs": source_peak,
        "downmix": downmix,
        "resample": resample,
        "crop_start": crop_start,
        "crop_end": crop_end,
        "pad_left": 0,
        "pad_right": pad_right,
        "output_sample_rate_hz": TARGET_SAMPLE_RATE,
        "output_channels": TARGET_CHANNELS,
        "output_samples": TARGET_NUM_SAMPLES,
        "output_subtype": TARGET_SUBTYPE,
    }


def _write_pcm16(path: Path, waveform: np.ndarray) -> None:
    if waveform.shape != (TARGET_NUM_SAMPLES,):
        raise BridgeError("cannot write non-canonical waveform")
    quantized = np.rint(waveform * 32767.0).astype("<i2")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with wave.open(str(temporary), "wb") as handle:
        handle.setnchannels(TARGET_CHANNELS)
        handle.setsampwidth(2)
        handle.setframerate(TARGET_SAMPLE_RATE)
        handle.setnframes(TARGET_NUM_SAMPLES)
        handle.writeframes(quantized.tobytes(order="C"))
    temporary.replace(path)


def _content_addressed_audio(audio_root: Path, waveform: np.ndarray) -> Tuple[Path, str, str]:
    temporary = audio_root / ".materializing.wav"
    _write_pcm16(temporary, waveform)
    audio_sha = sha256_file(temporary)
    destination = audio_root / audio_sha[:2] / f"{audio_sha}.wav"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if sha256_file(destination) != audio_sha:
            raise BridgeError(f"content-addressed audio collision: {destination}")
        temporary.unlink()
    else:
        temporary.replace(destination)
    decoded = load_exact_mono_pcm(destination, expected_sha256=audio_sha)
    decoded_pcm_sha = sha256_bytes(np.asarray(decoded, dtype="<f4").tobytes(order="C"))
    return destination, audio_sha, decoded_pcm_sha


def _license_by_dataset(receipt: Mapping[str, Any]) -> Dict[str, Mapping[str, Any]]:
    result = {}
    for item in receipt.get("license_receipts", []):
        key = str(item.get("dataset_key", ""))
        if key not in {"gsc_v2", "mswc"}:
            raise BridgeError("acquisition license receipt lacks an approved dataset_key")
        result[key] = item
    if set(result) != {"gsc_v2", "mswc"}:
        raise BridgeError("acquisition receipt license provenance is incomplete")
    return result


def _jsonl_bytes(rows: Iterable[Mapping[str, Any]]) -> bytes:
    return b"".join(canonical_json_bytes(row) + b"\n" for row in rows)


def materialize(
    proposal_path: str | Path,
    proposal_receipt_path: str | Path,
    acquisition_receipt_path: str | Path,
    output_root: str | Path,
    manifest_version: str,
) -> Dict[str, Any]:
    validate_shared_contract()
    proposal_rows, proposal_receipt = load_frozen_proposal(proposal_path, proposal_receipt_path)
    acquisition = _load_acquisition_receipt(acquisition_receipt_path)
    roots = _asset_roots(acquisition)
    licenses = _license_by_dataset(acquisition)
    locator = _build_audio_locator(proposal_rows, roots)
    root = Path(output_root).resolve()
    audio_root = root / "audio"
    audio_root.mkdir(parents=True, exist_ok=True)
    manifest_records: List[Dict[str, Any]] = []
    lineage_rows: List[Dict[str, Any]] = []
    qc_quarantine_rows: List[Dict[str, Any]] = []
    duplicate_splits: Dict[str, set[str]] = defaultdict(set)
    support = Counter()

    for row in sorted(proposal_rows, key=lambda item: (item["dataset_key"], item["source_record_id"])):
        raw_path, asset = locator[
            (row["dataset_key"], row["language"], row["source_audio_relpath"])
        ]
        raw_sha = sha256_file(raw_path)
        try:
            waveform, transform = _decode_and_convert(raw_path, row)
        except BridgeError as exc:
            qc_quarantine_rows.append(
                {
                    "schema_version": "drone.multilingual_audio_qc_quarantine.v0",
                    "source_record_id": row["source_record_id"],
                    "source_dataset": row["dataset_key"],
                    "source_release": row["dataset_version"],
                    "language": row["language"],
                    "source_word": row["source_word"],
                    "label": row["canonical_class"],
                    "split": row["proposed_split"],
                    "speaker_id": row["speaker_id"],
                    "source_clip_family": row["source_clip_family"],
                    "source_archive_id": asset["asset_id"],
                    "source_archive_sha256": asset["archive_sha256"],
                    "source_audio_path": str(raw_path),
                    "source_audio_sha256": raw_sha,
                    "reason": str(exc),
                    "disposition": "excluded_without_repair_or_substitution",
                }
            )
            continue
        derived_path, audio_sha, pcm_sha = _content_addressed_audio(audio_root, waveform)
        duplicate_group = f"decoded-pcm-sha256:{pcm_sha}"
        duplicate_splits[duplicate_group].add(row["proposed_split"])
        sample_id = sha256_bytes(
            canonical_json_bytes(
                {
                    "dataset": row["dataset_key"],
                    "record": row["source_record_id"],
                    "decoded_pcm_sha256": pcm_sha,
                }
            )
        )
        relative_audio_path = derived_path.relative_to(audio_root).as_posix()
        record = {
            "schema_version": "drone.multilingual_audio_manifest.v0",
            "manifest_version": manifest_version,
            "sample_id": sample_id,
            "relative_audio_path": relative_audio_path,
            "audio_sha256": audio_sha,
            "decoded_pcm_sha256": pcm_sha,
            "source_dataset": row["dataset_key"],
            "source_release": row["dataset_version"],
            "language": row["language"],
            "source_word": row["source_word"],
            "label": row["canonical_class"],
            "speaker_id": row["speaker_id"],
            "voice_id": "",
            "isolation_group_id": row["isolation_component_id"],
            "duplicate_group_id": duplicate_group,
            "split": row["proposed_split"],
            "license_id": licenses[row["dataset_key"]]["license_id"],
            "provenance_status": "accepted",
            "sample_rate_hz": TARGET_SAMPLE_RATE,
            "channels": TARGET_CHANNELS,
            "num_samples": TARGET_NUM_SAMPLES,
        }
        manifest_records.append(record)
        support[(record["split"], record["language"], record["label"])] += 1
        lineage_rows.append(
            {
                "schema_version": LINEAGE_SCHEMA,
                "sample_id": sample_id,
                "source_record_id": row["source_record_id"],
                "source_dataset": row["dataset_key"],
                "source_release": row["dataset_version"],
                "source_word": row["source_word"],
                "speaker_id": row["speaker_id"],
                "source_clip_family": row["source_clip_family"],
                "source_archive_id": asset["asset_id"],
                "source_archive_sha256": asset["archive_sha256"],
                "source_audio_path": str(raw_path),
                "source_audio_sha256": raw_sha,
                "derived_relative_audio_path": relative_audio_path,
                "audio_sha256": audio_sha,
                "decoded_pcm_sha256": pcm_sha,
                "transform": transform,
                "proposal_sha256": proposal_receipt["proposal_sha256"],
                "config_sha256": proposal_receipt["config_sha256"],
                "license_id": licenses[row["dataset_key"]]["license_id"],
                "attribution_source": licenses[row["dataset_key"]]["attribution_source"],
                "no_reidentification_performed": True,
                "redistribution_authorized": False,
            }
        )

    leaking = {key: sorted(value) for key, value in duplicate_splits.items() if len(value) > 1}
    if leaking:
        raise BridgeError(f"decoded duplicate family crosses splits: {dict(list(leaking.items())[:3])}")
    missing_cells = [
        f"{split}|{language}|{label}"
        for split in SPLITS
        for language in LANGUAGES
        for label in LABELS
        if support[(split, language, label)] == 0
    ]
    if missing_cells:
        raise BridgeError(
            f"audio QC quarantine empties language/class/split cells: {missing_cells[:8]}"
        )
    index_rows = [
        {
            "schema_version": MATERIALIZATION_INDEX_SCHEMA,
            "manifest_record": record,
            "lineage_sha256": sha256_bytes(canonical_json_bytes(lineage)),
        }
        for record, lineage in zip(manifest_records, lineage_rows)
    ]
    index_path = root / "materialization_index.jsonl"
    lineage_path = root / "audio_lineage.jsonl"
    qc_quarantine_path = root / "audio_qc_quarantine.jsonl"
    atomic_write(index_path, _jsonl_bytes(index_rows))
    atomic_write(lineage_path, _jsonl_bytes(lineage_rows))
    atomic_write(qc_quarantine_path, _jsonl_bytes(qc_quarantine_rows))
    return {
        "status": "pass",
        "audio_root": str(audio_root),
        "record_count": len(manifest_records),
        "proposal_record_count": len(proposal_rows),
        "qc_quarantine_count": len(qc_quarantine_rows),
        "qc_quarantine": str(qc_quarantine_path),
        "qc_quarantine_sha256": sha256_file(qc_quarantine_path),
        "materialization_index": str(index_path),
        "materialization_index_sha256": sha256_file(index_path),
        "lineage": str(lineage_path),
        "lineage_sha256": sha256_file(lineage_path),
        "proposal_sha256": proposal_receipt["proposal_sha256"],
        "config_sha256": proposal_receipt["config_sha256"],
        "acquisition_plan_sha256": acquisition["plan_sha256"],
        "support": {
            f"{split}|{language}|{label}": count
            for (split, language, label), count in sorted(support.items())
        },
        "manifest_records": manifest_records,
    }
