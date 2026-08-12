"""Safe preflight, synthetic dry-run, and guarded future training entrypoint."""

from __future__ import annotations

import json
import os
import random
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple

import numpy as np

from .config import (
    LoadedConfig,
    canonical_json_bytes,
    load_config,
    parity_contract_sha256,
    sha256_bytes,
    sha256_file,
)
from .contracts import (
    ABORT_RECEIPT_SCHEMA,
    COMPLETION_RECEIPT_SCHEMA,
    LABELS,
    LABEL_TO_INDEX,
    PREDICTION_SCHEMA,
    START_RECEIPT_SCHEMA,
    WEEKLY_OUTPUT_PREFIX,
)
from .frontend import (
    extract_logmel_input,
    frontend_contract_sha256,
    load_exact_mono_pcm,
    tensor_sha256,
)
from .manifest import FrozenManifest, ManifestError, load_frozen_manifest, resolve_audio_path
from .metrics import compute_metrics, fit_temperature, temperature_scale
from .receipts import git_identity, hash_inventory, runtime_environment, utc_now, write_json, write_jsonl
from .sampler import derive_seed, epoch_indices


class RunError(RuntimeError):
    """Raised when a run cannot satisfy its execution contract."""


@dataclass(frozen=True)
class RunContext:
    repo_root: Path
    loaded_config: LoadedConfig
    config: Mapping[str, Any]
    manifest: FrozenManifest
    audio_root: Path
    output_dir: Path | None
    seed_id: int


def _source_hashes(repo_root: Path) -> Dict[str, str]:
    package_paths = sorted(
        path.relative_to(repo_root).as_posix()
        for path in (repo_root / "src/multilingual_retraining").glob("*.py")
    )
    paths = tuple(package_paths) + (
        "scripts/run_multilingual_retraining_2026w33.py",
        "src/model.py",
        "src/model_config.py",
    )
    return {path: sha256_file(repo_root / path) for path in paths}


def _model_contract(config: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "builder": config["model"]["builder"],
        "profile": config["model"]["profile"],
        "input_shape": config["model"]["input_shape"],
        "num_classes": config["model"]["num_classes"],
        "output_activation": config["model"]["output_activation"],
        "initialization": config["model"]["initialization"],
        "checkpoint_input": config["model"]["checkpoint_input"],
        "label_order": list(LABELS),
    }


def _noise_contract(config: Mapping[str, Any]) -> Dict[str, Any]:
    return dict(config["noise"])


def _seed_bundle(config: Mapping[str, Any], seed_id: int) -> Dict[str, int]:
    protocol = config["protocol_id"]
    lane = config["lane"]["lane_id"]
    return {
        component: derive_seed(protocol, lane, seed_id, component)
        for component in ("python", "numpy", "tensorflow", "train_order", "augmentation", "selection_eval")
    }


def build_context(
    repo_root: str | Path,
    config_path: str | Path,
    manifest_path: str | Path,
    validation_receipt_path: str | Path,
    audio_root: str | Path,
    output_dir: str | Path | None,
    seed_id: int,
) -> RunContext:
    root = Path(repo_root).resolve()
    loaded = load_config(config_path)
    config = loaded.effective
    accessible_languages = tuple(
        dict.fromkeys(
            language
            for field in (
                "train_languages",
                "selection_languages",
                "calibration_languages",
                "evaluation_languages",
            )
            for language in config["lane"][field]
        )
    )
    manifest = load_frozen_manifest(
        manifest_path,
        validation_receipt_path,
        selected_languages=accessible_languages,
        expected_manifest_languages=config["dataset"]["manifest_languages"],
    )
    if seed_id not in config["training"]["seed_ids"]:
        raise RunError(f"seed_id {seed_id} is outside the frozen seed_ids")
    target = None if output_dir is None else Path(output_dir).resolve()
    return RunContext(
        repo_root=root,
        loaded_config=loaded,
        config=config,
        manifest=manifest,
        audio_root=Path(audio_root).resolve(),
        output_dir=target,
        seed_id=seed_id,
    )


def stage_records(context: RunContext, split: str, language_field: str) -> Tuple[Mapping[str, Any], ...]:
    languages = set(context.config["lane"][language_field])
    return tuple(
        record
        for record in context.manifest.records
        if record["split"] == split and record["language"] in languages
    )


