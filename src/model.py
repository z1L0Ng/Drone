# src/model.py

import tensorflow as tf
from keras.models import Model
from keras.layers import (
    Input, Conv2D, BatchNormalization, Activation, MaxPooling2D, Dropout,
    Permute, Reshape, Dense, LayerNormalization, Add, MultiHeadAttention,
    GlobalAveragePooling1D, DepthwiseConv1D, Multiply, Lambda, Conv1D, Concatenate
)

# 这个设计是正确的，保持不变
def branchformer_block(x, head_size, num_heads, ff_dim, input_feature_dim, dropout=0.1, kernel_size=31, block_idx=0):
    """A single Branchformer block."""
    prefix = f"branchformer{block_idx}"

    # FFN Module (first half)
    ff1 = Dense(ff_dim, activation='relu', name=f"{prefix}_ff1_dense1")(x)
    ff1 = Dropout(dropout, name=f"{prefix}_ff1_dropout")(ff1)
    ff1 = Dense(input_feature_dim, name=f"{prefix}_ff1_dense2")(ff1)
    x = Add(name=f"{prefix}_ff1_add")([x, Lambda(lambda z: 0.5 * z)(ff1)])

    # Multi-Head Attention Branch
    x_ln_attn = LayerNormalization(epsilon=1e-6, name=f"{prefix}_attn_ln")(x)
    attn_out = MultiHeadAttention(
        num_heads=num_heads,
        key_dim=head_size,
        dropout=dropout,
        name=f"{prefix}_mha"
    )(x_ln_attn, x_ln_attn)
    attn_out = Dropout(dropout, name=f"{prefix}_attn_dropout")(attn_out)
    cg_attn = Add(name=f"{prefix}_attn_add")([x, attn_out])

    # Convolutional Branch
    x_ln_conv = LayerNormalization(epsilon=1e-6, name=f"{prefix}_conv_ln")(x)
    
    conv_gates = Conv1D(input_feature_dim, kernel_size=1, activation='sigmoid', name=f"{prefix}_conv_gate")(x_ln_conv)
    conv_in = Conv1D(input_feature_dim, kernel_size=1, name=f"{prefix}_conv_in")(x_ln_conv)
    conv_in = Multiply(name=f"{prefix}_conv_glu")([conv_in, conv_gates])
    
    conv_in = Conv1D(input_feature_dim, kernel_size, padding='same', groups=input_feature_dim, name=f"{prefix}_conv_dwise")(conv_in)
    conv_in = BatchNormalization(name=f"{prefix}_conv_bn")(conv_in)
    conv_in = Activation('swish', name=f"{prefix}_conv_swish")(conv_in)
    
    conv_out = Conv1D(input_feature_dim, kernel_size=1, name=f"{prefix}_conv_pwise")(conv_in)
    conv_out = Dropout(dropout, name=f"{prefix}_conv_dropout")(conv_out)
    cg_conv = Add(name=f"{prefix}_conv_add")([x, conv_out])

    # Merge branches
    x = Add(name=f"{prefix}_merge_add")([cg_attn, cg_conv])
    x_ln = LayerNormalization(epsilon=1e-6, name=f"{prefix}_merge_ln")(x)
    
    # FFN Module (second half)
    ff2 = Dense(ff_dim, activation='swish', name=f"{prefix}_ff2_dense1")(x_ln)
    ff2 = Dropout(dropout, name=f"{prefix}_ff2_dropout")(ff2)
    ff2 = Dense(input_feature_dim, name=f"{prefix}_ff2_dense2")(ff2)
    x = Add(name=f"{prefix}_ff2_add")([x, Lambda(lambda z: 0.5 * z)(ff2)])
    
    x = LayerNormalization(epsilon=1e-6, name=f"{prefix}_ln_out")(x)
    return x

