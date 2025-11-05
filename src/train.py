# src/train.py

import os
import numpy as np
import tensorflow as tf
import librosa
from model import build_model
from keras.optimizers import Adam
from keras.callbacks import ModelCheckpoint, EarlyStopping, Callback
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report
import joblib


# --- 1. 定义路径和参数 ---
PROCESSED_DATA_PATH = "dataset/processed/data_paths.npz"
MODELS_PATH = "saved_models/"
HISTORY_PATH = "saved_models/training_history.npy"
ENCODER_PATH = os.path.join(MODELS_PATH, "label_encoder.joblib")

# 结果保存路径
RESULT_PATH = "result/"
PLOT_ACC_LOSS_PATH = os.path.join(RESULT_PATH, "training_accuracy_loss.png")
PLOT_CLASS_ACC_PATH = os.path.join(RESULT_PATH, "training_class_accuracy.png")
CONFUSION_MATRIX_PATH = os.path.join(RESULT_PATH, "confusion_matrix.png")
CLASSIFICATION_REPORT_PATH = os.path.join(RESULT_PATH, "classification_report.txt")


# 确保目录存在
os.makedirs(RESULT_PATH, exist_ok=True)
os.makedirs(MODELS_PATH, exist_ok=True)

# 训练参数
EPOCHS = 50
BATCH_SIZE = 32
LEARNING_RATE = 0.0001

# 音频处理参数
SAMPLE_RATE = 16000 # 采样率
DURATION = 1       # 音频时长（秒）
N_MELS = 256       # Mel Spectrogram 的频带数
MAX_FRAMES = int(DURATION * SAMPLE_RATE / 512) + 1 # 帧数

# --- 2. 自定义回调函数，用于计算每个类别的指标 ---
class MetricsCallback(Callback):
    """
    一个自定义的回调函数，用于在每个epoch结束时计算并记录
    每个类别的准确率和误分类数量。
    """
    def __init__(self, validation_generator, num_classes, label_encoder):
        super().__init__()
        self.validation_generator = validation_generator
        self.num_classes = num_classes
        self.le = label_encoder

    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}
        # 1. 获取验证集的真实标签和预测结果
        y_pred_probs = self.model.predict(self.validation_generator)
        y_pred = np.argmax(y_pred_probs, axis=1)
        
        # 从生成器中获取真实标签
        y_true = []
        for i in range(len(self.validation_generator)):
            _, labels_batch = self.validation_generator[i]
            y_true.extend(np.argmax(labels_batch, axis=1))
        y_true = np.array(y_true)

        # 2. 计算混淆矩阵
        cm = confusion_matrix(y_true, y_pred)

        # 3. 从混淆矩阵计算每个类别的指标
        for i in range(self.num_classes):
            class_name = self.le.classes_[i]
            correct_predictions = cm[i, i]
            total_samples = np.sum(cm[i, :])
            
            # 避免除以零
            if total_samples == 0:
                accuracy = 0.0
            else:
                accuracy = correct_predictions / total_samples
            
            misclassifications = total_samples - correct_predictions
            
            # 存入logs，以便history对象可以记录
            logs[f'class_{class_name}_accuracy'] = accuracy
            logs[f'class_{class_name}_misclassifications'] = misclassifications
        
        print(f"\nEpoch {epoch+1} Per-Class Validation Metrics:")
        for i in range(self.num_classes):
            class_name = self.le.classes_[i]
            print(f"  - {class_name}: Accuracy: {logs[f'class_{class_name}_accuracy']:.4f}, Misclassified: {logs[f'class_{class_name}_misclassifications']}")


# --- 3. 数据生成器 (DataGenerator) ---
class DataGenerator(tf.keras.utils.Sequence):
    def __init__(self, filepaths, labels, batch_size, num_classes, is_training=True):
        self.filepaths = filepaths
        self.labels = labels
        self.batch_size = batch_size
        self.num_classes = num_classes
        self.is_training = is_training
        self.on_epoch_end()

    def __len__(self):
        return int(np.floor(len(self.filepaths) / self.batch_size))

    def __getitem__(self, index):
        indexes = self.indexes[index*self.batch_size:(index+1)*self.batch_size]
        batch_filepaths = [self.filepaths[k] for k in indexes]
        batch_labels = [self.labels[k] for k in indexes]
        X, y = self.__data_generation(batch_filepaths, batch_labels)
        return X, y

    def on_epoch_end(self):
        self.indexes = np.arange(len(self.filepaths))
        if self.is_training:
            np.random.shuffle(self.indexes)

    def _augment_audio(self, y):
        if np.random.rand() < 0.5:
            rate = np.random.uniform(0.9, 1.1)
            y = librosa.effects.time_stretch(y=y, rate=rate)
        if np.random.rand() < 0.5:
            n_steps = np.random.randint(-2, 3)
            y = librosa.effects.pitch_shift(y=y, sr=SAMPLE_RATE, n_steps=n_steps)
        return y

    def _extract_features(self, y):
        mel_spec = librosa.feature.melspectrogram(y=y, sr=SAMPLE_RATE, n_mels=N_MELS)
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        
        if mel_spec_db.shape[1] < MAX_FRAMES:
            pad_width = MAX_FRAMES - mel_spec_db.shape[1]
            mel_spec_db = np.pad(mel_spec_db, ((0, 0), (0, pad_width)), mode='constant')
        else:
            mel_spec_db = mel_spec_db[:, :MAX_FRAMES]
        return mel_spec_db

    def __data_generation(self, batch_filepaths, batch_labels):
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

