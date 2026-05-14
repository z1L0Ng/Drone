"""Minimal project-local BC-ResNet-style model.

This is a compact Keras skeleton for same-split offline comparison. It is not
vendored from the upstream Qualcomm implementation.
"""

from __future__ import annotations

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers


def _conv_bn_relu(x, filters: int, kernel_size, strides=(1, 1), name: str = "conv"):
    x = layers.Conv2D(filters, kernel_size, strides=strides, padding="same", use_bias=False, name=f"{name}_conv")(x)
    x = layers.BatchNormalization(name=f"{name}_bn")(x)
    return layers.Activation("relu", name=f"{name}_relu")(x)


def _broadcast_block(x, filters: int, stride_freq: int, block_name: str):
    shortcut = x
    if int(shortcut.shape[-1]) != filters or stride_freq != 1:
        shortcut = layers.Conv2D(
            filters,
            kernel_size=(1, 1),
            strides=(stride_freq, 1),
            padding="same",
            use_bias=False,
            name=f"{block_name}_shortcut_conv",
        )(shortcut)
        shortcut = layers.BatchNormalization(name=f"{block_name}_shortcut_bn")(shortcut)

    y = _conv_bn_relu(x, filters, (3, 3), strides=(stride_freq, 1), name=f"{block_name}_main1")
    context = layers.Lambda(lambda t: tf.reduce_mean(t, axis=1, keepdims=True), name=f"{block_name}_freq_mean")(y)
    context = layers.Conv2D(filters, (1, 3), padding="same", activation="sigmoid", name=f"{block_name}_context")(context)
    y = layers.Multiply(name=f"{block_name}_broadcast_gate")([y, context])
    y = layers.Conv2D(filters, (3, 3), padding="same", use_bias=False, name=f"{block_name}_main2_conv")(y)
    y = layers.BatchNormalization(name=f"{block_name}_main2_bn")(y)
    y = layers.Add(name=f"{block_name}_add")([shortcut, y])
    return layers.Activation("relu", name=f"{block_name}_out")(y)


def build_bcresnet1(
    input_shape=(256, 32, 1),
    num_classes: int = 3,
    base_filters: int = 16,
    width_multiplier: float = 1.0,
    dropout_rate: float = 0.10,
) -> keras.Model:
    filters = max(8, int(round(base_filters * width_multiplier)))
    inputs = keras.Input(shape=tuple(input_shape), name="features")
    x = _conv_bn_relu(inputs, filters, (5, 3), name="stem")
    x = _broadcast_block(x, filters, 1, "bc_block1")
    x = _broadcast_block(x, filters * 2, 2, "bc_block2")
    x = _broadcast_block(x, filters * 2, 1, "bc_block3")
    x = _broadcast_block(x, filters * 4, 2, "bc_block4")
    x = layers.GlobalAveragePooling2D(name="global_pool")(x)
    x = layers.Dropout(dropout_rate, name="dropout")(x)
    outputs = layers.Dense(num_classes, activation="softmax", name="intent")(x)
    return keras.Model(inputs, outputs, name="bcresnet1_trackd")