def build_model(
    input_shape,
    num_classes,
    num_layers=1,
    head_size=32,
    num_heads=4,
    ff_dim=256,
    dropout_rate=0.15,
    fnn_units=[128],
    use_stats_branch=False,
    stats_dim=4,
    stats_mlp_units=(32, 16),
    fuse_units=128,
    fusion_mode="concat",
    gate_units=16,
):
    """Builds the full ResNet-Branchformer model."""
    spec_input = Input(shape=input_shape)

    # ResNet part (Feature Extractor)
    x = Conv2D(filters=64, kernel_size=(3, 3), padding='same')(spec_input)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)
    x = MaxPooling2D(pool_size=(4, 1))(x)

    x = Conv2D(filters=64, kernel_size=(3, 3), padding='same')(x)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)
    x = MaxPooling2D(pool_size=(4, 1))(x)

    x = Conv2D(filters=64, kernel_size=(3, 3), padding='same')(x)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)
    x = MaxPooling2D(pool_size=(2, 1))(x)
    
    # === 【最终修正】: 使用 Keras 自身机制进行动态 Reshape ===
    # Permute 2D feature map to a sequence for the Branchformer
    # 交换维度，使时间维度在前 -> (Batch, Time, Freq, Channels)
    x = Permute((2, 1, 3))(x)

    # 获取当前 Keras 张量的静态形状信息
    # x.shape is a tuple like (None, time_steps, freq_bins, channels)
    # 我们希望的新形状是 (time_steps, freq_bins * channels)
    # Reshape 层中的 -1 是一个强大的工具，它告诉 Keras 自动计算这个维度的大小
    # target_shape 的第一个维度是时间步，可以直接从 x.shape[1] 获取
    time_steps = x.shape[1]
    
    # Reshape 层会自动将最后两个维度 (Freq, Channels) 合并
    x = Reshape((time_steps, -1))(x)
    
    # 动态获取特征维度，用于传递给 Branchformer Block
    # Reshape 之后，x.shape[-1] 就代表了 Freq * Channels
    feature_dim = x.shape[-1]

    # Branchformer part
    for i in range(num_layers):
        x = branchformer_block(
            x, head_size, num_heads, ff_dim, 
            input_feature_dim=feature_dim, # 将动态计算的维度传入
            dropout=dropout_rate, 
            block_idx=i
        )

    # Classification Head (mel branch)
    x = GlobalAveragePooling1D()(x)
    for units in fnn_units:
        x = Dense(units, activation='relu')(x)
        x = Dropout(dropout_rate)(x)

    mel_embed = Lambda(lambda z: z, name="mel_embed")(x)

    if use_stats_branch:
        stats_input = Input(shape=(int(stats_dim),), name="stats_input")
        s = stats_input
        if isinstance(stats_mlp_units, int):
            stats_mlp_units = (stats_mlp_units,)
        for i, units in enumerate(stats_mlp_units):
            if int(units) <= 0:
                continue
            s = Dense(int(units), activation="relu", name=f"stats_mlp_dense_{i + 1}")(s)
            s = Dropout(dropout_rate, name=f"stats_mlp_dropout_{i + 1}")(s)
        stats_embed = Lambda(lambda z: z, name="stats_embed")(s)

        fusion_mode = str(fusion_mode).strip().lower()
        if fusion_mode not in {"concat", "gated"}:
            raise ValueError(f"Unsupported fusion_mode={fusion_mode}, expected one of: concat, gated")

        if fusion_mode == "gated":
            gate_in = stats_embed
            if int(gate_units) > 0:
                gate_in = Dense(int(gate_units), activation="relu", name="gate_mlp_dense")(gate_in)
            stats_embed_dim = stats_embed.shape[-1]
            if stats_embed_dim is None:
                stats_embed_dim = int(stats_dim)
            stats_gate = Dense(int(stats_embed_dim), activation="sigmoid", name="stats_gate")(gate_in)
            gated_stats = Multiply(name="gated_stats")([stats_embed, stats_gate])
            fused_input = Concatenate(name="fusion_concat")([mel_embed, gated_stats])
        else:
            fused_input = Concatenate(name="fusion_concat")([mel_embed, stats_embed])

        fused = Dense(int(fuse_units), activation="relu", name="fusion_dense")(fused_input)
        fused = Dropout(dropout_rate, name="fusion_dropout")(fused)
        fused = Lambda(lambda z: z, name="fused_embed")(fused)
        outputs = Dense(num_classes, activation="softmax", name="class_output")(fused)
        return Model(inputs=[spec_input, stats_input], outputs=outputs)

    fused = Lambda(lambda z: z, name="fused_embed")(mel_embed)
    outputs = Dense(num_classes, activation="softmax", name="class_output")(fused)
    return Model(inputs=spec_input, outputs=outputs)