def validate_lane_dataset_contract(context: RunContext) -> None:
    mapping = context.config["dataset"]["language_source_contract"]
    for record in context.manifest.records:
        if context.manifest.fixture_only and str(record["source_dataset"]).startswith("synthetic_fixture"):
            continue
        allowed_sources = mapping.get(record["language"], [])
        if record["source_dataset"] not in allowed_sources:
            raise RunError(
                f"{record['sample_id']}: source_dataset={record['source_dataset']!r} is invalid "
                f"for language={record['language']!r}"
            )
    missing_cells = []
    stage_contracts = (
        ("train", "train_languages"),
        ("validation_selection", "selection_languages"),
        ("validation_calibration", "calibration_languages"),
        ("test", "evaluation_languages"),
    )
    for split, language_field in stage_contracts:
        for language in context.config["lane"][language_field]:
            for label in LABELS:
                if not any(
                    record["split"] == split
                    and record["language"] == language
                    and record["label"] == label
                    for record in context.manifest.records
                ):
                    missing_cells.append((split, language, label))
    if missing_cells:
        raise RunError(f"lane manifest is missing split/language/class cells: {missing_cells}")
    if context.config["lane"]["sampler"] == "language_class_word_speaker_balanced":
        training_records = stage_records(context, "train", "train_languages")
        epoch_indices(
            training_records,
            mode=context.config["lane"]["sampler"],
            languages=context.config["lane"]["train_languages"],
            labels=LABELS,
            epoch_size=max(
                len(training_records),
                len(context.config["lane"]["train_languages"]) * len(LABELS),
            ),
            seed=_seed_bundle(context.config, context.seed_id)["train_order"],
        )


def verify_audio_files(
    context: RunContext,
    records: Sequence[Mapping[str, Any]],
) -> Dict[str, str]:
    decoded: Dict[str, str] = {}
    for record in records:
        path = resolve_audio_path(context.audio_root, record)
        waveform = load_exact_mono_pcm(path, expected_sha256=record["audio_sha256"])
        pcm_hash = sha256_bytes(np.ascontiguousarray(waveform.astype("<f4")).tobytes())
        if pcm_hash != record["decoded_pcm_sha256"]:
            raise RunError(f"decoded PCM SHA-256 mismatch: {record['sample_id']}")
        decoded[str(record["sample_id"])] = pcm_hash
    return decoded


def preflight_summary(context: RunContext, verify_audio: bool) -> Dict[str, Any]:
    validate_lane_dataset_contract(context)
    development_records = tuple(
        list(stage_records(context, "train", "train_languages"))
        + list(stage_records(context, "validation_selection", "selection_languages"))
        + list(stage_records(context, "validation_calibration", "calibration_languages"))
    )
    audio_hashes = verify_audio_files(context, development_records) if verify_audio else {}
    return {
        "status": "pass",
        "mode": "preflight",
        "lane_id": context.config["lane"]["lane_id"],
        "stage_languages": {
            field: list(context.config["lane"][field])
            for field in (
                "train_languages",
                "selection_languages",
                "calibration_languages",
                "evaluation_languages",
            )
        },
        "accessible_languages": list(context.manifest.selected_languages),
        "manifest_languages": list(context.manifest.manifest_languages),
        "selected_record_count": len(context.manifest.records),
        "full_manifest_record_count": context.manifest.full_record_count,
        "support": context.manifest.support(),
        "manifest_sha256": context.manifest.sha256,
        "split_sha256": context.manifest.split_sha256,
        "config_sha256": context.loaded_config.effective_sha256,
        "parity_contract_sha256": parity_contract_sha256(context.config),
        "frontend_contract_sha256": frontend_contract_sha256(context.config["frontend"]),
        "model_contract_sha256": sha256_bytes(canonical_json_bytes(_model_contract(context.config))),
        "noise_contract_sha256": sha256_bytes(canonical_json_bytes(_noise_contract(context.config))),
        "verified_development_audio_count": len(audio_hashes),
        "test_audio_opened": False,
    }


