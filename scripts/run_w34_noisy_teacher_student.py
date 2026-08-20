#!/usr/bin/env python3
"""W34 manifest-driven noisy Teacher--Student comparison.

This entrypoint has one path: train one complete scope.  It uses the frozen
manifest and its four declared splits, keeps test audio sealed until student
selection and calibration are written, and emits only readable run artifacts.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import traceback
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import tensorflow as tf


LABELS = ("emergency", "movement", "unknown")
LABEL_TO_INDEX = {label: index for index, label in enumerate(LABELS)}
LANGUAGES = ("en", "es", "de")
SPLITS = ("train", "validation_selection", "validation_calibration", "test")
REQUIRED_RECORD_FIELDS = (
    "sample_id",
    "relative_audio_path",
    "language",
    "label",
    "source_word",
    "speaker_id",
    "voice_id",
    "isolation_group_id",
    "duplicate_group_id",
    "split",
    "sample_rate_hz",
    "channels",
    "num_samples",
)


class ContractError(ValueError):
    pass


def read_json(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ContractError(f"expected a JSON object: {path}")
    return value


def load_records(manifest_path: Path, receipt_path: Path) -> tuple[dict[str, Any], ...]:
    receipt = read_json(receipt_path)
    if receipt.get("status") != "pass" or receipt.get("frozen") is not True:
        raise ContractError("dataset validation receipt is not a frozen pass")
    if tuple(receipt.get("labels", ())) != LABELS:
        raise ContractError("validation receipt does not declare the ordered three-class labels")

    rows: list[dict[str, Any]] = []
    with manifest_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ContractError(f"manifest line {line_number} is not an object")
            missing = [field for field in REQUIRED_RECORD_FIELDS if field not in row]
            if missing:
                raise ContractError(f"manifest line {line_number} is missing {missing}")
            if row["language"] not in LANGUAGES or row["label"] not in LABELS:
                raise ContractError(f"manifest line {line_number} has an unsupported language or label")
            if row["split"] not in SPLITS:
                raise ContractError(f"manifest line {line_number} has an unsupported split")
            if row["sample_rate_hz"] != 16000 or row["channels"] != 1 or row["num_samples"] != 16000:
                raise ContractError(f"manifest line {line_number} violates the audio contract")
            if not row["relative_audio_path"] or str(row["relative_audio_path"]).startswith("/"):
                raise ContractError(f"manifest line {line_number} has an unsafe audio path")
            if not (str(row["speaker_id"]).strip() or str(row["voice_id"]).strip()):
                raise ContractError(f"manifest line {line_number} has no speaker or voice identity")
            rows.append(row)

    if not rows:
        raise ContractError("manifest is empty")
    if len({str(row["sample_id"]) for row in rows}) != len(rows):
        raise ContractError("manifest sample_id values are not unique")
    for group_field in ("isolation_group_id", "duplicate_group_id"):
        split_by_group: dict[str, set[str]] = defaultdict(set)
        for row in rows:
            value = str(row[group_field]).strip()
            if value:
                split_by_group[value].add(str(row["split"]))
        if any(len(splits) > 1 for splits in split_by_group.values()):
            raise ContractError(f"{group_field} crosses frozen splits")
    for split in SPLITS:
        if not any(row["split"] == split for row in rows):
            raise ContractError(f"frozen manifest has no {split} rows")
    return tuple(rows)


def load_audio(path: Path) -> np.ndarray:
    import soundfile as sf

    info = sf.info(path)
    if info.channels != 1 or info.samplerate != 16000 or info.frames != 16000:
        raise ContractError(f"audio is not mono 16 kHz 1 s: {path}")
    if not str(info.subtype).startswith("PCM_"):
        raise ContractError(f"audio is not PCM: {path}")
    waveform, sample_rate = sf.read(path, dtype="float32", always_2d=False)
    waveform = np.asarray(waveform, dtype=np.float32)
    if sample_rate != 16000 or waveform.shape != (16000,) or not np.all(np.isfinite(waveform)):
        raise ContractError(f"decoded audio violates the exact waveform contract: {path}")
    return waveform


def logmel(waveform: np.ndarray, frontend: Mapping[str, Any]) -> np.ndarray:
    os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/numba_cache")
    import librosa

    mel = librosa.feature.melspectrogram(
        y=waveform,
        sr=16000,
        n_fft=int(frontend["n_fft"]),
        hop_length=int(frontend["hop_length"]),
        center=bool(frontend["center"]),
        n_mels=int(frontend["n_mels"]),
        fmin=float(frontend["fmin_hz"]),
        fmax=frontend["fmax_hz"],
        power=float(frontend["power"]),
    )
    feature = librosa.power_to_db(mel, ref=np.max, top_db=float(frontend["top_db"]))
    max_frames = int(frontend["max_frames"])
    if feature.shape[1] < max_frames:
        feature = np.pad(
            feature,
            ((0, 0), (0, max_frames - feature.shape[1])),
            mode="constant",
            constant_values=float(frontend["pad_value_db"]),
        )
    feature = feature[:, :max_frames]
    tensor = np.expand_dims(feature, axis=-1).astype(np.float32, copy=False)
    if tensor.shape != (256, 32, 1) or not np.all(np.isfinite(tensor)):
        raise ContractError(f"frontend produced an invalid tensor shape or value set: {tensor.shape}")
    return tensor


def stable_number(value: str) -> int:
    number = 0
    for index, character in enumerate(value):
        number = (number * 131 + ord(character) + index) & 0xFFFFFFFF
    return number


class Cycle:
    def __init__(self, values: Iterable[Any], rng: random.Random):
        self.values = list(values)
        if not self.values:
            raise ContractError("balanced sampler encountered an empty group")
        self.rng = rng
        self.order: list[Any] = []
        self.position = 0

    def next(self) -> Any:
        if self.position >= len(self.order):
            self.order = list(self.values)
            self.rng.shuffle(self.order)
            self.position = 0
        value = self.order[self.position]
        self.position += 1
        return value


def balanced_indices(
    records: Sequence[Mapping[str, Any]],
    languages: Sequence[str],
    sampler: str,
    epoch_size: int,
    seed: int,
) -> list[int]:
    rng = random.Random(seed)
    cell_records: dict[tuple[str, ...], list[int]] = defaultdict(list)
    word_records: dict[tuple[str, ...], list[int]] = defaultdict(list)
    speaker_records: dict[tuple[str, ...], list[int]] = defaultdict(list)
    language_balanced = sampler == "language_class_word_speaker_balanced"
    required_cells = [
        (language, label) if language_balanced else (label,)
        for language in (languages if language_balanced else ("_",))
        for label in LABELS
    ]
    for index, row in enumerate(records):
        cell = (str(row["language"]), str(row["label"])) if language_balanced else (str(row["label"]),)
        word = cell + (str(row["source_word"]),)
        speaker = word + (str(row.get("speaker_id") or row.get("voice_id")),)
        cell_records[cell].append(index)
        word_records[word].append(index)
        speaker_records[speaker].append(index)
    missing = [cell for cell in required_cells if not cell_records.get(cell)]
    if missing:
        raise ContractError(f"balanced sampler missing cells: {missing}")

    cell_cycle = Cycle(required_cells, rng)
    word_cycles: dict[tuple[str, ...], Cycle] = {}
    speaker_cycles: dict[tuple[str, ...], Cycle] = {}
    record_cycles: dict[tuple[str, ...], Cycle] = {}
    for cell in required_cells:
        words = sorted({word[-1] for word in word_records if word[:-1] == cell})
        word_cycles[cell] = Cycle(words, rng)
        for word_value in words:
            word = cell + (word_value,)
            speakers = sorted({speaker[-1] for speaker in speaker_records if speaker[:-1] == word})
            speaker_cycles[word] = Cycle(speakers, rng)
            for speaker_value in speakers:
                speaker = word + (speaker_value,)
                record_cycles[speaker] = Cycle(speaker_records[speaker], rng)

    indices: list[int] = []
    for _ in range(epoch_size):
        cell = cell_cycle.next()
        word_value = word_cycles[cell].next()
        word = cell + (word_value,)
        speaker_value = speaker_cycles[word].next()
        speaker = word + (speaker_value,)
        indices.append(int(record_cycles[speaker].next()))
    return indices


@dataclass(frozen=True)
class Scope:
    name: str
    languages: tuple[str, ...]
    sampler: str


class NoiseBank:
    def __init__(self, root: Path, snr_db: float):
        import soundfile as sf

        self.paths = sorted(root.rglob("*.wav"))
        if not self.paths:
            raise ContractError(f"no Tello noise WAVs found under {root}")
        self.snr_db = float(snr_db)
        self._cache: dict[Path, np.ndarray] = {}
        for path in self.paths:
            info = sf.info(path)
            if info.channels != 1 or info.samplerate != 16000 or info.frames != 16000:
                raise ContractError(f"Tello noise is not mono 16 kHz 1 s: {path}")

    def _read(self, path: Path) -> np.ndarray:
        if path not in self._cache:
            self._cache[path] = load_audio(path)
        return self._cache[path]

    def mix(self, clean: np.ndarray, sample_id: str) -> np.ndarray:
        path = self.paths[stable_number(sample_id) % len(self.paths)]
        noise = self._read(path)
        signal_rms = float(np.sqrt(np.mean(np.square(clean))))
        noise_rms = float(np.sqrt(np.mean(np.square(noise))))
        if signal_rms <= 0.0 or noise_rms <= 0.0:
            raise ContractError(f"cannot mix silent audio for {sample_id}")
        target_ratio = 10.0 ** (self.snr_db / 20.0)
        return (clean + noise * (signal_rms / target_ratio / noise_rms)).astype(np.float32)


class ManifestSequence(tf.keras.utils.Sequence):
    def __init__(
        self,
        tf,
        records: Sequence[Mapping[str, Any]],
        audio_root: Path,
        frontend: Mapping[str, Any],
        noise_bank: NoiseBank | None,
        batch_size: int,
        languages: Sequence[str],
        sampler: str,
        condition: str,
        training: bool,
        seed: int,
    ):
        super().__init__()
        self.tf = tf
        self.records = tuple(records)
        self.audio_root = audio_root
        self.frontend = frontend
        self.noise_bank = noise_bank
        self.batch_size = int(batch_size)
        self.languages = tuple(languages)
        self.sampler = sampler
        self.condition = condition
        self.training = training
        self.seed = int(seed)
        self.epoch = 0
        self.indices: list[int] = []
        self.reset()

    def reset(self) -> None:
        if self.training:
            self.indices = balanced_indices(
                self.records,
                self.languages,
                self.sampler,
                len(self.records),
                self.seed + self.epoch,
            )
        else:
            self.indices = list(range(len(self.records)))
        self.epoch += 1

    def __len__(self) -> int:
        return int(math.ceil(len(self.indices) / self.batch_size))

    def _features(self, row: Mapping[str, Any], noisy: bool) -> np.ndarray:
        path = (self.audio_root / str(row["relative_audio_path"])).resolve()
        try:
            path.relative_to(self.audio_root.resolve())
        except ValueError as exc:
            raise ContractError(f"audio path escapes the frozen audio root: {path}") from exc
        clean = load_audio(path)
        waveform = self.noise_bank.mix(clean, str(row["sample_id"])) if noisy else clean
        return logmel(waveform, self.frontend)

    def __getitem__(self, batch_index: int):
        selected = self.indices[batch_index * self.batch_size : (batch_index + 1) * self.batch_size]
        rows = [self.records[index] for index in selected]
        noisy = self.condition in {"noisy", "paired"}
        clean_x = np.stack([self._features(row, noisy=False) for row in rows]).astype(np.float32, copy=False)
        noisy_x = np.stack([self._features(row, noisy=True) for row in rows]).astype(np.float32, copy=False) if noisy else None
        labels = np.asarray([LABEL_TO_INDEX[str(row["label"])] for row in rows], dtype=np.int64)
        y = np.eye(len(LABELS), dtype=np.float32)[labels]
        if self.condition == "paired":
            return {"clean": clean_x, "noisy": noisy_x}, y
        return (noisy_x if noisy_x is not None else clean_x), y

    def on_epoch_end(self) -> None:
        if self.training:
            self.reset()


def stage(records: Sequence[Mapping[str, Any]], split: str, languages: Sequence[str]) -> tuple[Mapping[str, Any], ...]:
    selected = tuple(row for row in records if row["split"] == split and row["language"] in languages)
    if not selected:
        raise ContractError(f"no records for {split} and languages={tuple(languages)}")
    return selected


def require_cells(records: Sequence[Mapping[str, Any]], languages: Sequence[str]) -> None:
    for split in SPLITS:
        rows = [row for row in records if row["split"] == split]
        for language in languages:
            for label in LABELS:
                if not any(row["language"] == language and row["label"] == label for row in rows):
                    raise ContractError(f"missing {split}/{language}/{label}")


def set_seed(seed: int) -> None:
    os.environ.setdefault("TF_DETERMINISTIC_OPS", "1")
    random.seed(seed)
    np.random.seed(seed)


def make_model(tf, config: Mapping[str, Any], seed: int):
    from src.model import build_model
    from src.model_config import get_model_kwargs

    tf.keras.utils.set_random_seed(seed)
    model = build_model(
        tuple(config["model"]["input_shape"]),
        int(config["model"]["num_classes"]),
        **get_model_kwargs(str(config["model"]["profile"])),
    )
    if tuple(model.output_shape) != (None, len(LABELS)):
        raise ContractError(f"model output shape is {model.output_shape}")
    return model


def make_probe(tf, model):
    names = {layer.name for layer in model.layers}
    fused = model.get_layer("fused_embed").output if "fused_embed" in names else model.layers[-1].input
    mel = model.get_layer("mel_embed").output if "mel_embed" in names else fused
    return tf.keras.Model(model.input, [model.output, fused, mel], name=f"{model.name}_probe")


def make_distiller(tf, student_probe, teacher_probe, distill: Mapping[str, Any]):
    class _Distiller(tf.keras.Model):
        def __init__(self):
            super().__init__()
            self.student_probe = student_probe
            self.teacher_probe = teacher_probe
            self.classification_weight = float(distill["classification_weight"])
            self.logit_weight = float(distill["logit_weight"])
            self.embedding_weight = float(distill["embedding_weight"])
            self.temperature = float(distill["temperature"])
            self.ce = tf.keras.losses.CategoricalCrossentropy()
            self.kld = tf.keras.losses.KLDivergence()
            self.mse = tf.keras.losses.MeanSquaredError()
            self.loss_tracker = tf.keras.metrics.Mean(name="loss")
            self.accuracy = tf.keras.metrics.CategoricalAccuracy(name="accuracy")

        @property
        def metrics(self):
            return [self.loss_tracker, self.accuracy]

        def train_step(self, data):
            x, y = data
            clean_x = x["clean"]
            noisy_x = x["noisy"]
            teacher_probs, teacher_embed, _ = self.teacher_probe(clean_x, training=False)
            with tf.GradientTape() as tape:
                student_probs, student_embed, _ = self.student_probe(noisy_x, training=True)
                ce = self.ce(y, student_probs)
                teacher_soft = tf.nn.softmax(tf.math.log(tf.clip_by_value(teacher_probs, 1e-7, 1.0)) / self.temperature)
                student_soft = tf.nn.softmax(tf.math.log(tf.clip_by_value(student_probs, 1e-7, 1.0)) / self.temperature)
                logits = self.kld(teacher_soft, student_soft) * (self.temperature ** 2)
                teacher_norm = tf.math.l2_normalize(tf.stop_gradient(teacher_embed), axis=-1)
                student_norm = tf.math.l2_normalize(student_embed, axis=-1)
                embed = self.mse(teacher_norm, student_norm)
                loss = self.classification_weight * ce + self.logit_weight * logits + self.embedding_weight * embed
            variables = self.student_probe.trainable_variables
            gradients = tape.gradient(loss, variables)
            self.optimizer.apply_gradients(zip(gradients, variables))
            self.loss_tracker.update_state(loss)
            self.accuracy.update_state(y, student_probs)
            return {metric.name: metric.result() for metric in self.metrics}

    teacher_probe.trainable = False
    return _Distiller()


def metric_bundle(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    languages: Sequence[str],
    include_language: bool = True,
) -> dict[str, Any]:
    truth = np.asarray(y_true, dtype=np.int64)
    probs = np.asarray(probabilities, dtype=np.float64)
    prediction = np.argmax(probs, axis=1)
    per_class: dict[str, dict[str, Any]] = {}
    for index, label in enumerate(LABELS):
        support = int(np.sum(truth == index))
        tp = int(np.sum((truth == index) & (prediction == index)))
        fp = int(np.sum((truth != index) & (prediction == index)))
        fn = int(np.sum((truth == index) & (prediction != index)))
        precision = None if tp + fp == 0 else tp / (tp + fp)
        recall = None if support == 0 else tp / support
        f1 = None
        if precision is not None and recall is not None and precision + recall:
            f1 = 2.0 * precision * recall / (precision + recall)
        elif support:
            f1 = 0.0
        per_class[label] = {
            "support": support,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "tp": tp,
            "fp": fp,
            "fn": fn,
        }
    defined = [value["f1"] for value in per_class.values() if value["f1"] is not None]
    confusion = [[int(np.sum((truth == row) & (prediction == column))) for column in range(3)] for row in range(3)]
    language_metrics: dict[str, Any] = {}
    language_array = np.asarray(languages, dtype=object)
    if include_language:
        for language in sorted(set(str(value) for value in language_array)):
            mask = language_array == language
            language_metrics[language] = metric_bundle(
                truth[mask], probs[mask], language_array[mask].tolist(), include_language=False
            )["per_class"]
    correct_probability = np.clip(probs[np.arange(len(truth)), truth], 1e-12, 1.0)
    return {
        "label_order": list(LABELS),
        "support": int(len(truth)),
        "per_class": per_class,
        "macro_f1": None if not defined else float(np.mean(defined)),
        "emergency_recall": per_class["emergency"]["recall"],
        "movement_recall": per_class["movement"]["recall"],
        "unknown_recall": per_class["unknown"]["recall"],
        "confusion_matrix": confusion,
        "nll": float(-np.mean(np.log(correct_probability))),
        "per_language": language_metrics,
    }


def fit_temperature(probabilities: np.ndarray, truth: np.ndarray) -> float:
    from scipy.optimize import minimize_scalar

    def objective(value: float) -> float:
        logits = np.log(np.clip(probabilities, 1e-12, 1.0)) / value
        logits -= np.max(logits, axis=1, keepdims=True)
        scaled = np.exp(logits)
        scaled /= np.sum(scaled, axis=1, keepdims=True)
        return float(-np.mean(np.log(np.clip(scaled[np.arange(len(truth)), truth], 1e-12, 1.0))))

    result = minimize_scalar(objective, bounds=(0.05, 10.0), method="bounded")
    if not result.success:
        raise ContractError(f"temperature fitting failed: {result.message}")
    return float(result.x)


def scale_probabilities(probabilities: np.ndarray, temperature: float) -> np.ndarray:
    logits = np.log(np.clip(probabilities, 1e-12, 1.0)) / temperature
    logits -= np.max(logits, axis=1, keepdims=True)
    scaled = np.exp(logits)
    return scaled / np.sum(scaled, axis=1, keepdims=True)


def predict(tf, model, sequence: ManifestSequence) -> tuple[np.ndarray, np.ndarray, tuple[Mapping[str, Any], ...]]:
    probabilities = np.asarray(model.predict(sequence, verbose=0), dtype=np.float64)
    rows = tuple(sequence.records)
    truth = np.asarray([LABEL_TO_INDEX[str(row["label"])] for row in rows], dtype=np.int64)
    if probabilities.shape != (len(rows), len(LABELS)):
        raise ContractError(f"prediction shape is {probabilities.shape}")
    return probabilities, truth, rows


def selection_key(metrics: Mapping[str, Any], epoch: int) -> tuple[float, float, float, int]:
    return (
        float(metrics["macro_f1"] if metrics["macro_f1"] is not None else -1.0),
        float(metrics["emergency_recall"] if metrics["emergency_recall"] is not None else -1.0),
        -float(metrics["nll"]),
        -int(epoch),
    )


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def append_jsonl(path: Path, values: Sequence[Mapping[str, Any]]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        for value in values:
            handle.write(json.dumps(value, ensure_ascii=False) + "\n")


def fit_teacher(
    tf,
    config: Mapping[str, Any],
    scope: Scope,
    records: Sequence[Mapping[str, Any]],
    audio_root: Path,
    frontend: Mapping[str, Any],
    teacher_dir: Path,
    seed: int,
) -> tuple[Any, dict[str, Any]]:
    teacher_dir.mkdir()
    model = make_model(tf, config, seed)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(float(config["training"]["learning_rate"])),
        loss="categorical_crossentropy",
    )
    train = stage(records, "train", scope.languages)
    validation = stage(records, "validation_selection", scope.languages)
    train_sequence = ManifestSequence(
        tf, train, audio_root, frontend, None, config["training"]["batch_size"], scope.languages,
        scope.sampler, "clean", True, seed + 11,
    )
    validation_sequence = ManifestSequence(
        tf, validation, audio_root, frontend, None, config["training"]["batch_size"], scope.languages,
        scope.sampler, "clean", False, seed + 12,
    )
    checkpoint = teacher_dir / "selected.weights.h5"
    best_key: tuple[float, float, float, int] | None = None
    best_epoch = None
    stale = 0
    history: list[dict[str, Any]] = []
    for epoch in range(int(config["training"]["max_epochs"])):
        fit_result = model.fit(train_sequence, epochs=1, verbose=2)
        probabilities, truth, rows = predict(tf, model, validation_sequence)
        metrics = metric_bundle(truth, probabilities, [str(row["language"]) for row in rows])
        key = selection_key(metrics, epoch)
        improved = best_key is None or key > best_key
        history.append({
            "epoch": epoch,
            "training_loss": float(fit_result.history["loss"][-1]),
            "selection_key": list(key),
            "improved": improved,
            "metrics": metrics,
        })
        write_jsonl(teacher_dir / "selection_history.jsonl", history)
        if improved:
            model.save_weights(checkpoint)
            best_key = key
            best_epoch = epoch
            stale = 0
        else:
            stale += 1
        if stale >= int(config["training"]["early_stopping_patience"]):
            break
    if best_epoch is None:
        raise ContractError("teacher selection produced no checkpoint")
    model.load_weights(checkpoint)
    info = {"selected_epoch": best_epoch, "selection_metrics": history[best_epoch]["metrics"]}
    write_json(teacher_dir / "selection.json", info)
    return model, info


def fit_student(
    tf,
    config: Mapping[str, Any],
    scope: Scope,
    records: Sequence[Mapping[str, Any]],
    audio_root: Path,
    frontend: Mapping[str, Any],
    noise_bank: NoiseBank,
    teacher_model: Any,
    student_dir: Path,
    seed: int,
) -> tuple[Any, dict[str, Any]]:
    student_dir.mkdir()
    student_model = make_model(tf, config, seed)
    teacher_probe = make_probe(tf, teacher_model)
    student_probe = make_probe(tf, student_model)
    distiller = make_distiller(tf, student_probe, teacher_probe, config["distillation"])
    distiller.compile(optimizer=tf.keras.optimizers.Adam(float(config["training"]["learning_rate"])))

    train = stage(records, "train", scope.languages)
    validation = stage(records, "validation_selection", scope.languages)
    train_sequence = ManifestSequence(
        tf, train, audio_root, frontend, noise_bank, config["training"]["batch_size"], scope.languages,
        scope.sampler, "paired", True, seed + 21,
    )
    validation_sequence = ManifestSequence(
        tf, validation, audio_root, frontend, noise_bank, config["training"]["batch_size"], scope.languages,
        scope.sampler, "noisy", False, seed + 22,
    )
    checkpoint = student_dir / "selected.weights.h5"
    best_key: tuple[float, float, float, int] | None = None
    best_epoch = None
    stale = 0
    history: list[dict[str, Any]] = []
    for epoch in range(int(config["training"]["max_epochs"])):
        fit_result = distiller.fit(train_sequence, epochs=1, verbose=2)
        probabilities, truth, rows = predict(tf, student_model, validation_sequence)
        metrics = metric_bundle(truth, probabilities, [str(row["language"]) for row in rows])
        key = selection_key(metrics, epoch)
        improved = best_key is None or key > best_key
        history.append({
            "epoch": epoch,
            "training_loss": float(fit_result.history["loss"][-1]),
            "selection_key": list(key),
            "improved": improved,
            "metrics": metrics,
        })
        write_jsonl(student_dir / "selection_history.jsonl", history)
        if improved:
            student_model.save_weights(checkpoint)
            best_key = key
            best_epoch = epoch
            stale = 0
        else:
            stale += 1
        if stale >= int(config["training"]["early_stopping_patience"]):
            break
    if best_epoch is None:
        raise ContractError("student selection produced no checkpoint")
    student_model.load_weights(checkpoint)
    info = {"selected_epoch": best_epoch, "selection_metrics": history[best_epoch]["metrics"]}
    write_json(student_dir / "selection.json", info)
    return student_model, info


def predictions_jsonl(path: Path, probabilities: np.ndarray, truth: np.ndarray, rows: Sequence[Mapping[str, Any]], condition: str) -> None:
    values = []
    for index, row in enumerate(rows):
        values.append({
            "sample_id": row["sample_id"],
            "language": row["language"],
            "true_label": row["label"],
            "predicted_label": LABELS[int(np.argmax(probabilities[index]))],
            "probabilities": probabilities[index].tolist(),
            "condition": condition,
        })
    with path.open("w", encoding="utf-8") as handle:
        for value in values:
            handle.write(json.dumps(value, ensure_ascii=False) + "\n")


def run_scope(args: argparse.Namespace) -> None:
    config = read_json(Path(args.config).resolve())
    if tuple(config["labels"]) != LABELS or tuple(config["splits"]) != SPLITS:
        raise ContractError("W34 config labels or split contract is not the frozen one")
    if config["model"]["profile"] != "xiao_bottleneck256_tflm" or config["model"]["input_shape"] != [256, 32, 1]:
        raise ContractError("W34 model contract is not xiao_bottleneck256_tflm mel-only")
    if config["noise"]["snr_db"] != -10.0 or config["noise"]["probability"] != 1.0 or config["noise"]["prosody"] != "disabled":
        raise ContractError("W34 noise contract is not fixed -10 dB p=1 without prosody")
    scope_value = config["scopes"][args.scope]
    scope = Scope(args.scope, tuple(scope_value["languages"]), str(scope_value["sampler"]))
    manifest = Path(args.manifest).resolve()
    receipt = Path(args.manifest_validation_receipt).resolve()
    records = load_records(manifest, receipt)
    require_cells(records, scope.languages)
    audio_root = Path(args.audio_root).resolve()
    noise_bank = NoiseBank(Path(args.noise_root).resolve(), float(config["noise"]["snr_db"]))
    frontend = config["frontend"]
    output_root = Path(args.output_root).resolve()
    scope_dir = output_root / f"seed_{args.seed:02d}" / args.scope
    if scope_dir.exists():
        raise ContractError(f"refusing to reuse existing W34 scope output: {scope_dir}")
    scope_dir.mkdir(parents=True)
    write_json(scope_dir / "run_config.json", {
        "version": config["version"],
        "scope": scope.__dict__,
        "seed": args.seed,
        "manifest": str(manifest),
        "validation_receipt": str(receipt),
        "audio_root": str(audio_root),
        "noise_root": str(Path(args.noise_root).resolve()),
        "contract": {
            "labels": list(LABELS),
            "splits": list(SPLITS),
            "snr_db": -10.0,
            "noise_probability": 1.0,
            "prosody": "disabled",
            "test_opening": "after_student_checkpoint_and_calibration",
        },
    })
    write_json(scope_dir / "status.json", {"status": "running", "scope": args.scope, "seed": args.seed})
    try:
        import tensorflow as tf

        set_seed(stable_number(f"{args.seed}|{args.scope}|setup"))
        teacher_model, teacher_info = fit_teacher(
            tf, config, scope, records, audio_root, frontend,
            scope_dir / "teacher", stable_number(f"{args.seed}|{args.scope}|teacher"),
        )
        student_model, student_info = fit_student(
            tf, config, scope, records, audio_root, frontend, noise_bank, teacher_model,
            scope_dir / "student", stable_number(f"{args.seed}|{args.scope}|student"),
        )

        calibration_records = stage(records, "validation_calibration", scope.languages)
        calibration_sequence = ManifestSequence(
            tf, calibration_records, audio_root, frontend, noise_bank, config["training"]["batch_size"],
            scope.languages, scope.sampler, "noisy", False, stable_number(f"{args.scope}|calibration"),
        )
        calibration_probs, calibration_truth, calibration_rows = predict(tf, student_model, calibration_sequence)
        temperature = fit_temperature(calibration_probs, calibration_truth)
        calibration = {
            "dataset": "validation_calibration",
            "condition": "student_minus_10_db_noisy",
            "temperature": temperature,
            "selection_checkpoint_frozen": True,
        }
        write_json(scope_dir / "student" / "calibration.json", calibration)

        # The sealed test rows and audio are opened only after the calibration file exists.
        test_records = stage(records, "test", scope.languages)
        clean_sequence = ManifestSequence(
            tf, test_records, audio_root, frontend, noise_bank, config["training"]["batch_size"],
            scope.languages, scope.sampler, "clean", False, stable_number(f"{args.scope}|test-clean"),
        )
        noisy_sequence = ManifestSequence(
            tf, test_records, audio_root, frontend, noise_bank, config["training"]["batch_size"],
            scope.languages, scope.sampler, "noisy", False, stable_number(f"{args.scope}|test-noisy"),
        )
        clean_probs, clean_truth, clean_rows = predict(tf, student_model, clean_sequence)
        noisy_probs, noisy_truth, noisy_rows = predict(tf, student_model, noisy_sequence)
        clean_probs = scale_probabilities(clean_probs, temperature)
        noisy_probs = scale_probabilities(noisy_probs, temperature)
        metrics = {
            "scope": args.scope,
            "seed": args.seed,
            "teacher": teacher_info,
            "student": student_info,
            "calibration": calibration,
            "student_clean_test": metric_bundle(clean_truth, clean_probs, [str(row["language"]) for row in clean_rows]),
            "student_minus_10_db_noisy_test": metric_bundle(noisy_truth, noisy_probs, [str(row["language"]) for row in noisy_rows]),
        }
        write_json(scope_dir / "metrics.json", metrics)
        predictions_jsonl(scope_dir / "student_clean_test_predictions.jsonl", clean_probs, clean_truth, clean_rows, "clean")
        predictions_jsonl(scope_dir / "student_minus_10_db_test_predictions.jsonl", noisy_probs, noisy_truth, noisy_rows, "minus_10_db_noisy")
        write_json(scope_dir / "status.json", {"status": "completed", "scope": args.scope, "seed": args.seed, "metrics": str(scope_dir / "metrics.json")})
    except Exception as exc:
        write_json(scope_dir / "status.json", {
            "status": "aborted",
            "scope": args.scope,
            "seed": args.seed,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        })
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one W34 noisy Teacher--Student language scope")
    parser.add_argument("--config", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--manifest-validation-receipt", required=True)
    parser.add_argument("--audio-root", required=True)
    parser.add_argument("--noise-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--scope", choices=("mixed_en_es_de", "en_only", "es_only", "de_only"), required=True)
    parser.add_argument("--seed", type=int, default=0)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.seed != 0:
        raise SystemExit("W34 is authorized only for seed 0")
    run_scope(args)
