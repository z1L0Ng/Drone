# src/train.py

import os
import numpy as np
import tensorflow as tf
import librosa
from model import build_model
from keras.optimizers import Adam
from keras.callbacks import ModelCheckpoint, EarlyStopping
import matplotlib.pyplot as plt

# --- 1. 定义路径和参数 ---
PROCESSED_DATA_PATH = "dataset/processed/data_paths.npz"
MODELS_PATH = "saved_models/"
HISTORY_PATH = "saved_models/training_history.npy"
PLOT_PATH = "result/training_history.png"

# 确保目录存在
os.makedirs("result", exist_ok=True)
os.makedirs(MODELS_PATH, exist_ok=True)

# 训练参数
EPOCHS = 50
BATCH_SIZE = 32
LEARNING_RATE = 0.0001

# 音频处理参数
SAMPLE_RATE = 16000 # 采样率
DURATION = 2       # 音频时长（秒）
N_MELS = 128       # Mel Spectrogram 的频带数
# 根据librosa的帧计算方式 (n_fft - hop_length) // hop_length + 1，这里用一个通用估算
# hop_length 通常是 n_fft // 4，这里假设 n_fft=2048, hop_length=512
MAX_FRAMES = int(DURATION * SAMPLE_RATE / 512) + 1 # 帧数，用于统一输入尺寸

# --- 2. 数据生成器 (DataGenerator) ---
class DataGenerator(tf.keras.utils.Sequence):
    """
    为Keras模型动态生成数据的工具。
    它会在每个epoch中对数据进行实时增强。
    """
    def __init__(self, filepaths, labels, batch_size, num_classes, is_training=True):
        self.filepaths = filepaths
        self.labels = labels
        self.batch_size = batch_size
        self.num_classes = num_classes
        self.is_training = is_training # 决定是否进行数据增强
        self.on_epoch_end()

    def __len__(self):
        '返回每个epoch的批次数'
        return int(np.floor(len(self.filepaths) / self.batch_size))

    def __getitem__(self, index):
        '生成一个批次的数据'
        indexes = self.indexes[index*self.batch_size:(index+1)*self.batch_size]
        batch_filepaths = [self.filepaths[k] for k in indexes]
        batch_labels = [self.labels[k] for k in indexes]
        X, y = self.__data_generation(batch_filepaths, batch_labels)
        return X, y

    def on_epoch_end(self):
        '每个epoch结束后，打乱数据顺序'
        self.indexes = np.arange(len(self.filepaths))
        if self.is_training:
            np.random.shuffle(self.indexes)

    def _augment_audio(self, y):
        '对音频波形进行随机增强'
        if np.random.rand() < 0.5:
            rate = np.random.uniform(0.9, 1.1)
            y = librosa.effects.time_stretch(y=y, rate=rate)
        if np.random.rand() < 0.5:
            n_steps = np.random.randint(-2, 3)
            y = librosa.effects.pitch_shift(y=y, sr=SAMPLE_RATE, n_steps=n_steps)
        return y

    def _extract_features(self, y):
        '从音频波形提取Mel频谱图特征'
        mel_spec = librosa.feature.melspectrogram(y=y, sr=SAMPLE_RATE, n_mels=N_MELS)
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        
        if mel_spec_db.shape[1] < MAX_FRAMES:
            pad_width = MAX_FRAMES - mel_spec_db.shape[1]
            mel_spec_db = np.pad(mel_spec_db, ((0, 0), (0, pad_width)), mode='constant')
        else:
            mel_spec_db = mel_spec_db[:, :MAX_FRAMES]
        return mel_spec_db

    def __data_generation(self, batch_filepaths, batch_labels):
        '生成一个批次的特征和标签'
        X = np.empty((self.batch_size, N_MELS, MAX_FRAMES, 1))
        y = np.empty((self.batch_size), dtype=int)
        for i, filepath in enumerate(batch_filepaths):
            audio, _ = librosa.load(filepath, sr=SAMPLE_RATE, duration=DURATION)
            if len(audio) < DURATION * SAMPLE_RATE:
                 audio = np.pad(audio, (0, DURATION * SAMPLE_RATE - len(audio)))

            if self.is_training:
                audio = self._augment_audio(audio)
            
            features = self._extract_features(audio)
            X[i,] = np.expand_dims(features, axis=-1)
            y[i] = batch_labels[i]
        return X, tf.keras.utils.to_categorical(y, num_classes=self.num_classes)

