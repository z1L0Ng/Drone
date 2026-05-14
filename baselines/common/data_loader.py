"""Project data split, labels, and optional batch adapter."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import joblib
import numpy as np

from .constants import ENCODER_PATH, LABELS, PROCESSED_DATA_PATH


@dataclass(frozen=True)
class SplitData:
    x_train: np.ndarray
    y_train: np.ndarray
    x_val: np.ndarray
    y_val: np.ndarray
    x_test: np.ndarray
    y_test: np.ndarray


def load_split(processed_data_path: str | Path = PROCESSED_DATA_PATH) -> SplitData:
    data = np.load(str(processed_data_path), allow_pickle=True)
    required = ("X_train", "y_train", "X_val", "y_val", "X_test", "y_test")
    missing = [key for key in required if key not in data.files]
    if missing:
        raise KeyError(f"Missing keys in {processed_data_path}: {missing}")
    return SplitData(
        x_train=np.asarray(data["X_train"]),
        y_train=np.asarray(data["y_train"], dtype=np.int64),
        x_val=np.asarray(data["X_val"]),
        y_val=np.asarray(data["y_val"], dtype=np.int64),
        x_test=np.asarray(data["X_test"]),
        y_test=np.asarray(data["y_test"], dtype=np.int64),
    )


def load_label_encoder(encoder_path: str | Path = ENCODER_PATH):
    return joblib.load(str(encoder_path))


def load_class_names(encoder_path: str | Path = ENCODER_PATH) -> list[str]:
    encoder = load_label_encoder(encoder_path)
    return [str(v) for v in encoder.classes_]


def validate_label_contract(class_names: Iterable[str]) -> None:
    observed = tuple(str(v) for v in class_names)
    if observed != LABELS:
        raise ValueError(f"Expected labels {LABELS}, observed {observed}")


def tiny_data_loader_check(
    processed_data_path: str | Path = PROCESSED_DATA_PATH,
    encoder_path: str | Path = ENCODER_PATH,
) -> dict[str, object]:
    split = load_split(processed_data_path)
    class_names = load_class_names(encoder_path)
    validate_label_contract(class_names)
    return {
        "class_names": class_names,
        "n_train": int(split.x_train.shape[0]),
        "n_val": int(split.x_val.shape[0]),
        "n_test": int(split.x_test.shape[0]),
        "first_train_path": str(split.x_train[0]) if split.x_train.size else "",
        "first_train_label": int(split.y_train[0]) if split.y_train.size else -1,
    }
