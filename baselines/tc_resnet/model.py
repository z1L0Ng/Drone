"""Minimal project-local TCResNet8-style model."""

from __future__ import annotations

from tensorflow import keras
from tensorflow.keras import layers


def _to_time_sequence(inputs):
    freq_bins = int(inputs.shape[1])
    time_frames = int(inputs.shape[2])
    x = layers.Permute((2, 1, 3), name="freq_time_to_time_freq")(inputs)
    return layers.Reshape((time_frames, freq_bins), name="time_sequence")(x)


def _tc_block(x, filters: int, kernel_size: int, block_name: str):
    shortcut = x
    if int(shortcut.shape[-1]) != filters:
        shortcut = layers.Conv1D(filters, 1, padding="same", use_bias=False, name=f"{block_name}_shortcut_conv")(shortcut)
        shortcut = layers.BatchNormalization(name=f"{block_name}_shortcut_bn")(shortcut)

    y = layers.Conv1D(filters, kernel_size, padding="same", use_bias=False, name=f"{block_name}_conv1")(x)
    y = layers.BatchNormalization(name=f"{block_name}_bn1")(y)
    y = layers.Activation("relu", name=f"{block_name}_relu1")(y)
    y = layers.Conv1D(filters, kernel_size, padding="same", use_bias=False, name=f"{block_name}_conv2")(y)
    y = layers.BatchNormalization(name=f"{block_name}_bn2")(y)
    y = layers.Add(name=f"{block_name}_add")([shortcut, y])
    return layers.Activation("relu", name=f"{block_name}_out")(y)


def build_tcresnet8(
    input_shape=(256, 32, 1),
    num_classes: int = 3,
    channels=(16, 24, 32, 48),
    kernel_size: int = 9,
    dropout_rate: float = 0.10,
) -> keras.Model:
    inputs = keras.Input(shape=tuple(input_shape), name="features")
    x = _to_time_sequence(inputs)
    for idx, filters in enumerate(channels, start=1):
        x = _tc_block(x, int(filters), int(kernel_size), f"tc_block{idx}")
    x = layers.GlobalAveragePooling1D(name="global_pool")(x)
    x = layers.Dropout(dropout_rate, name="dropout")(x)
    outputs = layers.Dense(num_classes, activation="softmax", name="intent")(x)
    return keras.Model(inputs, outputs, name="tcresnet8_trackd")
