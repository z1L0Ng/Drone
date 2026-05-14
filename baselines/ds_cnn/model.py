"""Minimal project-local DS-CNN-S-style model."""

from __future__ import annotations

from tensorflow import keras
from tensorflow.keras import layers


def _ds_block(x, pointwise_filters: int, block_name: str):
    x = layers.DepthwiseConv2D((3, 3), padding="same", use_bias=False, name=f"{block_name}_dwconv")(x)
    x = layers.BatchNormalization(name=f"{block_name}_dwbn")(x)
    x = layers.Activation("relu", name=f"{block_name}_dwrelu")(x)
    x = layers.Conv2D(pointwise_filters, (1, 1), padding="same", use_bias=False, name=f"{block_name}_pwconv")(x)
    x = layers.BatchNormalization(name=f"{block_name}_pwbn")(x)
    return layers.Activation("relu", name=f"{block_name}_pwrelu")(x)


def build_dscnn_s(
    input_shape=(256, 32, 1),
    num_classes: int = 3,
    stem_filters: int = 32,
    depthwise_blocks: int = 4,
    pointwise_filters: int = 64,
    dropout_rate: float = 0.10,
) -> keras.Model:
    inputs = keras.Input(shape=tuple(input_shape), name="features")
    x = layers.Conv2D(stem_filters, (10, 4), strides=(2, 1), padding="same", use_bias=False, name="stem_conv")(inputs)
    x = layers.BatchNormalization(name="stem_bn")(x)
    x = layers.Activation("relu", name="stem_relu")(x)
    for idx in range(int(depthwise_blocks)):
        x = _ds_block(x, int(pointwise_filters), f"ds_block{idx + 1}")
    x = layers.GlobalAveragePooling2D(name="global_pool")(x)
    x = layers.Dropout(dropout_rate, name="dropout")(x)
    outputs = layers.Dense(num_classes, activation="softmax", name="intent")(x)
    return keras.Model(inputs, outputs, name="dscnn_s_trackd")