def _base_receipt(context: RunContext, mode: str) -> Dict[str, Any]:
    return {
        "mode": mode,
        "protocol_id": context.config["protocol_id"],
        "config_version": context.config["config_version"],
        "lane_id": context.config["lane"]["lane_id"],
        "run_name": context.config["lane"]["run_name"],
        "seed_id": context.seed_id,
        "seed_bundle": _seed_bundle(context.config, context.seed_id),
        "label_order": list(LABELS),
        "git": git_identity(context.repo_root),
        "argv": list(sys.argv),
        "environment": runtime_environment(context.repo_root),
        "hashes": {
            "effective_config_sha256": context.loaded_config.effective_sha256,
            "config_source_sha256": context.loaded_config.source_sha256,
            "manifest_sha256": context.manifest.sha256,
            "manifest_validation_receipt_sha256": context.manifest.validation_receipt_sha256,
            "split_sha256": context.manifest.split_sha256,
            "frontend_contract_sha256": frontend_contract_sha256(context.config["frontend"]),
            "noise_contract_sha256": sha256_bytes(canonical_json_bytes(_noise_contract(context.config))),
            "model_contract_sha256": sha256_bytes(canonical_json_bytes(_model_contract(context.config))),
            "parity_contract_sha256": parity_contract_sha256(context.config),
            "source_sha256": _source_hashes(context.repo_root),
        },
        "support": context.manifest.support(),
    }


def run_synthetic_dry_run(context: RunContext) -> Dict[str, Any]:
    if context.output_dir is None:
        raise RunError("dry-run requires --output-dir")
    if not context.manifest.fixture_only:
        raise RunError("dry-run is restricted to a Dataset-owner receipt with fixture_only=true")
    validate_lane_dataset_contract(context)
    output = context.output_dir
    output.mkdir(parents=True, exist_ok=False)
    start = _base_receipt(context, "synthetic_dry_run")
    start.update({"schema_version": START_RECEIPT_SCHEMA, "status": "started", "started_at": utc_now()})
    write_json(output / "start_receipt.json", start)

    try:
        verified_pcm = verify_audio_files(context, context.manifest.records)
        feature_rows: List[Mapping[str, Any]] = []
        for record in context.manifest.records:
            path = resolve_audio_path(context.audio_root, record)
            waveform = load_exact_mono_pcm(path, expected_sha256=record["audio_sha256"])
            tensor = extract_logmel_input(waveform, context.config["frontend"])
            feature_rows.append(
                {
                    "sample_id": record["sample_id"],
                    "language": record["language"],
                    "label": record["label"],
                    "shape": list(tensor.shape),
                    "dtype": str(tensor.dtype),
                    "decoded_pcm_sha256": verified_pcm[str(record["sample_id"])],
                    "feature_sha256": tensor_sha256(tensor),
                }
            )
        write_jsonl(output / "synthetic_feature_receipt.jsonl", feature_rows)

        train = stage_records(context, "train", "train_languages")
        indices = epoch_indices(
            train,
            mode=context.config["lane"]["sampler"],
            languages=context.config["lane"]["train_languages"],
            labels=LABELS,
            epoch_size=max(
                len(train),
                len(context.config["lane"]["train_languages"]) * len(LABELS) * 2,
            ),
            seed=_seed_bundle(context.config, context.seed_id)["train_order"],
        )
        sampling_rows = [
            {
                "position": position,
                "sample_id": train[index]["sample_id"],
                "language": train[index]["language"],
                "label": train[index]["label"],
                "source_word": train[index]["source_word"],
                "speaker_or_voice": train[index].get("speaker_id") or train[index].get("voice_id"),
            }
            for position, index in enumerate(indices)
        ]
        write_jsonl(output / "synthetic_sampling_plan.jsonl", sampling_rows)

        completion = _base_receipt(context, "synthetic_dry_run")
        completion.update(
            {
                "schema_version": COMPLETION_RECEIPT_SCHEMA,
                "status": "synthetic_dry_run_pass",
                "completed_at": utc_now(),
                "checkpoint_sha256": None,
                "result_scope": "synthetic fixtures only; no training, evaluation, or empirical claim",
                "output_sha256": hash_inventory(output, exclude_names=("completion_receipt.json",)),
            }
        )
        write_json(output / "completion_receipt.json", completion)
        return completion
    except Exception as exc:
        write_abort_receipt(context, output, "synthetic_dry_run", exc)
        raise


