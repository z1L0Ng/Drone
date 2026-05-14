"""Adapter from Track D config to TC-ResNet model."""

from __future__ import annotations

from .model import build_tcresnet8


def build_from_config(config: dict):
    return build_tcresnet8(
        input_shape=tuple(config.get("input_shape", (256, 32, 1))),
        num_classes=int(config.get("num_classes", 3)),
        channels=tuple(config.get("channels", (16, 24, 32, 48))),
        kernel_size=int(config.get("kernel_size", 9)),
        dropout_rate=float(config.get("dropout_rate", 0.10)),
    )
