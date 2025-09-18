import tensorflow as tf
from keras.models import Model
from keras.layers import (
    Input, Conv2D, BatchNormalization, Activation, MaxPooling2D, Dropout,
    Permute, Reshape, Dense, LayerNormalization, Add, MultiHeadAttention,
    GlobalAveragePooling1D, DepthwiseConv1D, Multiply, Lambda, Conv1D
)

def branchformer_block(x, head_size, num_heads, ff_dim, dropout=0.1, kernel_size=31, block_idx=0):
    """A single Branchformer block."""
    prefix = f"branchformer{block_idx}"
    ff1 = Dense(ff_dim, activation='relu', name=f"{prefix}_ff1_dense1")(x)
    ff1 = Dropout(dropout, name=f"{prefix}_ff1_dropout")(ff1)
    ff1 = Dense(x.shape[-1], name=f"{prefix}_ff1_dense2")(ff1)
    x = Add(name=f"{prefix}_ff1_add")([x, Lambda(lambda z: 0.5 * z)(ff1)])
    x_ln_attn = LayerNormalization(epsilon=1e-6, name=f"{prefix}_attn_ln")(x)
    attn_out = MultiHeadAttention(num_heads=num_heads, key_dim=head_size, dropout=dropout, name=f"{prefix}_attn")(x_ln_attn, x_ln_attn)
    attn_out = Dropout(dropout, name=f"{prefix}_attn_dropout")(attn_out)
    conv_input = LayerNormalization(epsilon=1e-6, name=f"{prefix}_conv_ln")(x)
    conv_u = Conv1D(filters=x.shape[-1], kernel_size=1, padding='same', name=f"{prefix}_conv_u")(conv_input)
    conv_v = Conv1D(filters=x.shape[-1], kernel_size=1, padding='same', activation='sigmoid', name=f"{prefix}_conv_v")(conv_input)
    conv_glu = Multiply(name=f"{prefix}_glu_out")([conv_u, conv_v])
    conv_dw = DepthwiseConv1D(kernel_size=kernel_size, padding='same', name=f"{prefix}_depthwise")(conv_glu)
    conv_dw = BatchNormalization(name=f"{prefix}_dw_bn")(conv_dw)
    conv_dw = Activation('swish', name=f"{prefix}_swish")(conv_dw)
    conv_out = Conv1D(filters=x.shape[-1], kernel_size=1, padding='same', name=f"{prefix}_conv_pw2")(conv_dw)
    conv_out = Dropout(dropout, name=f"{prefix}_conv_dropout")(conv_out)
    merged = Add(name=f"{prefix}_merge")([attn_out, conv_out])
    x = Add(name=f"{prefix}_residual_merge")([x, merged])
    ff2 = Dense(ff_dim, activation='relu', name=f"{prefix}_ff2_dense1")(x)
    ff2 = Dropout(dropout, name=f"{prefix}_ff2_dropout")(ff2)
    ff2 = Dense(x.shape[-1], name=f"{prefix}_ff2_dense2")(ff2)
    x = Add(name=f"{prefix}_ff2_add")([x, Lambda(lambda z: 0.5 * z)(ff2)])
    x = LayerNormalization(epsilon=1e-6, name=f"{prefix}_ln_out")(x)
    return x

def build_model(input_shape, num_classes, num_layers=1, head_size=32, num_heads=4, ff_dim=256, dropout_rate=0.15, fnn_units=[128]):
    """Builds the full ResNet-Conformer model."""
    spec_input = Input(shape=input_shape)

    # ResNet part
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
    
    # Reshape 2D feature map to a sequence for the Branchformer
    x = Permute((2, 1, 3))(x)
    
    # *** 关键修改：使用静态、确定的形状进行 Reshape ***
    # 原始形状: (None, 61, 8, 64) -> 目标形状: (None, 61, 512)
    x = Reshape((61, 8 * 64))(x)

    # Branchformer part
    for i in range(num_layers):
        x = branchformer_block(x, head_size=head_size, num_heads=num_heads, ff_dim=ff_dim, dropout=dropout_rate, block_idx=i)

    x = GlobalAveragePooling1D(name='embedding_output')(x)

    # Output classification head
    x = Dense(fnn_units[0], activation='relu', name="final_dense")(x)
    x = Dropout(dropout_rate, name="final_dropout")(x)
    output = Dense(num_classes, activation='softmax', name='output')(x)

    model = Model(inputs=spec_input, outputs=output)
    return model