# --- 3. 加载数据索引并创建生成器 ---
print("加载数据集索引...")
with np.load(PROCESSED_DATA_PATH, allow_pickle=True) as data:
    X_train_paths, y_train = data['X_train'], data['y_train']
    X_val_paths, y_val = data['X_val'], data['y_val']
    X_test_paths, y_test = data['X_test'], data['y_test']

NUM_CLASSES = len(np.unique(np.concatenate((y_train, y_val, y_test))))
INPUT_SHAPE = (N_MELS, MAX_FRAMES, 1)

print(f"类别数量: {NUM_CLASSES}")
print(f"模型输入尺寸: {INPUT_SHAPE}")

train_generator = DataGenerator(X_train_paths, y_train, BATCH_SIZE, NUM_CLASSES, is_training=True)
val_generator = DataGenerator(X_val_paths, y_val, BATCH_SIZE, NUM_CLASSES, is_training=False)
test_generator = DataGenerator(X_test_paths, y_test, BATCH_SIZE, NUM_CLASSES, is_training=False)

# --- 4. 构建、编译和训练模型 ---
model = build_model(input_shape=INPUT_SHAPE, num_classes=NUM_CLASSES)
model.compile(
    optimizer=Adam(learning_rate=LEARNING_RATE),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)
model.summary()

checkpoint_path = os.path.join(MODELS_PATH, "resnet_conformer_drone.keras")
model_checkpoint = ModelCheckpoint(
    filepath=checkpoint_path,
    save_best_only=True,
    monitor='val_accuracy',
    mode='max',
    verbose=1
)
early_stopping = EarlyStopping(
    monitor='val_accuracy',
    patience=10,
    verbose=1,
    restore_best_weights=True
)

# --- 5. 训练模型 ---
print("\n开始模型训练...")

# === 【关键修改】: 移除了在新版 Keras 中已弃用的 'workers' 和 'use_multiprocessing' 参数 ===
history = model.fit(
    train_generator,
    validation_data=val_generator,
    epochs=EPOCHS,
    callbacks=[model_checkpoint, early_stopping]
)
print("\n✅ 训练完成。")

# --- 6. 评估模型 ---
print("\n在测试集上评估模型性能...")
# 确保测试生成器不会因为批次大小不能整除而丢失样本
test_loss, test_accuracy = model.evaluate(test_generator, verbose=1)
print(f"测试集损失: {test_loss:.4f}")
print(f"测试集准确率: {test_accuracy:.4f}")

# --- 7. 保存和绘制训练历史 ---
print("\n保存训练历史并生成图表...")
np.save(HISTORY_PATH, history.history)
print(f"训练历史已保存至: {HISTORY_PATH}")

plt.style.use('seaborn-v0_8-whitegrid')
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
# 绘制准确率
ax1.plot(history.history['accuracy'])
ax1.plot(history.history['val_accuracy'])
ax1.set_title('Model Accuracy')
ax1.set_ylabel('Accuracy')
ax1.set_xlabel('Epoch')
ax1.legend(['Train', 'Validation'], loc='upper left')
# 绘制损失
ax2.plot(history.history['loss'])
ax2.plot(history.history['val_loss'])
ax2.set_title('Model Loss')
ax2.set_ylabel('Loss')
ax2.set_xlabel('Epoch')
ax2.legend(['Train', 'Validation'], loc='upper left')

plt.savefig(PLOT_PATH)
print(f"训练图表已保存至: {PLOT_PATH}")
# plt.show() # 在服务器后台运行时，通常不需要这行