# --- 4. 加载数据索引并创建生成器 ---
print("加载数据集索引...")
with np.load(PROCESSED_DATA_PATH, allow_pickle=True) as data:
    X_train_paths, y_train = data['X_train'], data['y_train']
    X_val_paths, y_val = data['X_val'], data['y_val']
    X_test_paths, y_test = data['X_test'], data['y_test']

# 加载标签编码器
le = joblib.load(ENCODER_PATH)
class_names = le.classes_
NUM_CLASSES = len(class_names)
INPUT_SHAPE = (N_MELS, MAX_FRAMES, 1)

print(f"类别数量: {NUM_CLASSES}")
print(f"类别名称: {class_names}")
print(f"模型输入尺寸: {INPUT_SHAPE}")

train_generator = DataGenerator(X_train_paths, y_train, BATCH_SIZE, NUM_CLASSES, is_training=True)
val_generator = DataGenerator(X_val_paths, y_val, BATCH_SIZE, NUM_CLASSES, is_training=False)
test_generator = DataGenerator(X_test_paths, y_test, BATCH_SIZE, NUM_CLASSES, is_training=False)

# --- 5. 构建、编译和训练模型 ---
model = build_model(input_shape=INPUT_SHAPE, num_classes=NUM_CLASSES)
model.compile(
    optimizer=Adam(learning_rate=LEARNING_RATE),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)
model.summary()

checkpoint_path = os.path.join(MODELS_PATH, "resnet_conformer_drone.keras")
model_checkpoint = ModelCheckpoint(filepath=checkpoint_path, save_best_only=True, monitor='val_accuracy', mode='max', verbose=1)
early_stopping = EarlyStopping(monitor='val_accuracy', patience=10, verbose=1, restore_best_weights=True)

# 实例化我们自定义的回调
metrics_callback = MetricsCallback(validation_generator=val_generator, num_classes=NUM_CLASSES, label_encoder=le)

print("\n开始模型训练...")
history = model.fit(
    train_generator,
    validation_data=val_generator,
    epochs=EPOCHS,
    callbacks=[model_checkpoint, early_stopping, metrics_callback]
)
print("\n✅ 训练完成。")

# --- 6. 在测试集上进行最终评估 ---
print("\n在测试集上评估模型最终性能...")
test_loss, test_accuracy = model.evaluate(test_generator, verbose=1)
print(f"测试集损失: {test_loss:.4f}")
print(f"测试集准确率: {test_accuracy:.4f}")

# 生成分类报告和混淆矩阵
y_pred_test_probs = model.predict(test_generator)
y_pred_test = np.argmax(y_pred_test_probs, axis=1)

y_true_test = []
for i in range(len(test_generator)):
    _, labels_batch = test_generator[i]
    y_true_test.extend(np.argmax(labels_batch, axis=1))
y_true_test = np.array(y_true_test)

# 生成分类报告
report = classification_report(y_true_test, y_pred_test, target_names=class_names)
print("\n--- 分类报告 ---")
print(report)
with open(CLASSIFICATION_REPORT_PATH, 'w') as f:
    f.write(report)
print(f"分类报告已保存至: {CLASSIFICATION_REPORT_PATH}")

# 生成混淆矩阵
cm = confusion_matrix(y_true_test, y_pred_test)
plt.figure(figsize=(10, 8))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=class_names, yticklabels=class_names)
plt.title('Confusion Matrix')
plt.ylabel('True Label')
plt.xlabel('Predicted Label')
plt.savefig(CONFUSION_MATRIX_PATH)
plt.close()
print(f"混淆矩阵图表已保存至: {CONFUSION_MATRIX_PATH}")


# --- 7. 保存和绘制训练历史 ---
print("\n保存训练历史并生成图表...")
np.save(HISTORY_PATH, history.history)
print(f"训练历史已保存至: {HISTORY_PATH}")

# 绘制整体准确率和损失曲线
plt.style.use('seaborn-v0_8-whitegrid')
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
ax1.plot(history.history['accuracy'], label='Train Accuracy')
ax1.plot(history.history['val_accuracy'], label='Validation Accuracy')
ax1.set_title('Model Accuracy')
ax1.set_ylabel('Accuracy')
ax1.set_xlabel('Epoch')
ax1.legend(loc='upper left')
ax2.plot(history.history['loss'], label='Train Loss')
ax2.plot(history.history['val_loss'], label='Validation Loss')
ax2.set_title('Model Loss')
ax2.set_ylabel('Loss')
ax2.set_xlabel('Epoch')
ax2.legend(loc='upper left')
plt.savefig(PLOT_ACC_LOSS_PATH)
plt.close(fig)
print(f"整体训练图表已保存至: {PLOT_ACC_LOSS_PATH}")


# 绘制每个类别的准确率曲线
plt.figure(figsize=(12, 8))
for i in range(NUM_CLASSES):
    class_name = class_names[i]
    key = f'class_{class_name}_accuracy'
    if key in history.history:
        plt.plot(history.history[key], label=f'{class_name} Accuracy')
plt.title('Per-Class Validation Accuracy')
plt.ylabel('Accuracy')
plt.xlabel('Epoch')
plt.legend(loc='lower right')
plt.grid(True)
plt.savefig(PLOT_CLASS_ACC_PATH)
plt.close()
print(f"各类别准确率图表已保存至: {PLOT_CLASS_ACC_PATH}")