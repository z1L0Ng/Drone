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
    def __init__(self, filepaths, labels, batch_size, num_classes, 
                 is_training=True, 
                 noise_filepaths=None, 
                 noise_label_id=None, 
                 noise_mix_prob=0.5,  
                 min_snr_db=-30,       
                 max_snr_db=-20):      
        """
        数据生成器
        :param filepaths: 目标音频的文件路径列表
        :param labels: 对应的标签列表
        :param batch_size: 批次大小
        :param num_classes: 类别总数
        :param is_training: 是否为训练模式（True 会启用所有增强）
        :param noise_filepaths: [新增] 独立的背景噪声文件路径列表
        :param noise_label_id: [新增] 'noise' 类别在编码后的数字ID
        :param noise_mix_prob: [新增] 应用噪声叠加的概率
        :param min_snr_db: [新增] 混合噪声的最小信噪比
        :param max_snr_db: [新增] 混合噪声的最大信噪比
        """
        self.filepaths = filepaths
        self.labels = labels
        self.batch_size = batch_size
        self.num_classes = num_classes
        self.is_training = is_training
        
        self.noise_filepaths = noise_filepaths if noise_filepaths is not None else []
        self.noise_label_id = noise_label_id
        self.noise_mix_prob = noise_mix_prob
        self.min_snr_db = min_snr_db
        self.max_snr_db = max_snr_db
        
        self.target_length = DURATION * SAMPLE_RATE # 目标长度 (例如 16000)
        
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

    def _load_random_noise(self):
        """
        随机选择一个噪声文件，加载并从中随机截取 1 秒的片段。
        (完美契合您 5 秒噪声文件的需求)
        """
        if not self.noise_filepaths:
            return None
            
        noise_path = np.random.choice(self.noise_filepaths)
        try:
            # 加载完整的 5 秒噪声
            noise_audio, _ = librosa.load(noise_path, sr=SAMPLE_RATE)
        except Exception as e:
            print(f"警告：加载噪声文件失败 {noise_path}: {e}")
            return None
        
        # 检查噪声是否足够长（至少 1 秒）
        if len(noise_audio) < self.target_length:
            # 不够长，循环平铺
            padding = self.target_length - len(noise_audio)
            return np.pad(noise_audio, (0, padding), mode='wrap')
        else:
            # 噪声足够长（例如 5 秒），随机截取 1 秒
            start_idx = np.random.randint(0, len(noise_audio) - self.target_length + 1)
            return noise_audio[start_idx : start_idx + self.target_length]

    def _mix_audio(self, signal, noise, snr_db):
        """根据 SNR (dB) 将信号和噪声混合"""
        signal_rms = np.sqrt(np.mean(signal**2)) + 1e-8
        noise_rms = np.sqrt(np.mean(noise**2)) + 1e-8
        
        scale = 10**(snr_db / 20)
        desired_noise_rms = signal_rms / scale
        gain = desired_noise_rms / noise_rms
        
        return signal + (noise * gain)

    def _extract_features(self, y):
        """（不变）特征提取"""
        mel_spec = librosa.feature.melspectrogram(y=y, sr=SAMPLE_RATE, n_mels=N_MELS)
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
            
        if mel_spec_db.shape[1] < MAX_FRAMES:
            pad_width = MAX_FRAMES - mel_spec_db.shape[1]
            mel_spec_db = np.pad(mel_spec_db, ((0, 0), (0, pad_width)), mode='constant')
        else:
            mel_spec_db = mel_spec_db[:, :MAX_FRAMES]
        return mel_spec_db

    def __data_generation(self, batch_filepaths, batch_labels):
        """
        [重大更新]
        实现了 50% 噪声, 20% 变调, 20% 拉伸 的独立增强逻辑。
        """
        X = np.empty((self.batch_size, N_MELS, MAX_FRAMES, 1))
        y = np.empty((self.batch_size), dtype=int)
        
        for i, filepath in enumerate(batch_filepaths):
            # 1. 加载干净的音频
            try:
                audio, _ = librosa.load(filepath, sr=SAMPLE_RATE, duration=DURATION)
                if len(audio) < self.target_length:
                     audio = np.pad(audio, (0, self.target_length - len(audio)))
            except Exception as e:
                print(f"错误：加载音频文件失败 {filepath}: {e}")
                audio = np.zeros(self.target_length)
            
            current_label = batch_labels[i]
            
            # --- 【开始数据增强 (仅训练时)】 ---
            if self.is_training:
                
                # time stretch, pitch shift, noise addition
                if np.random.rand() < 0.2:
                    rate = np.random.uniform(0.9, 1.1)
                    audio = librosa.effects.time_stretch(y=audio, rate=rate)
                    # 拉伸后需要重新对齐长度
                    if len(audio) < self.target_length:
                         audio = np.pad(audio, (0, self.target_length - len(audio)))
                    else:
                         audio = audio[:self.target_length]
                
                # 【增强 2：音高变换 (20% 概率)】
                if np.random.rand() < 0.2:
                    n_steps = np.random.randint(-2, 3)
                    audio = librosa.effects.pitch_shift(y=audio, sr=SAMPLE_RATE, n_steps=n_steps)
                
                # 【增强 3：噪声叠加 (50% 概率)】
                # 仅在当前样本*不是* 'noise' 类别时执行
                if current_label != self.noise_label_id and np.random.rand() < self.noise_mix_prob:
                    # 随机选择一个 SNR
                    snr_db = np.random.uniform(self.min_snr_db, self.max_snr_db)
                    
                    # 加载并准备 1 秒的噪声片段
                    noise_audio = self._load_random_noise()
                    
                    if noise_audio is not None:
                        # 混合音频
                        audio = self._mix_audio(audio, noise_audio, snr_db)
            # --- 【数据增强结束】 ---
            
            # 3. 提取特征
            features = self._extract_features(audio)
            X[i,] = np.expand_dims(features, axis=-1)
            y[i] = current_label
            
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


