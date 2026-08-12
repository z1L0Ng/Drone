"""Metadata-only feasibility tooling for the multilingual three-class intake.

This module deliberately has no audio or network dependencies.  It reads pinned
local metadata, proposes non-canonical split assignments, and fails closed when
identity or provenance fields are missing.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List, Mapping, Optional, Sequence, Tuple


SCHEMA_VERSION = "talk-to-me-drone.multilingual-three-class-intake.v1"
INDEX_SCHEMA_VERSION = "talk-to-me-drone.metadata-index.v1"
REPORT_SCHEMA_VERSION = "talk-to-me-drone.metadata-feasibility-report.v1"
CANONICAL_CLASSES = ("emergency", "movement", "unknown")
SPLITS = ("train", "val", "test")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class ContractError(ValueError):
    """Raised when metadata cannot satisfy the fail-closed contract."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def canonical_json_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def load_json_yaml(path: Path) -> Dict[str, Any]:
    """Load JSON-compatible YAML without adding a PyYAML dependency."""

    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ContractError(
            f"{path} must remain JSON-compatible YAML: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise ContractError(f"{path} must contain a top-level object")
    return value


def _require(mapping: Mapping[str, Any], key: str, context: str) -> Any:
    if key not in mapping:
        raise ContractError(f"missing {context}.{key}")
    return mapping[key]


def normalize_surface(value: str) -> str:
    return unicodedata.normalize("NFC", value).strip().casefold()


def _validate_word_entry(entry: Mapping[str, Any], context: str) -> str:
    surface = _require(entry, "surface", context)
    if not isinstance(surface, str) or not surface.strip():
        raise ContractError(f"{context}.surface must be a non-empty string")
    for key in ("mapping_status", "semantic_risk", "native_review"):
        value = _require(entry, key, context)
        if not isinstance(value, str) or not value.strip():
            raise ContractError(f"{context}.{key} must be a non-empty string")
    return normalize_surface(surface)


def validate_config(config: Mapping[str, Any]) -> List[str]:
    """Validate the frozen contract and return unresolved receipt warnings."""

    if config.get("schema_version") != SCHEMA_VERSION:
        raise ContractError(f"schema_version must equal {SCHEMA_VERSION}")

    model = _require(config, "model_contract", "config")
    classes = tuple(_require(model, "canonical_classes", "model_contract"))
    if classes != CANONICAL_CLASSES or model.get("output_count") != 3:
        raise ContractError(
            "model_contract must freeze exactly emergency/movement/unknown and output_count=3"
        )
    if model.get("source_words_are_model_outputs") is not False:
        raise ContractError("source_words_are_model_outputs must be false")

    lexical = _require(config, "lexical_gate_policy", "config")
    if lexical.get("missing_native_reviewer_is_engineering_hard_no_go") is not False:
        raise ContractError("native reviewer absence must remain a deferred engineering risk")
    if lexical.get("paper_or_cross_language_semantic_claim_requires_future_native_review") is not True:
        raise ContractError("future native review must remain required for semantic claims")
    if set(lexical.get("approved_dictionary_backed_surfaces", [])) != {
        "es:alto:emergency",
        "de:halt:emergency",
        "de:los:movement",
    }:
        raise ContractError("dictionary-backed Management-provisional surfaces are not frozen")

    audio = _require(config, "future_audio_contract", "config")
    expected_audio = {
        "container": "WAV",
        "codec": "PCM",
        "sample_rate_hz": 16000,
        "channels": 1,
        "duration_seconds": 1.0,
        "sample_count": 16000,
    }
    for key, expected in expected_audio.items():
        if audio.get(key) != expected:
            raise ContractError(f"future_audio_contract.{key} must equal {expected!r}")

    split = _require(config, "split_policy", "config")
    if tuple(split.get("split_names", [])) != SPLITS:
        raise ContractError(f"split_policy.split_names must be {list(SPLITS)}")
    ratios = _require(split, "ratios", "split_policy")
    if set(ratios) != set(SPLITS):
        raise ContractError("split_policy.ratios must contain train/val/test only")
    if not math.isclose(sum(float(ratios[s]) for s in SPLITS), 1.0, abs_tol=1e-9):
        raise ContractError("split_policy.ratios must sum to 1")
    if not isinstance(split.get("seed"), int):
        raise ContractError("split_policy.seed must be an integer")
    if set(split.get("global_group_keys", [])) != {
        "speaker_id",
        "source_clip_family",
    }:
        raise ContractError(
            "split_policy.global_group_keys must contain speaker_id and source_clip_family"
        )

    sampling = _require(config, "sampling_policy", "config")
    if set(sampling.get("class_weights", {})) != set(CANONICAL_CLASSES):
        raise ContractError("sampling_policy.class_weights must cover exactly three classes")
    if not math.isclose(
        sum(float(v) for v in sampling["class_weights"].values()), 1.0, abs_tol=1e-9
    ):
        raise ContractError("sampling_policy.class_weights must sum to 1")
    cap = sampling.get("per_speaker_per_class_per_split_cap")
    if not isinstance(cap, int) or cap <= 0:
        raise ContractError("per-speaker cap must be a positive integer")

    execution = _require(config, "execution_policy", "config")
    forbidden = (
        "audio_download_authorized",
        "audio_transform_authorized",
        "canonical_split_authorized",
        "training_authorized",
        "evaluation_authorized",
    )
    if any(execution.get(field) is not False for field in forbidden):
        raise ContractError("all execution authorization fields must be false")

    downstream = _require(config, "downstream_hard_gates", "config")
    required_downstream = {
        "management_license_and_no_reidentification_acceptance",
        "gsc_immutable_archive_and_metadata_receipt",
        "audio_header_and_boundary_qc",
        "audio_download_authorization",
        "audio_transform_authorization",
        "canonical_split_authorization",
        "training_authorization",
        "evaluation_authorization",
    }
    if set(downstream) != required_downstream:
        raise ContractError("downstream_hard_gates fields do not match the frozen gate set")
    if any(not isinstance(value, bool) for value in downstream.values()):
        raise ContractError("downstream_hard_gates values must be booleans")

    datasets = _require(config, "datasets", "config")
    if not isinstance(datasets, dict) or not datasets:
        raise ContractError("config.datasets must be a non-empty object")

    seen_languages = set()
    unresolved: List[str] = []
    for dataset_key, dataset in datasets.items():
        context = f"datasets.{dataset_key}"
        for field in (
            "dataset_id",
            "version",
            "source_revision",
            "official_url",
            "license",
            "provenance",
            "languages",
        ):
            _require(dataset, field, context)
        receipt = _require(dataset, "receipt", context)
        if not isinstance(receipt, dict):
            raise ContractError(f"{context}.receipt must be an object")
        exact_receipts = [v for k, v in receipt.items() if k.endswith("sha256")]
        if not exact_receipts:
            raise ContractError(f"{context}.receipt must contain at least one sha256 field")
        for key, value in receipt.items():
            if key.endswith("sha256") and (not isinstance(value, str) or not HEX64.match(value)):
                unresolved.append(f"{context}.receipt.{key}={value!r}")

        languages = dataset["languages"]
        if not isinstance(languages, dict) or not languages:
            raise ContractError(f"{context}.languages must be a non-empty object")
        for language, lang_cfg in languages.items():
            seen_languages.add(language)
            lang_context = f"{context}.languages.{language}"
            mapping = _require(lang_cfg, "surface_mapping", lang_context)
            surface_roles: Dict[str, str] = {}
            for role in ("emergency", "movement", "protected"):
                entries = _require(mapping, role, f"{lang_context}.surface_mapping")
                if not isinstance(entries, list):
                    raise ContractError(f"{lang_context}.{role} must be a list")
                for index, entry in enumerate(entries):
                    if not isinstance(entry, dict):
                        raise ContractError(f"{lang_context}.{role}[{index}] must be an object")
                    normalized = _validate_word_entry(
                        entry, f"{lang_context}.surface_mapping.{role}[{index}]"
                    )
                    if normalized in surface_roles:
                        raise ContractError(
                            f"surface {normalized!r} appears in both {surface_roles[normalized]} and {role}"
                        )
                    surface_roles[normalized] = role

            unknown = _require(mapping, "unknown", f"{lang_context}.surface_mapping")
            if unknown.get("candidate_rule") not in {
                "allowlist_only",
                "inventory_complement_excluding_positive_and_protected",
            }:
                raise ContractError(f"unsupported unknown candidate rule in {lang_context}")
            approved = _require(unknown, "approved", f"{lang_context}.unknown")
            if not isinstance(approved, list):
                raise ContractError(f"{lang_context}.unknown.approved must be a list")
            for index, entry in enumerate(approved):
                normalized = _validate_word_entry(
                    entry, f"{lang_context}.surface_mapping.unknown.approved[{index}]"
                )
                if normalized in surface_roles:
                    raise ContractError(
                        f"surface {normalized!r} appears in both {surface_roles[normalized]} and unknown"
                    )
                surface_roles[normalized] = "unknown"
            if language in {"es", "de"}:
                if mapping.get("engineering_positive_candidates_admitted") is not True:
                    raise ContractError(f"{lang_context} positive engineering admission must be true")
                if unknown.get("candidate_rule") != "allowlist_only":
                    raise ContractError(f"{lang_context} must not use an inventory complement")
                if unknown.get("engineering_allowlist_admitted") is not True or not approved:
                    raise ContractError(f"{lang_context} requires a non-empty admitted unknown allowlist")

    if seen_languages != {"en", "es", "de"}:
        raise ContractError("frozen intake must contain exactly en, es, and de")
    return sorted(unresolved)


def validate_config_artifacts(config_path: Path, config: Mapping[str, Any]) -> Dict[str, Any]:
    """Verify the external approved-unknown allowlist against embedded mappings."""

    receipt = _require(config, "approved_unknown_inventory", "config")
    for field in ("path", "file_sha256", "canonical_tuple_sha256"):
        value = _require(receipt, field, "approved_unknown_inventory")
        if field.endswith("sha256") and (not isinstance(value, str) or not HEX64.match(value)):
            raise ContractError(f"approved_unknown_inventory.{field} must be an exact SHA-256")
    path = Path(receipt["path"])
    if not path.is_absolute():
        try:
            repo_root = config_path.resolve().parents[2]
        except IndexError as exc:
            raise ContractError("cannot resolve repository-relative inventory path") from exc
        path = repo_root / path
    if not path.is_file():
        raise ContractError(f"approved unknown inventory not found: {path}")
    actual_hash = sha256_file(path)
    if actual_hash != receipt["file_sha256"]:
        raise ContractError(
            f"approved unknown inventory checksum mismatch: expected {receipt['file_sha256']}, got {actual_hash}"
        )

    required = {
        "language",
        "surface",
        "train_samples",
        "dev_samples",
        "test_samples",
        "admission_status",
    }
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ContractError("approved unknown inventory is missing required columns")
        rows = list(reader)
    pairs = [(row["language"], normalize_surface(row["surface"])) for row in rows]
    if len(pairs) != len(set(pairs)):
        raise ContractError("approved unknown inventory contains duplicate language/surface rows")
    if set(language for language, _ in pairs) != {"es", "de"}:
        raise ContractError("approved unknown inventory must contain exactly es and de")
    for row in rows:
        if row["admission_status"] != "management_provisional_conservative_unknown":
            raise ContractError("unexpected unknown inventory admission status")
        for field in ("train_samples", "dev_samples", "test_samples"):
            try:
                value = int(row[field])
            except ValueError as exc:
                raise ContractError(f"approved unknown inventory {field} must be an integer") from exc
            if value <= 0:
                raise ContractError(f"approved unknown inventory {field} must be positive")

    canonical = "".join(
        f"{row['language']},{normalize_surface(row['surface'])},{row['train_samples']},{row['dev_samples']},{row['test_samples']}\n"
        for row in sorted(rows, key=lambda item: (item["language"], normalize_surface(item["surface"])))
    )
    tuple_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    if tuple_hash != receipt["canonical_tuple_sha256"]:
        raise ContractError("approved unknown inventory canonical tuple hash mismatch")

    embedded = set()
    for dataset in config["datasets"].values():
        for language, lang_cfg in dataset["languages"].items():
            if language not in {"es", "de"}:
                continue
            for entry in lang_cfg["surface_mapping"]["unknown"]["approved"]:
                embedded.add((language, normalize_surface(entry["surface"])))
    if embedded != set(pairs):
        raise ContractError("approved unknown inventory and embedded config allowlist disagree")
    return {
        "path": str(path),
        "file_sha256": actual_hash,
        "canonical_tuple_sha256": tuple_hash,
        "rows": len(rows),
        "expected_original_split_counts": {
            f"{row['language']}:{normalize_surface(row['surface'])}": {
                "train": int(row["train_samples"]),
                "dev": int(row["dev_samples"]),
                "test": int(row["test_samples"]),
            }
            for row in rows
        },
    }


def build_mapping_index(config: Mapping[str, Any]) -> Dict[Tuple[str, str], Dict[str, Any]]:
    result: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for dataset_key, dataset in config["datasets"].items():
        for language, lang_cfg in dataset["languages"].items():
            mapping = lang_cfg["surface_mapping"]
            indexed: Dict[str, Tuple[str, Mapping[str, Any]]] = {}
            for role in ("emergency", "movement", "protected"):
                for entry in mapping[role]:
                    indexed[normalize_surface(entry["surface"])] = (role, entry)
            for entry in mapping["unknown"]["approved"]:
                indexed[normalize_surface(entry["surface"])] = ("unknown", entry)
            result[(dataset_key, language)] = {
                "entries": indexed,
                "candidate_rule": mapping["unknown"]["candidate_rule"],
                "candidate_admitted": bool(mapping["unknown"].get("candidate_admitted", False)),
                "positive_engineering_admitted": bool(
                    mapping.get("engineering_positive_candidates_admitted", False)
                ),
                "unknown_allowlist_engineering_admitted": bool(
                    mapping["unknown"].get("engineering_allowlist_admitted", False)
                ),
            }
    return result


@dataclass(frozen=True)
class MetadataRecord:
    entry_id: str
    record_id: str
    dataset_key: str
    dataset_version: str
    language: str
    source_word: str
    speaker_id: str
    source_clip_family: str
    original_split: str
    metadata_source: str
    metadata_row: int


@dataclass(frozen=True)
class MappedRecord:
    record: MetadataRecord
    canonical_class: Optional[str]
    mapping_role: str
    mapping_status: str
    admitted: bool
    exclusion_reason: str = ""


def map_record(
    record: MetadataRecord,
    mapping_index: Mapping[Tuple[str, str], Mapping[str, Any]],
) -> MappedRecord:
    key = (record.dataset_key, record.language)
    if key not in mapping_index:
        raise ContractError(f"no surface mapping for {key}")
    lang_mapping = mapping_index[key]
    normalized = normalize_surface(record.source_word)
    entry = lang_mapping["entries"].get(normalized)
    if entry is not None:
        role, word_cfg = entry
        if role == "protected":
            return MappedRecord(
                record, None, "protected", word_cfg["mapping_status"], False, "protected_word"
            )
        admitted = word_cfg["native_review"] in {
            "native_approved",
            "not_applicable_english_anchor_current_policy",
        }
        if role in {"emergency", "movement"}:
            admitted = admitted or bool(lang_mapping["positive_engineering_admitted"])
        elif role == "unknown":
            admitted = admitted or bool(lang_mapping["unknown_allowlist_engineering_admitted"])
        return MappedRecord(
            record, role, role, word_cfg["mapping_status"], admitted
        )

    if lang_mapping["candidate_rule"] == "inventory_complement_excluding_positive_and_protected":
        return MappedRecord(
            record,
            "unknown",
            "unknown_candidate",
            "native_negative_review_required",
            bool(lang_mapping["candidate_admitted"]),
        )
    return MappedRecord(
        record, None, "unmapped", "not_in_allowlist", False, "unmapped_word"
    )


def _truthy(value: str) -> bool:
    return value.strip().casefold() in {"1", "true", "yes", "y"}


def _record_id(parts: Sequence[str]) -> str:
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def _iter_mswc_csv(entry: Mapping[str, Any], path: Path) -> Iterator[MetadataRecord]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"LINK", "WORD", "VALID", "SPEAKER"}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ContractError(f"{path} missing MSWC columns {sorted(required)}")
        for row_number, row in enumerate(reader, start=2):
            if not _truthy(row["VALID"]):
                continue
            word = row["WORD"].strip()
            speaker = row["SPEAKER"].strip()
            link = row["LINK"].strip()
            family = Path(link).name
            if not word or not speaker or not family:
                raise ContractError(
                    f"{path}:{row_number} missing WORD/SPEAKER/LINK; identity is fail-closed"
                )
            record_id = _record_id(
                [entry["entry_id"], str(row_number), family, word, speaker]
            )
            yield MetadataRecord(
                entry_id=entry["entry_id"],
                record_id=record_id,
                dataset_key=entry["dataset_key"],
                dataset_version=entry["dataset_version"],
                language=entry["language"],
                source_word=word,
                speaker_id=speaker,
                source_clip_family=family,
                original_split=entry["original_split"],
                metadata_source=str(path),
                metadata_row=row_number,
            )


