"""Shared runner utilities for Track D baselines."""

from __future__ import annotations

import argparse
import csv
import copy
import os
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from .audio_io import load_audio_1s, synthetic_audio
from .data_loader import load_class_names, load_split, tiny_data_loader_check, validate_label_contract
from .frontends import expected_shape, extract_feature_input, smoke_check_frontends
from .metrics import classification_report_text, metrics_dict, save_confusion_matrix
from .noise import list_noise_files, mix_with_noise, sample_noise_clip
from .receipts import result_tree, source_manifest, write_json, write_text


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def load_config(path: str | Path) -> dict[str, Any]:
    cfg_path = Path(path)
    with cfg_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    extends = config.pop("extends", None)
    if extends:
        parent_path = Path(extends)
        if not parent_path.is_absolute():
            parent_path = Path.cwd() / parent_path
        parent = load_config(parent_path)
        return _deep_merge(parent, config)
    return config


def build_model_from_config(config: dict[str, Any]):
    family = config["baseline"]["family"]
    model_cfg = config["model"]
    if family == "bc_resnet":
        from baselines.bc_resnet.adapter import build_from_config
    elif family == "tc_resnet":
        from baselines.tc_resnet.adapter import build_from_config
    elif family == "ds_cnn":
        from baselines.ds_cnn.adapter import build_from_config
    else:
        raise ValueError(f"Unsupported baseline family: {family}")
    return build_from_config(model_cfg)


def synthetic_forward_check(config: dict[str, Any]) -> dict[str, object]:
    model = build_model_from_config(config)
    frontend_type = config["frontend"]["type"]
    wav = synthetic_audio()
    x = extract_feature_input(wav, frontend_type)
    expected = tuple(config["model"]["input_shape"])
    if x.shape != expected:
        raise ValueError(f"Frontend shape {x.shape} != configured input_shape {expected}")
    y = model(np.expand_dims(x, axis=0), training=False).numpy()
    return {
        "model_name": str(model.name),
        "input_shape": tuple(int(v) for v in x.shape),
        "output_shape": tuple(int(v) for v in y.shape),
        "output_sum": float(np.sum(y)),
        "param_count": int(model.count_params()),
    }


def smoke_check(config: dict[str, Any], check_data: bool = False) -> dict[str, object]:
    frontend_shapes = smoke_check_frontends()
    for frontend_type, shape in frontend_shapes.items():
        if shape != expected_shape(frontend_type):
            raise ValueError(f"{frontend_type} shape check failed: {shape}")

    result: dict[str, object] = {
        "baseline": config["baseline"]["name"],
        "frontend_shapes": {k: tuple(int(v) for v in val) for k, val in frontend_shapes.items()},
        "synthetic_forward": synthetic_forward_check(config),
    }
    if check_data:
        data_cfg = config["data"]
        result["data_loader"] = tiny_data_loader_check(
            data_cfg["processed_data_path"],
            data_cfg["encoder_path"],
        )
    return result


def _ensure_output_dirs(output_dir: Path) -> None:
    for rel in ("history", "checkpoints", "receipts"):
        (output_dir / rel).mkdir(parents=True, exist_ok=True)


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    return value


