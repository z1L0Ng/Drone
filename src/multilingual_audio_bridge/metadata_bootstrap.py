"""Deterministic official-source metadata bootstrap for DATA-20260812-03.

The default path is a pure plan.  Execution is guarded by the same explicit
download approval as acquisition because it reads acquired source trees and
writes immutable metadata receipts.  It never attempts speaker
re-identification: MSWC speaker identifiers are copied exactly as published.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sqlite3
import tempfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

from src.multilingual_three_class_intake import (
    INDEX_SCHEMA_VERSION,
    load_json_yaml,
    load_metadata_index,
    validate_config,
    validate_config_artifacts,
)

from .acquisition import APPROVAL_ENV, load_plan
from .contracts import (
    ACQUISITION_RECEIPT_SCHEMA,
    METADATA_BOOTSTRAP_RECEIPT_SCHEMA,
    BridgeError,
    atomic_json,
    canonical_json_bytes,
    require_sha256,
    sha256_file,
)


GSC_NORMALIZED_FIELDS = (
    "source_record_id",
    "dataset_key",
    "dataset_version",
    "language",
    "source_word",
    "speaker_id",
    "source_clip_family",
    "source_audio_relpath",
    "original_split",
    "source_revision",
    "raw_audio_sha256",
    "official_split_source",
)
GSC_FILENAME = re.compile(r"^(?P<speaker>.+)_nohash_(?P<utterance>[0-9]+)\.wav$")
MSWC_SPLITS = ("train", "dev", "test")


def _load_object(path: Path, context: str) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BridgeError(f"cannot load {context} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BridgeError(f"{context} must be a JSON object")
    return value


def _safe_relative(value: str, context: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if (
        not value
        or "\\" in value
        or path.is_absolute()
        or ".." in path.parts
        or "." in path.parts
    ):
        raise BridgeError(f"unsafe {context}: {value!r}")
    return path


def _acquisition_receipt(path: Path, plan_sha256: str) -> Dict[str, Any]:
    receipt = _load_object(path, "acquisition receipt")
    if receipt.get("schema_version") != ACQUISITION_RECEIPT_SCHEMA:
        raise BridgeError("unexpected acquisition receipt schema")
    if receipt.get("status") != "pass":
        raise BridgeError("metadata bootstrap requires a passing acquisition receipt")
    if receipt.get("plan_sha256") != plan_sha256:
        raise BridgeError("acquisition receipt/plan SHA-256 mismatch")
    if receipt.get("no_reidentification_performed") is not True:
        raise BridgeError("acquisition receipt must attest no re-identification")
    if receipt.get("redistribution_authorized") is not False:
        raise BridgeError("acquisition receipt must not authorize redistribution")
    return receipt


def _asset_rows(
    receipt: Mapping[str, Any],
    dataset_key: str,
    *,
    role: str | None = None,
    language: str | None = None,
) -> List[Mapping[str, Any]]:
    rows = []
    for asset in receipt.get("assets", []):
        if asset.get("dataset_key") != dataset_key:
            continue
        asset_role = asset.get("asset_role", "audio_archive")
        if role is not None and asset_role != role:
            continue
        if language is not None and asset.get("language") != language:
            continue
        destination = Path(str(asset.get("extraction", {}).get("destination", ""))).resolve()
        if not destination.is_dir():
            raise BridgeError(f"acquired source root missing: {destination}")
        require_sha256(
            asset.get("download", {}).get("archive_sha256"),
            f"{asset.get('asset_id')}.archive_sha256",
        )
        rows.append(asset)
    return sorted(rows, key=lambda row: str(row.get("asset_id")))


def _read_gsc_split_list(root: Path, name: str) -> set[str]:
    path = root / name
    if not path.is_file():
        raise BridgeError(f"GSC official split list missing: {path}")
    values: set[str] = set()
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        value = raw.strip()
        if not value:
            continue
        relative = _safe_relative(value, f"{name}:{line_number}")
        if len(relative.parts) != 2 or relative.suffix.casefold() != ".wav":
            raise BridgeError(f"invalid GSC split-list entry {name}:{line_number}: {value!r}")
        normalized = relative.as_posix()
        if normalized in values:
            raise BridgeError(f"duplicate GSC split-list entry: {normalized}")
        values.add(normalized)
    if not values:
        raise BridgeError(f"GSC split list is empty: {name}")
    return values


def _atomic_csv(path: Path, fieldnames: Sequence[str], rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        handle.flush()
    if path.exists():
        if sha256_file(path) != sha256_file(temporary):
            temporary.unlink(missing_ok=True)
            raise BridgeError(f"existing metadata artifact differs from deterministic output: {path}")
        temporary.unlink()
    else:
        temporary.replace(path)


def generate_gsc_normalized_csv(root: Path, output: Path) -> Dict[str, Any]:
    """Generate a complete, deterministic GSC archive inventory."""

    validation = _read_gsc_split_list(root, "validation_list.txt")
    testing = _read_gsc_split_list(root, "testing_list.txt")
    overlap = validation & testing
    if overlap:
        raise BridgeError(f"GSC official validation/testing lists overlap: {sorted(overlap)[:1]}")

    wav_paths = sorted(
        path
        for path in root.rglob("*.wav")
        if "_background_noise_" not in path.relative_to(root).parts
    )
    if not wav_paths:
        raise BridgeError("GSC extracted tree contains no command WAV files")
    archive_paths = {path.relative_to(root).as_posix() for path in wav_paths}
    missing_listed = sorted((validation | testing) - archive_paths)
    if missing_listed:
        raise BridgeError(f"GSC split list references missing audio: {missing_listed[0]}")

    counts: Counter[str] = Counter()
    speakers: set[str] = set()
    families: Counter[str] = Counter()
    seen_ids: set[str] = set()

    def rows() -> Iterable[Mapping[str, Any]]:
        for path in wav_paths:
            if path.is_symlink():
                raise BridgeError(f"GSC symlink is forbidden: {path}")
            relative = path.relative_to(root)
            if len(relative.parts) != 2:
                raise BridgeError(f"GSC command audio must be word/file.wav: {relative}")
            source_word, filename = relative.parts
            match = GSC_FILENAME.fullmatch(filename)
            if match is None:
                raise BridgeError(f"GSC filename lacks _nohash_ grouping: {relative}")
            speaker = match.group("speaker")
            raw_sha = sha256_file(path)
            family = f"gsc-raw-sha256:{raw_sha}"
            reltext = relative.as_posix()
            if reltext in validation:
                original_split = "dev"
                split_source = "validation_list.txt"
            elif reltext in testing:
                original_split = "test"
                split_source = "testing_list.txt"
            else:
                original_split = "train"
                split_source = "official_complement"
            record_id = hashlib.sha256(
                f"gsc_v2\x1fraw_v0.02\x1f{reltext}\x1f{raw_sha}".encode("utf-8")
            ).hexdigest()
            if record_id in seen_ids:
                raise BridgeError(f"duplicate GSC source_record_id: {record_id}")
            seen_ids.add(record_id)
            counts[original_split] += 1
            speakers.add(speaker)
            families[family] += 1
            yield {
                "source_record_id": record_id,
                "dataset_key": "gsc_v2",
                "dataset_version": "raw_v0.02",
                "language": "en",
                "source_word": source_word,
                "speaker_id": speaker,
                "source_clip_family": family,
                "source_audio_relpath": reltext,
                "original_split": original_split,
                "source_revision": "archive_etag_6b74f3901214cb2c2934e98196829835",
                "raw_audio_sha256": raw_sha,
                "official_split_source": split_source,
            }

    _atomic_csv(output, GSC_NORMALIZED_FIELDS, rows())
    duplicate_clusters = sum(1 for value in families.values() if value > 1)
    duplicate_files = sum(value for value in families.values() if value > 1)
    return {
        "path": str(output.resolve()),
        "sha256": sha256_file(output),
        "rows": sum(counts.values()),
        "official_split_counts": dict(sorted(counts.items())),
        "unique_speakers": len(speakers),
        "raw_sha256_family_count": len(families),
        "duplicate_raw_sha256_clusters": duplicate_clusters,
        "files_in_duplicate_clusters": duplicate_files,
        "speaker_rule": "filename prefix before _nohash_",
        "source_family_duplicate_rule": "exact raw WAV byte SHA-256",
    }


def _build_audio_suffix_index(audio_assets: Sequence[Mapping[str, Any]], database: Path) -> Dict[str, int]:
    connection = sqlite3.connect(database)
    try:
        connection.execute("CREATE TABLE audio (relpath TEXT PRIMARY KEY, count INTEGER NOT NULL)")
        scanned = 0
        malformed = 0
        for asset in audio_assets:
            root = Path(asset["extraction"]["destination"]).resolve()
            for path in root.rglob("*.wav"):
                if path.is_symlink():
                    raise BridgeError(f"MSWC audio symlink is forbidden: {path}")
                relative = PurePosixPath(path.relative_to(root).as_posix())
                if len(relative.parts) < 2:
                    malformed += 1
                    continue
                suffix = PurePosixPath(*relative.parts[-2:]).as_posix()
                connection.execute(
                    "INSERT INTO audio(relpath,count) VALUES(?,1) "
                    "ON CONFLICT(relpath) DO UPDATE SET count=count+1",
                    (suffix,),
                )
                scanned += 1
        connection.commit()
        if malformed:
            raise BridgeError(f"MSWC audio paths lack word/file structure: {malformed}")
        if scanned == 0:
            raise BridgeError("MSWC audio asset set contains no WAV files")
        unique = int(connection.execute("SELECT COUNT(*) FROM audio").fetchone()[0])
        duplicate_suffixes = int(
            connection.execute("SELECT COUNT(*) FROM audio WHERE count != 1").fetchone()[0]
        )
        if duplicate_suffixes:
            raise BridgeError(f"MSWC audio suffixes are not unique: {duplicate_suffixes}")
        return {"scanned_wav_files": scanned, "unique_audio_relpaths": unique}
    finally:
        connection.close()


def _mswc_expected_relpath(word: str, link: str) -> str:
    relative = _safe_relative(link, "MSWC LINK")
    if len(relative.parts) != 2 or relative.parts[0] != word:
        raise BridgeError(
            f"MSWC LINK/WORD path contract mismatch: WORD={word!r}, LINK={link!r}"
        )
    family = relative.name
    stem = Path(family).stem
    if not word or not stem:
        raise BridgeError("MSWC metadata has empty WORD/LINK")
    return f"{word}/{word}_{stem}.wav"


def validate_mswc_metadata_audio(
    language: str,
    metadata_root: Path,
    audio_assets: Sequence[Mapping[str, Any]],
    temporary_root: Path,
) -> Dict[str, Any]:
    """Validate all official VALID metadata rows against acquired WAV shards."""

    database = temporary_root / f"mswc-{language}-audio.sqlite3"
    audio_receipt = _build_audio_suffix_index(audio_assets, database)
    connection = sqlite3.connect(database)
    split_receipts: Dict[str, Any] = {}
    try:
        connection.execute("CREATE TABLE used (relpath TEXT PRIMARY KEY)")
        for split in MSWC_SPLITS:
            path = metadata_root / f"{split}.csv"
            if not path.is_file():
                raise BridgeError(f"MSWC {language} metadata split missing: {path}")
            counts: Counter[str] = Counter()
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                required = {"LINK", "WORD", "VALID", "SPEAKER"}
                if reader.fieldnames is None or not required.issubset(reader.fieldnames):
                    raise BridgeError(f"MSWC {language}/{split} missing official columns")
                for row_number, row in enumerate(reader, start=2):
                    counts["rows"] += 1
                    if row["VALID"].strip().casefold() not in {"1", "true", "yes", "y"}:
                        counts["invalid_rows"] += 1
                        continue
                    word = row["WORD"].strip()
                    speaker = row["SPEAKER"].strip()
                    if not speaker:
                        raise BridgeError(
                            f"MSWC {language}/{split}:{row_number} missing published speaker ID"
                        )
                    relative = _mswc_expected_relpath(word, row["LINK"].strip())
                    match = connection.execute(
                        "SELECT count FROM audio WHERE relpath=?", (relative,)
                    ).fetchone()
                    if match is None or int(match[0]) != 1:
                        raise BridgeError(
                            f"MSWC {language}/{split}:{row_number} audio locator must resolve once: "
                            f"{relative}"
                        )
                    try:
                        connection.execute("INSERT INTO used(relpath) VALUES(?)", (relative,))
                    except sqlite3.IntegrityError as exc:
                        raise BridgeError(
                            f"MSWC audio locator appears more than once across split CSVs: {relative}"
                        ) from exc
                    counts["valid_rows"] += 1
            split_receipts[split] = {
                "path": str(path.resolve()),
                "sha256": sha256_file(path),
                **dict(sorted(counts.items())),
            }
        connection.commit()
        used_count = int(connection.execute("SELECT COUNT(*) FROM used").fetchone()[0])
    finally:
        connection.close()
        database.unlink(missing_ok=True)
    return {
        "language": language,
        "speaker_policy": "copy official SPEAKER field; no inference or re-identification",
        "source_family_policy": "official LINK source clip family",
        "audio_relpath_policy": "WORD/WORD_<LINK basename without extension>.wav",
        "audio": audio_receipt,
        "splits": split_receipts,
        "validated_unique_audio_rows": used_count,
    }


def _relative_from_index(index_path: Path, target: Path) -> str:
    return os.path.relpath(target.resolve(), start=index_path.parent.resolve())


def _emit_metadata_index(
    path: Path,
    gsc_receipt: Mapping[str, Any],
    mswc_receipts: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    entries: List[Dict[str, Any]] = [
        {
            "entry_id": "gsc-v2-complete-archive",
            "adapter": "normalized_csv",
            "path": _relative_from_index(path, Path(str(gsc_receipt["path"]))),
            "sha256": gsc_receipt["sha256"],
            "dataset_key": "gsc_v2",
            "dataset_version": "raw_v0.02",
            "language": "en",
            "original_split": "inventory",
            "coverage": "complete_archive_with_official_row_split",
            "source_revision": "archive_etag_6b74f3901214cb2c2934e98196829835",
        }
    ]
    receipt_by_language = {str(item["language"]): item for item in mswc_receipts}
    for language in ("es", "de"):
        receipt = receipt_by_language[language]
        for split in MSWC_SPLITS:
            split_receipt = receipt["splits"][split]
            entries.append(
                {
                    "entry_id": f"mswc-{language}-{split}",
                    "adapter": "mswc_csv",
                    "path": _relative_from_index(path, Path(split_receipt["path"])),
                    "sha256": split_receipt["sha256"],
                    "dataset_key": "mswc",
                    "dataset_version": "1.0",
                    "language": language,
                    "original_split": split,
                    "coverage": "complete_split",
                    "source_revision": "0bc9df68e92fd6bb54176bf7eb29e2b9e97cb218",
                }
            )
    value = {
        "schema_version": INDEX_SCHEMA_VERSION,
        "producer": "src.multilingual_audio_bridge.metadata_bootstrap",
        "entries": entries,
    }
    payload = canonical_json_bytes(value) + b"\n"
    if path.exists():
        if path.read_bytes() != payload:
            raise BridgeError(f"existing metadata index differs from deterministic output: {path}")
    else:
        atomic_json(path, value)
    return value


def bootstrap_plan(
    plan_path: str | Path,
    config_path: str | Path,
    acquisition_receipt_path: str | Path,
    root: str | Path,
) -> Dict[str, Any]:
    output_root = Path(root).resolve()
    load_plan(plan_path)
    config = load_json_yaml(Path(config_path))
    unresolved = validate_config(config)
    validate_config_artifacts(Path(config_path), config)
    return {
        "mode": "dry-run",
        "network_performed": False,
        "writes_performed": False,
        "audio_transformed": False,
        "config_unresolved_receipts": unresolved,
        "speaker_reidentification_performed": False,
        "execution_guard": {"cli": "--execute", "environment": f"{APPROVAL_ENV}=YES"},
        "inputs": {
            "plan": str(Path(plan_path).resolve()),
            "config": str(Path(config_path).resolve()),
            "acquisition_receipt": str(Path(acquisition_receipt_path).resolve()),
        },
        "outputs": {
            "gsc_normalized_csv": str(output_root / "intake" / "gsc_v2_normalized.csv"),
            "metadata_index": str(output_root / "intake" / "metadata_index.json"),
            "receipt": str(output_root / "receipts" / "S1_metadata_bootstrap.json"),
        },
    }


def _verify_resumable_receipt(
    path: Path, input_hashes: Mapping[str, str]
) -> Dict[str, Any] | None:
    if not path.is_file():
        return None
    receipt = _load_object(path, "metadata bootstrap receipt")
    if (
        receipt.get("schema_version") != METADATA_BOOTSTRAP_RECEIPT_SCHEMA
        or receipt.get("status") != "pass"
        or receipt.get("input_hashes") != dict(input_hashes)
    ):
        raise BridgeError("existing metadata bootstrap receipt does not match current inputs")
    for artifact_path, expected in receipt.get("artifacts", {}).items():
        candidate = Path(artifact_path)
        if not candidate.is_file() or sha256_file(candidate) != expected:
            raise BridgeError(f"metadata bootstrap artifact no longer verifies: {candidate}")
    return {**receipt, "resumed": True}


def bootstrap_metadata(
    plan_path: str | Path,
    config_path: str | Path,
    acquisition_receipt_path: str | Path,
    root: str | Path,
    *,
    execute: bool = False,
    fixture_only: bool = False,
) -> Dict[str, Any]:
    """Generate GSC metadata, validate MSWC metadata/audio, and emit the index."""

    if not execute:
        return bootstrap_plan(plan_path, config_path, acquisition_receipt_path, root)
    if os.environ.get(APPROVAL_ENV) != "YES":
        raise BridgeError(f"metadata bootstrap requires --execute and {APPROVAL_ENV}=YES")

    output_root = Path(root).resolve()
    plan_hash = sha256_file(plan_path)
    config_hash = sha256_file(config_path)
    acquisition_path = Path(acquisition_receipt_path).resolve()
    acquisition_hash = sha256_file(acquisition_path)
    receipt = _acquisition_receipt(acquisition_path, plan_hash)
    input_hashes = {
        "plan_sha256": plan_hash,
        "config_sha256": config_hash,
        "acquisition_receipt_sha256": acquisition_hash,
        "fixture_only": "true" if fixture_only else "false",
    }
    receipt_path = output_root / "receipts" / "S1_metadata_bootstrap.json"
    resumed = _verify_resumable_receipt(receipt_path, input_hashes)
    if resumed is not None:
        return resumed

    config = load_json_yaml(Path(config_path))
    validate_config(config)
    validate_config_artifacts(Path(config_path), config)
    gsc_assets = _asset_rows(receipt, "gsc_v2", role="audio_archive")
    if len(gsc_assets) != 1:
        raise BridgeError(f"metadata bootstrap requires one GSC archive root, got {len(gsc_assets)}")
    gsc_root = Path(gsc_assets[0]["extraction"]["destination"]).resolve()
    intake_root = output_root / "intake"
    gsc_csv = intake_root / "gsc_v2_normalized.csv"
    gsc_receipt = generate_gsc_normalized_csv(gsc_root, gsc_csv)
    expected_gsc_rows = int(config["datasets"]["gsc_v2"]["receipt"]["paper_inventory_total"])
    if not fixture_only and gsc_receipt["rows"] != expected_gsc_rows:
        raise BridgeError(
            f"GSC complete-archive row count mismatch: {gsc_receipt['rows']} != "
            f"{expected_gsc_rows}"
        )

    mswc_receipts: List[Dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="drone-mswc-bootstrap-") as temporary:
        temporary_root = Path(temporary)
        for language in ("es", "de"):
            metadata_assets = _asset_rows(
                receipt, "mswc", role="split_metadata", language=language
            )
            audio_assets = _asset_rows(receipt, "mswc", role="audio_archive", language=language)
            if len(metadata_assets) != 1:
                raise BridgeError(
                    f"metadata bootstrap requires one MSWC {language} split archive"
                )
            if not audio_assets:
                raise BridgeError(f"metadata bootstrap requires MSWC {language} WAV assets")
            metadata_root = Path(metadata_assets[0]["extraction"]["destination"]).resolve()
            mswc_receipts.append(
                validate_mswc_metadata_audio(
                    language, metadata_root, audio_assets, temporary_root
                )
            )

    index_path = intake_root / "metadata_index.json"
    index_value = _emit_metadata_index(index_path, gsc_receipt, mswc_receipts)
    _, verified_entries = load_metadata_index(index_path, config)
    artifacts = {
        str(gsc_csv.resolve()): sha256_file(gsc_csv),
        str(index_path.resolve()): sha256_file(index_path),
    }
    for language_receipt in mswc_receipts:
        for split_receipt in language_receipt["splits"].values():
            artifacts[str(Path(split_receipt["path"]).resolve())] = split_receipt["sha256"]
    result = {
        "schema_version": METADATA_BOOTSTRAP_RECEIPT_SCHEMA,
        "owner": "dataset",
        "status": "pass",
        "resumed": False,
        "input_hashes": input_hashes,
        "metadata_index": str(index_path.resolve()),
        "metadata_index_sha256": sha256_file(index_path),
        "metadata_index_entry_count": len(verified_entries),
        "metadata_index_schema": index_value["schema_version"],
        "gsc": gsc_receipt,
        "mswc": mswc_receipts,
        "no_reidentification_performed": True,
        "audio_transformed": False,
        "fixture_only": fixture_only,
        "artifacts": dict(sorted(artifacts.items())),
    }
    atomic_json(receipt_path, result)
    return result