def write_abort_receipt(context: RunContext, output: Path, mode: str, exc: BaseException) -> None:
    value = _base_receipt(context, mode)
    value.update(
        {
            "schema_version": ABORT_RECEIPT_SCHEMA,
            "status": "aborted",
            "aborted_at": utc_now(),
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "partial_output_sha256": hash_inventory(output, exclude_names=("abort_receipt.json",)),
        }
    )
    write_json(output / "abort_receipt.json", value)


def _set_random_seeds(bundle: Mapping[str, int]) -> None:
    os.environ.setdefault("TF_DETERMINISTIC_OPS", "1")
    random.seed(bundle["python"])
    np.random.seed(bundle["numpy"])


def _unexpected_server_status(status: str) -> List[str]:
    allowed_prefix = f"?? {WEEKLY_OUTPUT_PREFIX}/"
    return [line for line in status.splitlines() if line and not line.startswith(allowed_prefix)]


def _build_model(context: RunContext):
    import tensorflow as tf
    from src.model import build_model
    from src.model_config import get_model_kwargs

    bundle = _seed_bundle(context.config, context.seed_id)
    tf.keras.backend.clear_session()
    tf.keras.utils.set_random_seed(bundle["tensorflow"])
    model = build_model(
        tuple(context.config["model"]["input_shape"]),
        len(LABELS),
        **get_model_kwargs(context.config["model"]["profile"]),
    )
    if tuple(model.output_shape) != (None, len(LABELS)):
        raise RunError(f"model output shape violates shared encoder contract: {model.output_shape}")
    return model


class _BatchSequenceBase:
    """Framework-neutral record ordering used by the guarded Keras wrapper."""

    def __init__(self, context: RunContext, records: Sequence[Mapping[str, Any]], training: bool):
        self.context = context
        self.records = tuple(records)
        self.training = training
        self.batch_size = int(context.config["training"]["batch_size"])
        self.epoch = 0
        self.indices: List[int] = []
        self.reset()

    def reset(self) -> None:
        if not self.training:
            self.indices = list(range(len(self.records)))
            self.epoch += 1
            return
        mode = self.context.config["lane"]["sampler"]
        seed = derive_seed(
            self.context.config["protocol_id"],
            self.context.config["lane"]["lane_id"],
            self.context.seed_id,
            "train_order" if self.training else "fixed_eval",
            self.epoch,
        )
        self.indices = epoch_indices(
            self.records,
            mode=mode,
            languages=self.context.config["lane"]["train_languages"],
            labels=LABELS,
            epoch_size=len(self.records),
            seed=seed,
        )
        self.epoch += 1

    def __len__(self) -> int:
        return int(np.ceil(len(self.indices) / self.batch_size))

    def batch(self, index: int) -> Tuple[np.ndarray, np.ndarray, Sequence[Mapping[str, Any]]]:
        selected = self.indices[index * self.batch_size : (index + 1) * self.batch_size]
        rows = [self.records[item] for item in selected]
        features = []
        labels = []
        for record in rows:
            waveform = load_exact_mono_pcm(
                resolve_audio_path(self.context.audio_root, record),
                expected_sha256=record["audio_sha256"],
            )
            features.append(extract_logmel_input(waveform, self.context.config["frontend"]))
            labels.append(LABEL_TO_INDEX[record["label"]])
        x = np.stack(features).astype(np.float32, copy=False)
        y = np.eye(len(LABELS), dtype=np.float32)[np.asarray(labels, dtype=np.int64)]
        return x, y, rows


def _keras_sequence(base: _BatchSequenceBase):
    import tensorflow as tf

    class Sequence(tf.keras.utils.Sequence):
        def __len__(self):
            return len(base)

        def __getitem__(self, index):
            x, y, _ = base.batch(index)
            return x, y

        def on_epoch_end(self):
            if base.training:
                base.reset()

    return Sequence()


