"""Adapter from Track D config to BC-ResNet model."""

from __future__ import annotations

from .model import build_bcresnet1


def build_from_config(config: dict):
    return build_bcresnet1(
        input_shape=tuple(config.get("input_shape", (256, 32, 1))),
        num_classes=int(config.get("num_classes", 3)),
        base_filters=int(config.get("base_filters", 16)),
        width_multiplier=float(config.get("width_multiplier", 1.0)),
        dropout_rate=float(config.get("dropout_rate", 0.10)),
    )