def _iter_normalized_csv(entry: Mapping[str, Any], path: Path) -> Iterator[MetadataRecord]:
    required = {
        "source_record_id",
        "dataset_key",
        "dataset_version",
        "language",
        "source_word",
        "speaker_id",
        "source_clip_family",
        "original_split",
    }
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ContractError(f"{path} missing normalized columns {sorted(required)}")
        for row_number, row in enumerate(reader, start=2):
            for field in required:
                if not row[field].strip():
                    raise ContractError(
                        f"{path}:{row_number} missing {field}; provenance/identity is fail-closed"
                    )
            for fixed_field in ("dataset_key", "dataset_version", "language"):
                if row[fixed_field].strip() != str(entry[fixed_field]):
                    raise ContractError(
                        f"{path}:{row_number} {fixed_field} disagrees with metadata index"
                    )
            yield MetadataRecord(
                entry_id=entry["entry_id"],
                record_id=row["source_record_id"].strip(),
                dataset_key=row["dataset_key"].strip(),
                dataset_version=row["dataset_version"].strip(),
                language=row["language"].strip(),
                source_word=row["source_word"].strip(),
                speaker_id=row["speaker_id"].strip(),
                source_clip_family=row["source_clip_family"].strip(),
                original_split=row["original_split"].strip(),
                metadata_source=str(path),
                metadata_row=row_number,
            )