def _balanced_subset(paths: np.ndarray, labels: np.ndarray, max_samples: int | None, seed: int) -> tuple[np.ndarray, np.ndarray]:
    if max_samples is None or max_samples <= 0 or max_samples >= int(labels.shape[0]):
        return paths, labels
    rng = np.random.default_rng(seed)
    classes = sorted(int(v) for v in np.unique(labels))
    per_class = max(1, int(max_samples) // max(1, len(classes)))
    selected: list[int] = []
    for cls in classes:
        idxs = np.where(labels == cls)[0]
        take = min(per_class, idxs.shape[0])
        selected.extend(rng.choice(idxs, size=take, replace=False).tolist())
    remaining = max(0, int(max_samples) - len(selected))
    if remaining:
        pool = np.setdiff1d(np.arange(labels.shape[0]), np.asarray(selected, dtype=np.int64), assume_unique=False)
        if pool.size:
            selected.extend(rng.choice(pool, size=min(remaining, pool.size), replace=False).tolist())
    selected = sorted(selected)
    return paths[selected], labels[selected]


def _make_sequence_class(tf_module):
    class FeatureSequence(tf_module.keras.utils.Sequence):
        def __init__(
            self,
            paths: np.ndarray,
            labels: np.ndarray,
            batch_size: int,
            num_classes: int,
            frontend_type: str,
            noise_files: list[str],
            rng_seed: int,
            is_training: bool,
            noise_mix_prob: float,
            min_snr_db: float,
            max_snr_db: float,
            eval_snr_db: float,
        ):
            super().__init__()
            self.paths = np.asarray(paths)
            self.labels = np.asarray(labels, dtype=np.int64)
            self.batch_size = int(batch_size)
            self.num_classes = int(num_classes)
            self.frontend_type = str(frontend_type)
            self.noise_files = list(noise_files)
            self.rng = np.random.default_rng(int(rng_seed))
            self.is_training = bool(is_training)
            self.noise_mix_prob = float(noise_mix_prob)
            self.min_snr_db = float(min_snr_db)
            self.max_snr_db = float(max_snr_db)
            self.eval_snr_db = float(eval_snr_db)
            self.indexes = np.arange(self.paths.shape[0])
            self.on_epoch_end()

        def __len__(self):
            return int(np.ceil(self.paths.shape[0] / float(self.batch_size)))

        def on_epoch_end(self):
            if self.is_training:
                self.rng.shuffle(self.indexes)

        def _make_audio(self, path: str) -> np.ndarray:
            clean = load_audio_1s(path)
            noise = sample_noise_clip(self.noise_files, self.rng)
            if noise is None:
                return clean
            if self.is_training:
                if self.rng.random() > self.noise_mix_prob:
                    return clean
                snr_db = self.rng.uniform(self.min_snr_db, self.max_snr_db)
            else:
                snr_db = self.eval_snr_db
            return mix_with_noise(clean, noise, snr_db)

        def __getitem__(self, batch_idx: int):
            idxs = self.indexes[batch_idx * self.batch_size:(batch_idx + 1) * self.batch_size]
            x = np.empty((len(idxs), *expected_shape(self.frontend_type)), dtype=np.float32)
            y = np.empty((len(idxs), self.num_classes), dtype=np.float32)
            for row, idx in enumerate(idxs):
                wav = self._make_audio(str(self.paths[idx]))
                x[row] = extract_feature_input(wav, self.frontend_type)
                y[row] = np.eye(self.num_classes, dtype=np.float32)[int(self.labels[idx])]
            return x, y

        def ordered_true_labels(self) -> np.ndarray:
            ordered: list[int] = []
            for batch_idx in range(len(self)):
                idxs = self.indexes[batch_idx * self.batch_size:(batch_idx + 1) * self.batch_size]
                ordered.extend(int(v) for v in self.labels[idxs])
            return np.asarray(ordered, dtype=np.int64)

    return FeatureSequence


def _write_history_csv(history: dict[str, list[float]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = sorted(history.keys())
    rows = max((len(history[k]) for k in keys), default=0)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["epoch", *keys])
        writer.writeheader()
        for epoch in range(rows):
            row = {"epoch": epoch + 1}
            for key in keys:
                vals = history.get(key, [])
                row[key] = vals[epoch] if epoch < len(vals) else ""
            writer.writerow(row)


def _materialize_feature_arrays(
    paths: np.ndarray,
    labels: np.ndarray,
    *,
    num_classes: int,
    frontend_type: str,
    noise_files: list[str],
    rng_seed: int,
    is_training: bool,
    noise_mix_prob: float,
    min_snr_db: float,
    max_snr_db: float,
    eval_snr_db: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(int(rng_seed))
    x = np.empty((paths.shape[0], *expected_shape(frontend_type)), dtype=np.float32)
    y = np.empty((paths.shape[0], num_classes), dtype=np.float32)
    for row, path in enumerate(paths):
        clean = load_audio_1s(str(path))
        noise = sample_noise_clip(noise_files, rng)
        wav = clean
        if noise is not None:
            if is_training:
                if rng.random() <= noise_mix_prob:
                    snr_db = rng.uniform(min_snr_db, max_snr_db)
                    wav = mix_with_noise(clean, noise, snr_db)
            else:
                wav = mix_with_noise(clean, noise, eval_snr_db)
        x[row] = extract_feature_input(wav, frontend_type)
        y[row] = np.eye(num_classes, dtype=np.float32)[int(labels[row])]
    return x, y, np.asarray(labels, dtype=np.int64)


def _manual_tiny_fit(tf, model, optimizer, x_train, y_train, x_val, y_val, epochs: int, batch_size: int, checkpoint_path: Path) -> dict[str, list[float]]:
    loss_fn = tf.keras.losses.CategoricalCrossentropy()
    history = {"accuracy": [], "loss": [], "val_accuracy": [], "val_loss": []}
    best_val_accuracy = -1.0
    for _ in range(int(epochs)):
        losses: list[float] = []
        correct = 0
        total = 0
        for start in range(0, x_train.shape[0], int(batch_size)):
            xb = tf.convert_to_tensor(x_train[start:start + int(batch_size)], dtype=tf.float32)
            yb = tf.convert_to_tensor(y_train[start:start + int(batch_size)], dtype=tf.float32)
            with tf.GradientTape() as tape:
                preds = model(xb, training=True)
                loss = loss_fn(yb, preds)
            grads = tape.gradient(loss, model.trainable_weights)
            optimizer.apply_gradients((g, w) for g, w in zip(grads, model.trainable_weights) if g is not None)
            losses.append(float(loss.numpy()))
            correct += int(np.sum(np.argmax(preds.numpy(), axis=1) == np.argmax(yb.numpy(), axis=1)))
            total += int(yb.shape[0])

        val_preds = model(tf.convert_to_tensor(x_val, dtype=tf.float32), training=False)
        val_loss = float(loss_fn(tf.convert_to_tensor(y_val, dtype=tf.float32), val_preds).numpy())
        val_accuracy = float(np.mean(np.argmax(val_preds.numpy(), axis=1) == np.argmax(y_val, axis=1)))
        train_accuracy = float(correct / max(1, total))
        train_loss = float(np.mean(losses)) if losses else 0.0
        history["accuracy"].append(train_accuracy)
        history["loss"].append(train_loss)
        history["val_accuracy"].append(val_accuracy)
        history["val_loss"].append(val_loss)
        if val_accuracy >= best_val_accuracy:
            best_val_accuracy = val_accuracy
            checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
            model.save_weights(str(checkpoint_path))
    return history


def _train_batch(tf, model, optimizer, loss_fn, xb, yb) -> tuple[float, int, int]:
    xb_t = tf.convert_to_tensor(xb, dtype=tf.float32)
    yb_t = tf.convert_to_tensor(yb, dtype=tf.float32)
    with tf.GradientTape() as tape:
        preds = model(xb_t, training=True)
        loss = loss_fn(yb_t, preds)
    grads = tape.gradient(loss, model.trainable_weights)
    optimizer.apply_gradients((g, w) for g, w in zip(grads, model.trainable_weights) if g is not None)
    correct = int(np.sum(np.argmax(preds.numpy(), axis=1) == np.argmax(yb, axis=1)))
    return float(loss.numpy()), correct, int(yb.shape[0])


def _eval_sequence(tf, model, loss_fn, seq) -> tuple[float, float]:
    losses: list[float] = []
    correct = 0
    total = 0
    for batch_idx in range(len(seq)):
        xb, yb = seq[batch_idx]
        preds = model(tf.convert_to_tensor(xb, dtype=tf.float32), training=False)
        losses.append(float(loss_fn(tf.convert_to_tensor(yb, dtype=tf.float32), preds).numpy()))
        correct += int(np.sum(np.argmax(preds.numpy(), axis=1) == np.argmax(yb, axis=1)))
        total += int(yb.shape[0])
    return float(np.mean(losses)) if losses else 0.0, float(correct / max(1, total))


def _manual_sequence_fit(tf, model, optimizer, train_seq, val_seq, epochs: int, checkpoint_path: Path, patience: int) -> dict[str, list[float]]:
    loss_fn = tf.keras.losses.CategoricalCrossentropy()
    history = {"accuracy": [], "loss": [], "val_accuracy": [], "val_loss": []}
    best_val_accuracy = -1.0
    stale_epochs = 0
    for _ in range(int(epochs)):
        losses: list[float] = []
        correct = 0
        total = 0
        for batch_idx in range(len(train_seq)):
            xb, yb = train_seq[batch_idx]
            loss, batch_correct, batch_total = _train_batch(tf, model, optimizer, loss_fn, xb, yb)
            losses.append(loss)
            correct += batch_correct
            total += batch_total
        val_loss, val_accuracy = _eval_sequence(tf, model, loss_fn, val_seq)
        train_accuracy = float(correct / max(1, total))
        train_loss = float(np.mean(losses)) if losses else 0.0
        history["accuracy"].append(train_accuracy)
        history["loss"].append(train_loss)
        history["val_accuracy"].append(val_accuracy)
        history["val_loss"].append(val_loss)
        if val_accuracy >= best_val_accuracy:
            best_val_accuracy = val_accuracy
            stale_epochs = 0
            checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
            model.save_weights(str(checkpoint_path))
        else:
            stale_epochs += 1
        if stale_epochs >= int(patience):
            break
        train_seq.on_epoch_end()
    return history


def _startup_lines(config: dict[str, Any], output_dir: Path, run_mode: str, train_count: int, val_count: int, eval_count: int) -> list[str]:
    baseline = config["baseline"]["name"]
    lines = [
        "Track D offline baseline startup receipt",
        f"run_mode={run_mode}",
        f"baseline={baseline}",
        f"family={config['baseline']['family']}",
        f"frontend={config['frontend']['type']}",
        f"output_dir={output_dir}",
        f"processed_data_path={config['data']['processed_data_path']}",
        f"encoder_path={config['data']['encoder_path']}",
        f"noise_source_dir={config['data']['noise_source_dir']}",
        f"eval_snr_db={config['noise']['eval_snr_db']}",
        f"train_count={train_count}",
        f"val_count={val_count}",
        f"eval_count={eval_count}",
    ]
    manifest = source_manifest()
    for key in ("git_branch", "git_head", "python_version", "tensorflow_version", "keras_version"):
        lines.append(f"{key}={manifest.get(key)}")
    return lines[:30]


def run_training(
    config: dict[str, Any],
    *,
    run_mode: str,
    output_root: str | Path | None = None,
    train_samples: int | None = None,
    val_samples: int | None = None,
    eval_samples: int | None = None,
    epochs: int | None = None,
    batch_size: int | None = None,
) -> dict[str, object]:
    if run_mode not in {"tiny-train", "train"}:
        raise ValueError(f"Unsupported training run_mode={run_mode}")

    os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
    import tensorflow as tf
    from tensorflow import keras

    seed = int(config["experiment"].get("seed", 42))
    tf.keras.utils.set_random_seed(seed)

    baseline = config["baseline"]["name"]
    out_root = Path(output_root or config["experiment"]["output_root"])
    output_dir = out_root / baseline
    _ensure_output_dirs(output_dir)

    data_cfg = config["data"]
    train_cfg = config["train"]
    noise_cfg = config["noise"]
    frontend_type = config["frontend"]["type"]

    split = load_split(data_cfg["processed_data_path"])
    class_names = load_class_names(data_cfg["encoder_path"])
    validate_label_contract(class_names)
    noise_files = list_noise_files(data_cfg["noise_source_dir"])

    x_train, y_train = _balanced_subset(split.x_train, split.y_train, train_samples, seed)
    x_val, y_val = _balanced_subset(split.x_val, split.y_val, val_samples, seed + 1)
    x_eval, y_eval = _balanced_subset(split.x_test, split.y_test, eval_samples, seed + 2)

    eff_epochs = int(epochs or train_cfg["max_epochs"])
    eff_batch_size = int(batch_size or train_cfg["batch_size"])
    startup = _startup_lines(config, output_dir, run_mode, len(y_train), len(y_val), len(y_eval))
    write_text(output_dir / "receipts" / "startup_first30.txt", "\n".join(startup) + "\n")

    run_config = _jsonable(
        {
            **config,
            "execution": {
                "run_mode": run_mode,
                "output_dir": str(output_dir),
                "effective_epochs": eff_epochs,
                "effective_batch_size": eff_batch_size,
                "train_samples": int(len(y_train)),
                "val_samples": int(len(y_val)),
                "eval_samples": int(len(y_eval)),
                "noise_files": int(len(noise_files)),
            },
        }
    )
    write_json(output_dir / "run_config.json", run_config)
    write_json(output_dir / "source_manifest.json", source_manifest({"run_mode": run_mode, "baseline": baseline}))

    model = build_model_from_config(config)
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=float(train_cfg["learning_rate"])),
        loss=str(train_cfg["loss"]),
        metrics=[str(train_cfg["metric"])],
    )

    checkpoint_path = output_dir / "checkpoints" / "best.weights.h5"
    if run_mode == "tiny-train":
        x_train_feat, y_train_oh, _ = _materialize_feature_arrays(
            x_train,
            y_train,
            num_classes=len(class_names),
            frontend_type=frontend_type,
            noise_files=noise_files,
            rng_seed=seed,
            is_training=True,
            noise_mix_prob=noise_cfg["noise_mix_prob"],
            min_snr_db=noise_cfg["min_snr_db"],
            max_snr_db=noise_cfg["max_snr_db"],
            eval_snr_db=noise_cfg["eval_snr_db"],
        )
        x_val_feat, y_val_oh, _ = _materialize_feature_arrays(
            x_val,
            y_val,
            num_classes=len(class_names),
            frontend_type=frontend_type,
            noise_files=noise_files,
            rng_seed=seed + 1,
            is_training=False,
            noise_mix_prob=1.0,
            min_snr_db=noise_cfg["min_snr_db"],
            max_snr_db=noise_cfg["max_snr_db"],
            eval_snr_db=noise_cfg["eval_snr_db"],
        )
        x_eval_feat, _, y_true = _materialize_feature_arrays(
            x_eval,
            y_eval,
            num_classes=len(class_names),
            frontend_type=frontend_type,
            noise_files=noise_files,
            rng_seed=seed + 2,
            is_training=False,
            noise_mix_prob=1.0,
            min_snr_db=noise_cfg["min_snr_db"],
            max_snr_db=noise_cfg["max_snr_db"],
            eval_snr_db=noise_cfg["eval_snr_db"],
        )
        history = _manual_tiny_fit(
            tf,
            model,
            model.optimizer,
            x_train_feat,
            y_train_oh,
            x_val_feat,
            y_val_oh,
            eff_epochs,
            eff_batch_size,
            checkpoint_path,
        )
    else:
        FeatureSequence = _make_sequence_class(tf)
        train_seq = FeatureSequence(
            x_train,
            y_train,
            eff_batch_size,
            len(class_names),
            frontend_type,
            noise_files,
            seed,
            True,
            noise_cfg["noise_mix_prob"],
            noise_cfg["min_snr_db"],
            noise_cfg["max_snr_db"],
            noise_cfg["eval_snr_db"],
        )
        val_seq = FeatureSequence(
            x_val,
            y_val,
            eff_batch_size,
            len(class_names),
            frontend_type,
            noise_files,
            seed + 1,
            False,
            1.0,
            noise_cfg["min_snr_db"],
            noise_cfg["max_snr_db"],
            noise_cfg["eval_snr_db"],
        )
        eval_seq = FeatureSequence(
            x_eval,
            y_eval,
            eff_batch_size,
            len(class_names),
            frontend_type,
            noise_files,
            seed + 2,
            False,
            1.0,
            noise_cfg["min_snr_db"],
            noise_cfg["max_snr_db"],
            noise_cfg["eval_snr_db"],
        )
        history = _manual_sequence_fit(
            tf,
            model,
            model.optimizer,
            train_seq,
            val_seq,
            eff_epochs,
            checkpoint_path,
            int(train_cfg["earlystop_patience"]),
        )
    _write_history_csv(history, output_dir / "history" / "train_history.csv")
    if checkpoint_path.exists():
        model.load_weights(str(checkpoint_path))

    if run_mode == "tiny-train":
        probabilities = model(tf.convert_to_tensor(x_eval_feat, dtype=tf.float32), training=False).numpy()
        y_pred = np.argmax(probabilities, axis=1)
    else:
        probabilities = model.predict(eval_seq, verbose=0)
        y_pred = np.argmax(probabilities, axis=1)
        y_true = eval_seq.ordered_true_labels()
    report_text = classification_report_text(y_true, y_pred, class_names)
    write_text(output_dir / "classification_report_noisy.txt", report_text)
    metrics = metrics_dict(y_true, y_pred, class_names)
    write_json(output_dir / "metrics.json", _jsonable(metrics))
    save_confusion_matrix(y_true, y_pred, class_names, output_dir)

    tree_text = result_tree(output_dir)
    write_text(output_dir / "receipts" / "result_tree.txt", tree_text + "\n")

    completion_lines = [
        "Track D offline baseline completion receipt",
        f"run_mode={run_mode}",
        f"baseline={baseline}",
        f"checkpoint={checkpoint_path}",
        f"classification_report={output_dir / 'classification_report_noisy.txt'}",
        f"metrics={output_dir / 'metrics.json'}",
        f"accuracy={metrics['accuracy']:.6f}",
        f"macro_f1={metrics['macro_f1']:.6f}",
        "result_tree:",
        *tree_text.splitlines(),
    ]
    write_text(output_dir / "receipts" / "completion_last50.txt", "\n".join(completion_lines[-50:]) + "\n")
    final_tree_text = result_tree(output_dir)
    write_text(output_dir / "receipts" / "result_tree.txt", final_tree_text + "\n")

    return {
        "baseline": baseline,
        "run_mode": run_mode,
        "output_dir": str(output_dir),
        "checkpoint": str(checkpoint_path),
        "accuracy": metrics["accuracy"],
        "macro_f1": metrics["macro_f1"],
        "classification_report": str(output_dir / "classification_report_noisy.txt"),
        "param_count": int(model.count_params()),
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Track D offline baseline runner.")
    parser.add_argument("--config", required=True, help="Path to a baseline YAML config.")
    parser.add_argument("--mode", default="smoke", choices=["smoke", "tiny-train", "train"])
    parser.add_argument("--check-data-loader", action="store_true")
    parser.add_argument("--output-root", default=None, help="Override output root for validation or server runs.")
    parser.add_argument("--allow-full-train", action="store_true", help="Required for --mode train.")
    parser.add_argument("--tiny-train-samples", type=int, default=12)
    parser.add_argument("--tiny-val-samples", type=int, default=6)
    parser.add_argument("--tiny-eval-samples", type=int, default=6)
    parser.add_argument("--tiny-epochs", type=int, default=1)
    parser.add_argument("--tiny-batch-size", type=int, default=3)
    return parser
