"""Versioned JSON configuration loading and parity validation."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

from .contracts import CONFIG_SCHEMA, LABELS, LANGUAGES, WEEKLY_OUTPUT_PREFIX


class ConfigError(ValueError):
    """Raised when a run configuration violates the clean-slate contract."""


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def deep_merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = copy.deepcopy(dict(base))
    for key, value in override.items():
        if key == "extends":
            continue
        if isinstance(value, Mapping) and isinstance(result.get(key), Mapping):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


@dataclass(frozen=True)
class LoadedConfig:
    path: Path
    effective: Dict[str, Any]
    effective_sha256: str
    source_sha256: Dict[str, str]


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"cannot load config {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ConfigError(f"config must be a JSON object: {path}")
    return value


def load_config(path: str | Path) -> LoadedConfig:
    lane_path = Path(path).resolve()
    lane = _load_json(lane_path)
    sources = {str(lane_path): sha256_file(lane_path)}
    if "extends" in lane:
        common_path = (lane_path.parent / str(lane["extends"])).resolve()
        common = _load_json(common_path)
        if "extends" in common:
            raise ConfigError("nested config inheritance is not supported")
        sources[str(common_path)] = sha256_file(common_path)
        effective = deep_merge(common, lane)
    else:
        effective = copy.deepcopy(lane)
    validate_config(effective)
    return LoadedConfig(
        path=lane_path,
        effective=effective,
        effective_sha256=sha256_bytes(canonical_json_bytes(effective)),
        source_sha256=sources,
    )


def _require(mapping: Mapping[str, Any], dotted: str) -> Any:
    current: Any = mapping
    for part in dotted.split("."):
        if not isinstance(current, Mapping) or part not in current:
            raise ConfigError(f"missing required config field: {dotted}")
        current = current[part]
    return current


def validate_config(config: Mapping[str, Any]) -> None:
    if config.get("schema_version") != CONFIG_SCHEMA:
        raise ConfigError(f"schema_version must be {CONFIG_SCHEMA}")
    if tuple(config.get("labels", ())) != LABELS:
        raise ConfigError(f"labels must be the shared ordered encoder {list(LABELS)}")

    lane_id = str(_require(config, "lane.lane_id"))
    language_fields = (
        "train_languages",
        "selection_languages",
        "calibration_languages",
        "evaluation_languages",
    )
    language_sets = {}
    for field in language_fields:
        languages = tuple(_require(config, f"lane.{field}"))
        if not languages or any(language not in LANGUAGES for language in languages):
            raise ConfigError(f"invalid lane {field} for {lane_id}: {languages}")
        if len(set(languages)) != len(languages):
            raise ConfigError(f"lane.{field} contains duplicates")
        language_sets[field] = languages
    if not set(language_sets["selection_languages"]).issubset(language_sets["train_languages"]):
        raise ConfigError("selection_languages must be a subset of train_languages")
    if not set(language_sets["calibration_languages"]).issubset(language_sets["train_languages"]):
        raise ConfigError("calibration_languages must be a subset of train_languages")
    if tuple(language_sets["evaluation_languages"]) != LANGUAGES:
        raise ConfigError("all comparison lanes must evaluate on the ordered EN/ES/DE test languages")
    if _require(config, "lane.source_word_role") != "provenance_and_sampling_only":
        raise ConfigError("source_word may only be provenance_and_sampling_only")

    audio = _require(config, "audio")
    if audio.get("sample_rate_hz") != 16000 or audio.get("num_samples") != 16000:
        raise ConfigError("audio contract must be exact mono PCM 16 kHz / 16000 samples")
    if audio.get("channels") != 1 or audio.get("duration_seconds") != 1.0:
        raise ConfigError("audio contract must be exact mono PCM 1.0 s")

    frontend = _require(config, "frontend")
    required_frontend = {
        "type": "logmel",
        "n_fft": 1024,
        "hop_length": 512,
        "center": False,
        "n_mels": 256,
        "fmin_hz": 50.0,
        "fmax_hz": None,
        "power": 2.0,
        "top_db": 80.0,
        "max_frames": 32,
        "normalization": "per_example_power_to_db_ref_max",
        "pad_value_db": 0.0,
    }
    for key, expected in required_frontend.items():
        if frontend.get(key) != expected:
            raise ConfigError(f"frontend.{key} must be {expected!r}, got {frontend.get(key)!r}")

    model = _require(config, "model")
    if model.get("input_shape") != [256, 32, 1]:
        raise ConfigError("model.input_shape must be [256, 32, 1]")
    if model.get("num_classes") != 3 or model.get("output_activation") != "softmax":
        raise ConfigError("model must have one shared 3-class softmax head")
    if model.get("initialization") != "fresh_random":
        raise ConfigError("primary lanes must use fresh_random initialization")
    if model.get("checkpoint_input") is not None:
        raise ConfigError("legacy/warm-start checkpoint_input is forbidden")
    for head in ("language_head", "word_head", "hierarchical_head"):
        if model.get(head) is not False:
            raise ConfigError(f"model.{head} must be false")
    if _require(config, "training.teacher_student") != "not_in_primary_comparison":
        raise ConfigError("teacher/student must remain outside the primary clean-slate comparison")
    if config["dataset"].get("legacy_npz_allowed") is not False:
        raise ConfigError("legacy data_paths.npz input must be disabled")
    if config["dataset"].get("file_level_random_split_allowed") is not False:
        raise ConfigError("file-level random splitting must be disabled")

    output_root = str(_require(config, "paths.output_root")).rstrip("/")
    if output_root != WEEKLY_OUTPUT_PREFIX:
        raise ConfigError(f"paths.output_root must be {WEEKLY_OUTPUT_PREFIX}")
    run_name = str(_require(config, "lane.run_name"))
    if not run_name or "/" in run_name or run_name in {".", ".."}:
        raise ConfigError("lane.run_name must be one safe path component")

    if _require(config, "noise.mode") != "disabled_clean_primary":
        raise ConfigError("v0 primary comparison freezes noise.mode=disabled_clean_primary")
    if config["noise"].get("snr_db_levels") not in (None, []):
        raise ConfigError("v0 must not inherit or freeze numeric SNR levels")

    selection = _require(config, "selection")
    if selection.get("dataset") != "validation_selection":
        raise ConfigError("checkpoint selection must use validation_selection only")
    if _require(config, "calibration.dataset") != "validation_calibration":
        raise ConfigError("calibration must use validation_calibration only")
    if _require(config, "evaluation.dataset") != "test":
        raise ConfigError("final evaluation dataset must be test")


def parity_contract(config: Mapping[str, Any]) -> Dict[str, Any]:
    """Return fields that must be identical across the three comparison lanes."""

    keys: Iterable[str] = (
        "labels",
        "audio",
        "frontend",
        "model",
        "training",
        "selection",
        "calibration",
        "evaluation",
        "metrics",
        "noise",
    )
    return {key: copy.deepcopy(config[key]) for key in keys}


def parity_contract_sha256(config: Mapping[str, Any]) -> str:
    return sha256_bytes(canonical_json_bytes(parity_contract(config)))
