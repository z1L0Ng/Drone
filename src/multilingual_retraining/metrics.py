"""Unified three-class and calibration metrics for persisted predictions."""

from __future__ import annotations

import math
from collections import Counter
from typing import Any, Dict, Mapping, Sequence

import numpy as np

from .contracts import LABELS, METRICS_SCHEMA


class MetricsError(ValueError):
    """Raised when prediction arrays do not satisfy the metric contract."""


def _safe_rate(numerator: int, denominator: int) -> float | None:
    return None if denominator == 0 else float(numerator / denominator)


def _class_metrics(y_true: np.ndarray, y_pred: np.ndarray, class_index: int) -> Dict[str, Any]:
    tp = int(np.sum((y_true == class_index) & (y_pred == class_index)))
    fp = int(np.sum((y_true != class_index) & (y_pred == class_index)))
    fn = int(np.sum((y_true == class_index) & (y_pred != class_index)))
    support = int(np.sum(y_true == class_index))
    precision = _safe_rate(tp, tp + fp)
    recall = _safe_rate(tp, support)
    if precision is None or recall is None or precision + recall == 0:
        f1 = None if support == 0 else 0.0
    else:
        f1 = 2.0 * precision * recall / (precision + recall)
    return {
        "support": support,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def expected_calibration_error(probabilities: np.ndarray, y_true: np.ndarray, bins: int) -> Dict[str, Any]:
    confidence = np.max(probabilities, axis=1)
    prediction = np.argmax(probabilities, axis=1)
    correct = prediction == y_true
    edges = np.linspace(0.0, 1.0, bins + 1)
    rows = []
    ece = 0.0
    for index in range(bins):
        lower = float(edges[index])
        upper = float(edges[index + 1])
        mask = (confidence >= lower) & (confidence < upper if index < bins - 1 else confidence <= upper)
        count = int(np.sum(mask))
        mean_confidence = None if count == 0 else float(np.mean(confidence[mask]))
        accuracy = None if count == 0 else float(np.mean(correct[mask]))
        if count:
            ece += count / len(y_true) * abs(mean_confidence - accuracy)
        rows.append(
            {
                "bin": index,
                "lower": lower,
                "upper": upper,
                "count": count,
                "mean_confidence": mean_confidence,
                "accuracy": accuracy,
            }
        )
    return {"bins": bins, "value": float(ece), "reliability": rows}


def compute_metrics(
    y_true: Sequence[int],
    probabilities: Sequence[Sequence[float]],
    languages: Sequence[str],
    ece_bins: int = 15,
) -> Dict[str, Any]:
    truth = np.asarray(y_true, dtype=np.int64)
    probs = np.asarray(probabilities, dtype=np.float64)
    language_array = np.asarray(languages, dtype=object)
    if truth.ndim != 1 or probs.shape != (len(truth), len(LABELS)):
        raise MetricsError(f"expected probabilities shape {(len(truth), len(LABELS))}, got {probs.shape}")
    if language_array.shape != truth.shape:
        raise MetricsError("languages must have one value per prediction")
    if len(truth) == 0 or not np.all(np.isfinite(probs)):
        raise MetricsError("predictions must be non-empty and finite")
    if np.any(probs < 0.0) or not np.allclose(np.sum(probs, axis=1), 1.0, atol=1e-6):
        raise MetricsError("probabilities must be normalized")
    if np.any(truth < 0) or np.any(truth >= len(LABELS)):
        raise MetricsError("y_true contains an invalid label index")

    prediction = np.argmax(probs, axis=1)
    per_class = {
        label: _class_metrics(truth, prediction, index)
        for index, label in enumerate(LABELS)
    }
    defined_f1 = [value["f1"] for value in per_class.values() if value["f1"] is not None]
    macro_f1 = float(np.mean(defined_f1)) if defined_f1 else None
    clipped = np.clip(probs[np.arange(len(truth)), truth], 1e-12, 1.0)
    nll = float(-np.mean(np.log(clipped)))
    target = np.eye(len(LABELS), dtype=np.float64)[truth]
    brier = float(np.mean(np.sum((probs - target) ** 2, axis=1)))

    emergency = 0
    movement = 1
    unknown = 2
    non_emergency = truth != emergency
    false_emergency_count = int(np.sum(non_emergency & (prediction == emergency)))
    unknown_mask = truth == unknown
    unknown_false_emergency_count = int(np.sum(unknown_mask & (prediction == emergency)))

    language_class: Dict[str, Any] = {}
    for language in sorted(set(str(value) for value in language_array)):
        language_mask = language_array == language
        language_truth = truth[language_mask]
        language_prediction = prediction[language_mask]
        for index, label in enumerate(LABELS):
            values = _class_metrics(language_truth, language_prediction, index)
            true_class_mask = language_mask & (truth == index)
            values["false_emergency_count"] = int(np.sum(true_class_mask & (prediction == emergency)))
            language_class[f"{language}|{label}"] = values

    return {
        "schema_version": METRICS_SCHEMA,
        "label_order": list(LABELS),
        "support": int(len(truth)),
        "per_class": per_class,
        "per_language_class": language_class,
        "macro_f1": macro_f1,
        "emergency_recall": per_class["emergency"]["recall"],
        "unknown_recall": per_class["unknown"]["recall"],
        "false_emergency": {
            "count": false_emergency_count,
            "denominator": int(np.sum(non_emergency)),
            "rate": _safe_rate(false_emergency_count, int(np.sum(non_emergency))),
        },
        "unknown_false_emergency": {
            "count": unknown_false_emergency_count,
            "denominator": int(np.sum(unknown_mask)),
            "rate": _safe_rate(unknown_false_emergency_count, int(np.sum(unknown_mask))),
        },
        "nll": nll,
        "brier": brier,
        "ece": expected_calibration_error(probs, truth, ece_bins),
    }


def temperature_scale(probabilities: np.ndarray, temperature: float) -> np.ndarray:
    if not math.isfinite(temperature) or temperature <= 0:
        raise MetricsError("temperature must be finite and positive")
    probs = np.asarray(probabilities, dtype=np.float64)
    logits = np.log(np.clip(probs, 1e-12, 1.0)) / temperature
    logits -= np.max(logits, axis=1, keepdims=True)
    exp = np.exp(logits)
    return exp / np.sum(exp, axis=1, keepdims=True)


def fit_temperature(probabilities: np.ndarray, y_true: np.ndarray) -> Dict[str, Any]:
    from scipy.optimize import minimize_scalar

    probs = np.asarray(probabilities, dtype=np.float64)
    truth = np.asarray(y_true, dtype=np.int64)

    def objective(value: float) -> float:
        calibrated = temperature_scale(probs, value)
        correct = np.clip(calibrated[np.arange(len(truth)), truth], 1e-12, 1.0)
        return float(-np.mean(np.log(correct)))

    result = minimize_scalar(objective, bounds=(0.05, 10.0), method="bounded")
    if not result.success:
        raise MetricsError(f"temperature fitting failed: {result.message}")
    return {
        "method": "scalar_temperature_nll",
        "temperature": float(result.x),
        "validation_nll": float(result.fun),
        "bounds": [0.05, 10.0],
        "optimizer": "scipy.optimize.minimize_scalar_bounded",
    }
