"""Adapter from Track D config to DS-CNN model."""

from __future__ import annotations

from .model import build_dscnn_s


def build_from_config(config: dict):
    return build_dscnn_s(
        input_shape=tuple(config.get("input_shape", (256, 32, 1))),
        num_classes=int(config.get("num_classes", 3)),
        stem_filters=int(config.get("stem_filters", 32)),
        depthwise_blocks=int(config.get("depthwise_blocks", 4)),
        pointwise_filters=int(config.get("pointwise_filters", 64)),
        dropout_rate=float(config.get("dropout_rate", 0.10)),
    )