def _predict(model, context: RunContext, records: Sequence[Mapping[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
    base = _BatchSequenceBase(context, records, training=False)
    probabilities = np.asarray(model.predict(_keras_sequence(base), verbose=0), dtype=np.float64)
    truth = np.asarray([LABEL_TO_INDEX[record["label"]] for record in records], dtype=np.int64)
    if probabilities.shape != (len(records), len(LABELS)):
        raise RunError(f"prediction shape mismatch: {probabilities.shape}")
    return probabilities, truth


def _selection_key(metrics: Mapping[str, Any], epoch: int) -> Tuple[float, float, float, int]:
    macro = metrics["macro_f1"] if metrics["macro_f1"] is not None else -1.0
    emergency = metrics["emergency_recall"] if metrics["emergency_recall"] is not None else -1.0
    return (float(macro), float(emergency), -float(metrics["nll"]), -int(epoch))


def run_guarded_training(context: RunContext, expected_git_commit: str, allow_execution: bool) -> Dict[str, Any]:
    if not allow_execution or os.environ.get("DRONE_W33_MULTILINGUAL_EXECUTION_APPROVED") != "YES":
        raise RunError("training requires --allow-execution and DRONE_W33_MULTILINGUAL_EXECUTION_APPROVED=YES")
    if context.output_dir is None:
        raise RunError("training output directory is required")
    expected_output = (
        context.repo_root
        / WEEKLY_OUTPUT_PREFIX
        / context.config["lane"]["run_name"]
        / f"seed_{context.seed_id:02d}"
    ).resolve()
    if context.output_dir != expected_output:
        raise RunError(f"training output must be {expected_output}")
    git = git_identity(context.repo_root)
    if git["commit"] != expected_git_commit or _unexpected_server_status(git["status"]):
        raise RunError("server execution requires the exact clean committed SHA")
    validate_lane_dataset_contract(context)
    # Test audio is deliberately not touched until selection and calibration
    # artifacts are frozen below.
    development_records = tuple(
        list(stage_records(context, "train", "train_languages"))
        + list(stage_records(context, "validation_selection", "selection_languages"))
        + list(stage_records(context, "validation_calibration", "calibration_languages"))
    )
    for record in development_records:
        path = resolve_audio_path(context.audio_root, record)
        waveform = load_exact_mono_pcm(path, expected_sha256=record["audio_sha256"])
        pcm_hash = sha256_bytes(np.ascontiguousarray(waveform.astype("<f4")).tobytes())
        if pcm_hash != record["decoded_pcm_sha256"]:
            raise RunError(f"decoded PCM SHA-256 mismatch: {record['sample_id']}")

    output = context.output_dir
    output.mkdir(parents=True, exist_ok=False)
    start = _base_receipt(context, "guarded_training")
    start.update({"schema_version": START_RECEIPT_SCHEMA, "status": "started", "started_at": utc_now()})
    write_json(output / "start_receipt.json", start)
    write_json(output / "run_config.json", dict(context.config))
    try:
        import tensorflow as tf

        bundle = _seed_bundle(context.config, context.seed_id)
        _set_random_seeds(bundle)
        model = _build_model(context)
        model.compile(
            optimizer=tf.keras.optimizers.Adam(float(context.config["training"]["learning_rate"])),
            loss="categorical_crossentropy",
        )
        checkpoint_dir = output / "checkpoints"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_path = checkpoint_dir / "selected.weights.h5"
        train_base = _BatchSequenceBase(
            context,
            stage_records(context, "train", "train_languages"),
            training=True,
        )
        train_sequence = _keras_sequence(train_base)
        validation_records = stage_records(
            context,
            "validation_selection",
            "selection_languages",
        )
        selection_rows: List[Mapping[str, Any]] = []
        best_key: Tuple[float, float, float, int] | None = None
        best_epoch: int | None = None
        patience = int(context.config["selection"]["early_stopping_patience"])
        stale = 0
        for epoch in range(int(context.config["training"]["max_epochs"])):
            history = model.fit(train_sequence, epochs=1, verbose=2)
            probabilities, truth = _predict(model, context, validation_records)
            metrics = compute_metrics(
                truth,
                probabilities,
                [str(record["language"]) for record in validation_records],
                ece_bins=int(context.config["metrics"]["ece_bins"]),
            )
            key = _selection_key(metrics, epoch)
            improved = best_key is None or key > best_key
            selection_rows.append(
                {
                    "epoch": epoch,
                    "training_loss": float(history.history["loss"][-1]),
                    "selection_key": list(key),
                    "improved": improved,
                    "metrics": metrics,
                }
            )
            write_jsonl(output / "selection_history.jsonl", selection_rows)
            if improved:
                model.save_weights(checkpoint_path)
                best_key = key
                best_epoch = epoch
                stale = 0
            else:
                stale += 1
            if stale >= patience:
                break
        if best_epoch is None or not checkpoint_path.exists():
            raise RunError("no checkpoint satisfied the selection procedure")
        model.load_weights(checkpoint_path)

        calibration_records = stage_records(
            context,
            "validation_calibration",
            "calibration_languages",
        )
        calibration_probabilities, calibration_truth = _predict(model, context, calibration_records)
        calibration = fit_temperature(calibration_probabilities, calibration_truth)
        calibration.update(
            {
                "dataset": "validation_calibration",
                "manifest_sha256": context.manifest.sha256,
                "split_sha256": context.manifest.split_sha256,
                "threshold_policy": "calibrated_argmax_no_tuned_thresholds",
            }
        )
        write_json(output / "calibration_receipt.json", calibration)

        # The sealed-test bytes are first accessed only after checkpoint and
        # validation-only calibration receipts exist.
        test_records = stage_records(context, "test", "evaluation_languages")
        for record in test_records:
            path = resolve_audio_path(context.audio_root, record)
            waveform = load_exact_mono_pcm(path, expected_sha256=record["audio_sha256"])
            pcm_hash = sha256_bytes(np.ascontiguousarray(waveform.astype("<f4")).tobytes())
            if pcm_hash != record["decoded_pcm_sha256"]:
                raise RunError(f"decoded PCM SHA-256 mismatch: {record['sample_id']}")
        raw_probabilities, truth = _predict(model, context, test_records)
        probabilities = temperature_scale(raw_probabilities, calibration["temperature"])
        metrics = compute_metrics(
            truth,
            probabilities,
            [str(record["language"]) for record in test_records],
            ece_bins=int(context.config["metrics"]["ece_bins"]),
        )
        metrics.update(
            {
                "condition": "clean",
                "manifest_sha256": context.manifest.sha256,
                "split_sha256": context.manifest.split_sha256,
                "checkpoint_sha256": sha256_file(checkpoint_path),
                "calibration_receipt_sha256": sha256_file(output / "calibration_receipt.json"),
            }
        )
        write_json(output / "metrics.json", metrics)

        prediction_rows = []
        for index, record in enumerate(test_records):
            predicted_index = int(np.argmax(probabilities[index]))
            waveform = load_exact_mono_pcm(
                resolve_audio_path(context.audio_root, record),
                expected_sha256=record["audio_sha256"],
            )
            feature_hash = tensor_sha256(extract_logmel_input(waveform, context.config["frontend"]))
            prediction_rows.append(
                {
                    "schema_version": PREDICTION_SCHEMA,
                    "sample_id": record["sample_id"],
                    "language": record["language"],
                    "source_dataset": record["source_dataset"],
                    "source_word": record["source_word"],
                    "true_label": record["label"],
                    "predicted_label": LABELS[predicted_index],
                    "raw_probabilities": raw_probabilities[index].tolist(),
                    "calibrated_probabilities": probabilities[index].tolist(),
                    "confidence": float(np.max(probabilities[index])),
                    "condition": "clean",
                    "audio_sha256": record["audio_sha256"],
                    "decoded_pcm_sha256": record["decoded_pcm_sha256"],
                    "feature_sha256": feature_hash,
                    "frontend_contract_sha256": frontend_contract_sha256(context.config["frontend"]),
                    "noise_contract_sha256": sha256_bytes(canonical_json_bytes(_noise_contract(context.config))),
                    "checkpoint_sha256": sha256_file(checkpoint_path),
                    "calibration_receipt_sha256": sha256_file(output / "calibration_receipt.json"),
                }
            )
        write_jsonl(output / "per_sample_predictions.jsonl", prediction_rows)

        completion = _base_receipt(context, "guarded_training")
        completion.update(
            {
                "schema_version": COMPLETION_RECEIPT_SCHEMA,
                "status": "completed",
                "completed_at": utc_now(),
                "selected_epoch": best_epoch,
                "checkpoint_sha256": sha256_file(checkpoint_path),
                "run_config_sha256": sha256_file(output / "run_config.json"),
                "metrics_sha256": sha256_file(output / "metrics.json"),
                "predictions_sha256": sha256_file(output / "per_sample_predictions.jsonl"),
                "output_sha256": hash_inventory(output, exclude_names=("completion_receipt.json",)),
            }
        )
        write_json(output / "completion_receipt.json", completion)
        return completion
    except Exception as exc:
        write_abort_receipt(context, output, "guarded_training", exc)
        raise