# --- 【修改】准备噪声数据 ---
# 从您指定的 "background/" 文件夹加载
BACKGROUND_NOISE_PATH = "background/"  # <--- 修改点：指向您的文件夹
noise_source_paths = []

if os.path.exists(BACKGROUND_NOISE_PATH):
    print(f"Load Background Noise: {BACKGROUND_NOISE_PATH}")
    for root, _, files in os.walk(BACKGROUND_NOISE_PATH):
        for f in files:
            # 确保是音频文件 (您可以根据需要添加 .mp3, .flac 等)
            if f.endswith('.wav'):
                noise_source_paths.append(os.path.join(root, f))
    if noise_source_paths:
        print(f"Load {len(noise_source_paths)} files for background noise augmentation.")
    else:
        print(f"警告：在 {BACKGROUND_NOISE_PATH} 中未找到 .wav 文件。")
else:
    print(f"警告：未找到背景增强噪声目录: {BACKGROUND_NOISE_PATH}。")

# 我们仍然需要 "noise" 类的 ID，以 *避免* 往 "noise" 样本上添加背景噪声
try:
    noise_label_id = le.transform(['noise'])[0]
except ValueError:
    print("警告：在标签编码器中未找到 'noise' 类别。")
    noise_label_id = -1 # 设置一个不可能的 ID
# --- 修改结束 ---


print(f"Class number: {NUM_CLASSES}")
print(f"Class name: {class_names}")
print(f"Model input shape: {INPUT_SHAPE}")

# --- 【修改】实例化生成器 ---
# (我们使用 DataGenerator 的默认值：
#  noise_mix_prob=0.5, min_snr_db=5, max_snr_db=15)
train_generator = DataGenerator(
    X_train_paths, y_train, BATCH_SIZE, NUM_CLASSES, 
    is_training=True,
    noise_filepaths=noise_source_paths, # 传入 *独立* 的噪声路径
    noise_label_id=noise_label_id       # 传入 'noise' 类别 ID
)
val_generator = DataGenerator(X_val_paths, y_val, BATCH_SIZE, NUM_CLASSES, is_training=False)
test_generator = DataGenerator(X_test_paths, y_test, BATCH_SIZE, NUM_CLASSES, is_training=False)
# --- 修改结束 ---

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
    callbacks=[model_checkpoint, early_stopping, metrics_callback],
    verbose=2
)
print("\n✅ 训练完成。")

# --- 6. 在测试集上进行最终评估 ---
print("\n在测试集上评估模型最终性能...")
test_loss, test_accuracy = model.evaluate(test_generator, verbose=1)
print(f"Test set loss: {test_loss:.4f}")
print(f"Test set accuracy: {test_accuracy:.4f}")

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