def iter_entry_records(entry: Mapping[str, Any]) -> Iterator[MetadataRecord]:
    path = Path(entry["resolved_path"])
    if entry["adapter"] == "mswc_csv":
        yield from _iter_mswc_csv(entry, path)
    elif entry["adapter"] == "normalized_csv":
        yield from _iter_normalized_csv(entry, path)
    else:
        raise ContractError(f"unsupported adapter {entry['adapter']!r}")


def load_metadata_index(
    index_path: Path, config: Mapping[str, Any]
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    index = load_json_yaml(index_path)
    if index.get("schema_version") != INDEX_SCHEMA_VERSION:
        raise ContractError(f"metadata index schema must equal {INDEX_SCHEMA_VERSION}")
    entries = index.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ContractError("metadata index must contain non-empty entries")

    required = {
        "entry_id",
        "adapter",
        "path",
        "sha256",
        "dataset_key",
        "dataset_version",
        "language",
        "original_split",
        "source_revision",
    }
    seen_ids = set()
    resolved: List[Dict[str, Any]] = []
    for position, raw_entry in enumerate(entries):
        if not isinstance(raw_entry, dict):
            raise ContractError(f"metadata index entry {position} must be an object")
        missing = sorted(required - set(raw_entry))
        if missing:
            raise ContractError(f"metadata index entry {position} missing {missing}")
        entry = dict(raw_entry)
        if entry["entry_id"] in seen_ids:
            raise ContractError(f"duplicate metadata entry_id {entry['entry_id']}")
        seen_ids.add(entry["entry_id"])
        if entry["adapter"] not in {"mswc_csv", "normalized_csv"}:
            raise ContractError(f"unsupported adapter {entry['adapter']!r}")
        if entry["original_split"] not in {"train", "dev", "test", "inventory"}:
            raise ContractError(f"invalid original_split {entry['original_split']!r}")
        if not isinstance(entry["sha256"], str) or not HEX64.match(entry["sha256"]):
            raise ContractError(f"entry {entry['entry_id']} requires an exact SHA-256")
        raw_path = str(entry["path"])
        if "://" in raw_path:
            raise ContractError("metadata paths must be local; network URLs are forbidden")
        path = Path(raw_path)
        if not path.is_absolute():
            path = (index_path.parent / path).resolve()
        if not path.is_file():
            raise ContractError(f"metadata file not found: {path}")
        actual_hash = sha256_file(path)
        if actual_hash != entry["sha256"]:
            raise ContractError(
                f"checksum mismatch for {entry['entry_id']}: expected {entry['sha256']}, got {actual_hash}"
            )
        dataset_key = entry["dataset_key"]
        if dataset_key not in config["datasets"]:
            raise ContractError(f"unknown dataset_key {dataset_key!r}")
        dataset = config["datasets"][dataset_key]
        if entry["dataset_version"] != dataset["version"]:
            raise ContractError(f"version mismatch for {entry['entry_id']}")
        if entry["source_revision"] != dataset["source_revision"]:
            raise ContractError(f"source revision mismatch for {entry['entry_id']}")
        if entry["language"] not in dataset["languages"]:
            raise ContractError(
                f"language {entry['language']!r} is not configured for {dataset_key}"
            )
        entry["resolved_path"] = str(path)
        entry["verified_sha256"] = actual_hash
        resolved.append(entry)
    resolved.sort(key=lambda e: e["entry_id"])
    return index, resolved


def validate_complete_unknown_counts(
    entries: Sequence[Mapping[str, Any]],
    observed: Mapping[Tuple[str, str, str], int],
    expected: Mapping[str, Mapping[str, int]],
) -> List[str]:
    """Verify allowlist counts only when an index declares complete MSWC splits."""

    coverage = defaultdict(set)
    for entry in entries:
        if entry.get("coverage") == "complete_split" and entry["dataset_key"] == "mswc":
            coverage[entry["language"]].add(entry["original_split"])
    verified_languages = sorted(
        language for language, splits in coverage.items() if splits == {"train", "dev", "test"}
    )
    mismatches = []
    for key, split_counts in expected.items():
        language, surface = key.split(":", 1)
        if language not in verified_languages:
            continue
        for split, expected_count in split_counts.items():
            actual = observed[(language, surface, split)]
            if actual != expected_count:
                mismatches.append(
                    f"approved_unknown_count_mismatch:{language}:{surface}:{split}:expected={expected_count}:actual={actual}"
                )
    if mismatches:
        raise ContractError("; ".join(mismatches))
    return verified_languages


class DisjointSet:
    def __init__(self) -> None:
        self.parent: Dict[str, str] = {}
        self.rank: Dict[str, int] = {}

    def add(self, item: str) -> None:
        if item not in self.parent:
            self.parent[item] = item
            self.rank[item] = 0

    def find(self, item: str) -> str:
        parent = self.parent[item]
        if parent != item:
            self.parent[item] = self.find(parent)
        return self.parent[item]

    def union(self, left: str, right: str) -> None:
        self.add(left)
        self.add(right)
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            return
        if self.rank[left_root] < self.rank[right_root]:
            left_root, right_root = right_root, left_root
        self.parent[right_root] = left_root
        if self.rank[left_root] == self.rank[right_root]:
            self.rank[left_root] += 1


def _identity_nodes(record: MetadataRecord) -> Tuple[str, str]:
    dataset = record.dataset_key
    return (
        f"speaker\x1f{dataset}\x1f{record.speaker_id}",
        f"family\x1f{dataset}\x1f{record.source_clip_family}",
    )


def _iter_mapped_records(
    entries: Sequence[Mapping[str, Any]],
    mapping_index: Mapping[Tuple[str, str], Mapping[str, Any]],
) -> Iterator[MappedRecord]:
    for entry in entries:
        for record in iter_entry_records(entry):
            yield map_record(record, mapping_index)


def _component_ids(dsu: DisjointSet) -> Dict[str, str]:
    members: Dict[str, List[str]] = defaultdict(list)
    for node in dsu.parent:
        members[dsu.find(node)].append(node)
    root_to_component = {}
    for root, values in members.items():
        digest = hashlib.sha256()
        for value in sorted(values):
            digest.update(value.encode("utf-8"))
            digest.update(b"\0")
        root_to_component[root] = digest.hexdigest()
    return {node: root_to_component[dsu.find(node)] for node in dsu.parent}


def _assign_components(
    profiles: Mapping[str, Counter], ratios: Mapping[str, float], seed: int
) -> Dict[str, str]:
    dimensions = sorted({dimension for counter in profiles.values() for dimension in counter})
    totals = Counter()
    for profile in profiles.values():
        totals.update(profile)
    targets = {
        split: {dimension: totals[dimension] * float(ratios[split]) for dimension in dimensions}
        for split in SPLITS
    }
    assigned = {split: Counter() for split in SPLITS}
    total_assigned = Counter()
    total_target = {
        split: sum(totals.values()) * float(ratios[split]) for split in SPLITS
    }

    order = sorted(
        profiles,
        key=lambda component: (
            -sum(profiles[component].values()),
            hashlib.sha256(f"{seed}:{component}".encode("utf-8")).hexdigest(),
        ),
    )
    result: Dict[str, str] = {}
    for component in order:
        profile = profiles[component]
        component_total = sum(profile.values())
        scores = []
        for split_index, split in enumerate(SPLITS):
            incremental = 0.0
            for dimension in dimensions:
                before = assigned[split][dimension] - targets[split][dimension]
                after = before + profile[dimension]
                incremental += (after * after - before * before) / (
                    targets[split][dimension] + 1.0
                )
            before_total = total_assigned[split] - total_target[split]
            after_total = before_total + component_total
            incremental += (after_total * after_total - before_total * before_total) / (
                total_target[split] + 1.0
            )
            scores.append((incremental, split_index, split))
        split = min(scores)[2]
        result[component] = split
        assigned[split].update(profile)
        total_assigned[split] += component_total
    return result


def _manifest_row(mapped: MappedRecord, component: str, split: str) -> List[str]:
    record = mapped.record
    return [
        record.record_id,
        record.dataset_key,
        record.dataset_version,
        record.language,
        record.source_word,
        mapped.canonical_class or "",
        mapped.mapping_role,
        mapped.mapping_status,
        "true" if mapped.admitted else "false",
        record.speaker_id,
        record.source_clip_family,
        component,
        split,
        record.original_split,
        record.entry_id,
        str(record.metadata_row),
    ]


MANIFEST_FIELDS = [
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
    "isolation_component_id",
    "proposed_split",
    "original_split",
    "metadata_entry_id",
    "metadata_row",
]


def _csv_line(values: Sequence[str]) -> bytes:
    buffer = io.StringIO(newline="")
    csv.writer(buffer, lineterminator="\n").writerow(values)
    return buffer.getvalue().encode("utf-8")


def run_feasibility(
    config_path: Path,
    metadata_index_path: Path,
    output_dir: Optional[Path] = None,
    write_proposal: bool = False,
) -> Dict[str, Any]:
    """Run a metadata-only, non-canonical split feasibility proposal."""

    config = load_json_yaml(config_path)
    unresolved_receipts = validate_config(config)
    unknown_inventory_receipt = validate_config_artifacts(config_path, config)
    index, entries = load_metadata_index(metadata_index_path, config)
    mapping_index = build_mapping_index(config)

    dsu = DisjointSet()
    excluded = Counter()
    included_rows = 0
    mapping_status_counts = Counter()
    observed_unknown_original_split_counts = Counter()
    seen_record_ids = set()
    for mapped in _iter_mapped_records(entries, mapping_index):
        if mapped.canonical_class is None:
            excluded[(mapped.record.language, mapped.mapping_role)] += 1
            continue
        identity = (mapped.record.dataset_key, mapped.record.record_id)
        if identity in seen_record_ids:
            raise ContractError(
                f"duplicate mapped source_record_id: {mapped.record.dataset_key}:{mapped.record.record_id}"
            )
        seen_record_ids.add(identity)
        speaker_node, family_node = _identity_nodes(mapped.record)
        dsu.union(speaker_node, family_node)
        included_rows += 1
        mapping_status_counts[(mapped.record.language, mapped.mapping_status)] += 1
        if mapped.canonical_class == "unknown":
            observed_unknown_original_split_counts[
                (
                    mapped.record.language,
                    normalize_surface(mapped.record.source_word),
                    mapped.record.original_split,
                )
            ] += 1
    if included_rows == 0:
        raise ContractError("no mapped metadata rows remain after exclusions")

    node_components = _component_ids(dsu)
    profiles: Dict[str, Counter] = defaultdict(Counter)
    for mapped in _iter_mapped_records(entries, mapping_index):
        if mapped.canonical_class is None:
            continue
        speaker_node, _ = _identity_nodes(mapped.record)
        component = node_components[speaker_node]
        profiles[component][(mapped.record.language, mapped.canonical_class)] += 1

    split_policy = config["split_policy"]
    component_split = _assign_components(
        profiles, split_policy["ratios"], split_policy["seed"]
    )
    unknown_count_verified_languages = validate_complete_unknown_counts(
        entries,
        observed_unknown_original_split_counts,
        unknown_inventory_receipt["expected_original_split_counts"],
    )

    output_handle = None
    output_path = None
    if write_proposal:
        if output_dir is None:
            raise ContractError("--write-proposal requires an output directory")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "metadata_split_proposal.csv"
        output_handle = output_path.open("w", encoding="utf-8", newline="")

    manifest_hash = hashlib.sha256()
    header_line = _csv_line(MANIFEST_FIELDS)
    manifest_hash.update(header_line)
    if output_handle is not None:
        output_handle.write(header_line.decode("utf-8"))

    samples = Counter()
    words: Dict[Tuple[str, str, str], Counter] = defaultdict(Counter)
    speakers: Dict[Tuple[str, str, str], set] = defaultdict(set)
    families: Dict[Tuple[str, str, str], set] = defaultdict(set)
    speaker_counts = Counter()
    non_admitted = Counter()
    identity_splits: Dict[str, set] = defaultdict(set)
    try:
        for mapped in _iter_mapped_records(entries, mapping_index):
            if mapped.canonical_class is None:
                continue
            speaker_node, family_node = _identity_nodes(mapped.record)
            component = node_components[speaker_node]
            proposed_split = component_split[component]
            key = (
                mapped.record.language,
                mapped.canonical_class,
                proposed_split,
            )
            samples[key] += 1
            words[key][mapped.record.source_word] += 1
            speakers[key].add(speaker_node)
            families[key].add(family_node)
            speaker_counts[(key, speaker_node)] += 1
            if not mapped.admitted:
                non_admitted[key] += 1
            identity_splits[speaker_node].add(proposed_split)
            identity_splits[family_node].add(proposed_split)

            row = _manifest_row(mapped, component, proposed_split)
            encoded = _csv_line(row)
            manifest_hash.update(encoded)
            if output_handle is not None:
                output_handle.write(encoded.decode("utf-8"))
    finally:
        if output_handle is not None:
            output_handle.close()

    speaker_overlap = sum(
        1 for node, split_set in identity_splits.items() if node.startswith("speaker\x1f") and len(split_set) > 1
    )
    family_overlap = sum(
        1 for node, split_set in identity_splits.items() if node.startswith("family\x1f") and len(split_set) > 1
    )
    if speaker_overlap or family_overlap:
        raise ContractError("internal error: identity overlap remains after component assignment")

    per_speaker_cap = config["sampling_policy"][
        "per_speaker_per_class_per_split_cap"
    ]
    post_cap = Counter()
    for (key, _speaker), count in speaker_counts.items():
        post_cap[key] += min(count, per_speaker_cap)

    languages = sorted(
        language
        for dataset in config["datasets"].values()
        for language in dataset["languages"]
    )
    support: Dict[str, Dict[str, Dict[str, Any]]] = {}
    shortages: List[str] = []
    for language in languages:
        support[language] = {}
        for canonical_class in CANONICAL_CLASSES:
            support[language][canonical_class] = {}
            for split in SPLITS:
                key = (language, canonical_class, split)
                count = samples[key]
                support[language][canonical_class][split] = {
                    "samples": count,
                    "unique_speakers": len(speakers[key]),
                    "unique_source_clip_families": len(families[key]),
                    "post_per_speaker_cap_samples": post_cap[key],
                    "not_admitted_samples": non_admitted[key],
                    "source_word_counts": dict(sorted(words[key].items())),
                }
                if count == 0:
                    shortages.append(f"zero_support:{language}:{canonical_class}:{split}")

    balance_ceiling = {
        language: {
            split: min(
                post_cap[(language, canonical_class, split)]
                for canonical_class in CANONICAL_CLASSES
            )
            for split in SPLITS
        }
        for language in languages
    }
    common_ceiling = {
        split: min(balance_ceiling[language][split] for language in languages)
        for split in SPLITS
    }

    review_blockers = []
    deferred_review_risks = []
    for dataset_key, dataset in config["datasets"].items():
        for language, lang_cfg in dataset["languages"].items():
            mapping = lang_cfg["surface_mapping"]
            for role in ("emergency", "movement"):
                for entry in mapping[role]:
                    if entry["native_review"] not in {
                        "native_approved",
                        "not_applicable_english_anchor_current_policy",
                    }:
                        deferred_review_risks.append(
                            f"future_native_review_required:{language}:{entry['surface']}:{role}"
                        )
                        if not mapping.get("engineering_positive_candidates_admitted", False):
                            review_blockers.append(
                                f"engineering_mapping_not_admitted:{language}:{entry['surface']}:{role}"
                            )
            if not mapping["unknown"]["approved"]:
                review_blockers.append(f"no_approved_unknown_inventory:{language}")

    downstream_gates = config["downstream_hard_gates"]
    downstream_blockers = sorted(
        f"downstream_gate_not_satisfied:{gate}"
        for gate, state in downstream_gates.items()
        if state is not True
    )
    no_go_reasons = sorted(
        set(unresolved_receipts + shortages + review_blockers + downstream_blockers)
    )
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "task_id": config.get("task_id"),
        "dry_run": not write_proposal,
        "canonical_split_created": False,
        "model_contract": {
            "canonical_classes": list(CANONICAL_CLASSES),
            "output_count": 3,
            "source_words_are_model_outputs": False,
        },
        "hashes": {
            "config_file_sha256": sha256_file(config_path),
            "config_canonical_sha256": canonical_json_sha256(config),
            "metadata_index_file_sha256": sha256_file(metadata_index_path),
            "metadata_index_canonical_sha256": canonical_json_sha256(index),
            "proposal_manifest_sha256": manifest_hash.hexdigest(),
        },
        "metadata_receipts": [
            {
                "entry_id": entry["entry_id"],
                "path": entry["resolved_path"],
                "sha256": entry["verified_sha256"],
                "dataset_key": entry["dataset_key"],
                "dataset_version": entry["dataset_version"],
                "source_revision": entry["source_revision"],
                "language": entry["language"],
                "original_split": entry["original_split"],
            }
            for entry in entries
        ],
        "approved_unknown_inventory_receipt": unknown_inventory_receipt,
        "approved_unknown_original_split_count_verified_languages": unknown_count_verified_languages,
        "counts": {
            "included_rows": included_rows,
            "isolation_components": len(profiles),
            "excluded_by_language_and_role": {
                f"{language}:{role}": count
                for (language, role), count in sorted(excluded.items())
            },
            "mapping_status": {
                f"{language}:{status}": count
                for (language, status), count in sorted(mapping_status_counts.items())
            },
        },
        "support": support,
        "balance_ceiling_after_per_speaker_cap": balance_ceiling,
        "common_language_class_ceiling_after_per_speaker_cap": common_ceiling,
        "overlap_assertions": {
            "speaker_overlap_across_proposed_splits": speaker_overlap,
            "source_clip_family_overlap_across_proposed_splits": family_overlap,
            "passed": speaker_overlap == 0 and family_overlap == 0,
        },
        "admission_status": "NO_GO" if no_go_reasons else "METADATA_FEASIBLE_NOT_AUTHORIZED",
        "lexical_engineering_gate_status": (
            "PASS_MANAGEMENT_PROVISIONAL" if not review_blockers else "NO_GO"
        ),
        "no_go_reasons": no_go_reasons,
        "deferred_review_risks": sorted(set(deferred_review_risks)),
        "proposal_manifest_path": str(output_path) if output_path else None,
    }

    if write_proposal and output_dir is not None:
        report_path = output_dir / "feasibility_report.json"
        with report_path.open("w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
    return report


def validate_report(report: Mapping[str, Any], config: Mapping[str, Any]) -> None:
    if report.get("schema_version") != REPORT_SCHEMA_VERSION:
        raise ContractError("unexpected feasibility report schema")
    if report.get("canonical_split_created") is not False:
        raise ContractError("report must not claim a canonical split")
    model = report.get("model_contract", {})
    if tuple(model.get("canonical_classes", [])) != CANONICAL_CLASSES:
        raise ContractError("report does not preserve the three-class schema")
    if model.get("output_count") != 3 or model.get("source_words_are_model_outputs") is not False:
        raise ContractError("report model contract is invalid")
    overlap = report.get("overlap_assertions", {})
    if overlap.get("speaker_overlap_across_proposed_splits") != 0:
        raise ContractError("speaker overlap assertion failed")
    if overlap.get("source_clip_family_overlap_across_proposed_splits") != 0:
        raise ContractError("source clip-family overlap assertion failed")
    if overlap.get("passed") is not True:
        raise ContractError("overlap assertions did not pass")
    expected_config_hash = canonical_json_sha256(config)
    if report.get("hashes", {}).get("config_canonical_sha256") != expected_config_hash:
        raise ContractError("report/config canonical hash mismatch")
    manifest_hash = report.get("hashes", {}).get("proposal_manifest_sha256", "")
    if not HEX64.match(manifest_hash):
        raise ContractError("proposal manifest SHA-256 is missing or invalid")
    manifest_path = report.get("proposal_manifest_path")
    if manifest_path:
        path = Path(manifest_path)
        if not path.is_file():
            raise ContractError("proposal manifest path does not exist")
        if sha256_file(path) != manifest_hash:
            raise ContractError("proposal manifest file/hash mismatch")
