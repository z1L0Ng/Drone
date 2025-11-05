# src/inference.py

import os
import numpy as np
import tensorflow as tf
import librosa
import joblib
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt

# --- 1. 参数配置 (与 train.py 保持一致) ---
# 路径 (相对于项目根目录)
PROCESSED_DATA_PATH = "dataset/processed/data_paths.npz"
MODELS_PATH = "saved_models/"
MODEL_NAME = "resnet_conformer_drone.keras"
ENCODER_NAME = "label_encoder.joblib"
RESULT_PATH = "result/"

# 音频处理参数
SAMPLE_RATE = 16000
DURATION = 1
N_MELS = 256
MAX_FRAMES = int(DURATION * SAMPLE_RATE / 512) + 1 # 确保与 train.py 一致

# --- 2. 数据加载与预处理函数 ---

def load_audio_feature(filepath):
    """
    加载并预处理单个音频文件，返回梅尔频谱图。
    这个函数严格复制了 train.py 中 DataGenerator 的处理逻辑。
    """
    try:
        audio, _ = librosa.load(filepath, sr=SAMPLE_RATE, duration=DURATION)
        # 填充音频以确保长度一致
        if len(audio) < DURATION * SAMPLE_RATE:
            audio = np.pad(audio, (0, DURATION * SAMPLE_RATE - len(audio)), 'constant')

        # 提取特征
        mel_spec = librosa.feature.melspectrogram(y=audio, sr=SAMPLE_RATE, n_mels=N_MELS)
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        
        # 填充或截断频谱图帧以确保尺寸一致
        if mel_spec_db.shape[1] < MAX_FRAMES:
            pad_width = MAX_FRAMES - mel_spec_db.shape[1]
            mel_spec_db = np.pad(mel_spec_db, ((0, 0), (0, pad_width)), mode='constant')
        else:
            mel_spec_db = mel_spec_db[:, :MAX_FRAMES]
        
        # 增加通道维度以匹配模型输入
        return np.expand_dims(mel_spec_db, axis=-1)
        
    except Exception as e:
        print(f"处理文件时出错 {filepath}: {e}")
        return None

# --- 3. 主执行逻辑 ---

def main():
    print("--- 开始在独立的测试集上评估最终模型 ---")

    # 组合路径
    model_path = os.path.join(MODELS_PATH, MODEL_NAME)
    encoder_path = os.path.join(MODELS_PATH, ENCODER_NAME)
    os.makedirs(RESULT_PATH, exist_ok=True)

    # 加载模型
    print(f"正在加载模型: {model_path}")
    if not os.path.exists(model_path):
        print(f"错误: 找不到模型文件 '{model_path}'。请先运行 train.py 进行训练。")
        return
    # src/inference.py (修改后的代码)
    model = tf.keras.models.load_model(model_path, safe_mode=False)

    # 加载标签编码器
    print(f"正在加载标签编码器: {encoder_path}")
    if not os.path.exists(encoder_path):
        print(f"错误: 找不到标签编码器 '{encoder_path}'。请先运行 data_pre.py。")
        return
    label_encoder = joblib.load(encoder_path)
    class_names = label_encoder.classes_

    # 加载测试集文件路径
    print(f"正在加载测试集数据索引: {PROCESSED_DATA_PATH}")
    with np.load(PROCESSED_DATA_PATH) as data:
        X_test_paths = data['X_test']
        y_test_indices = data['y_test']

    # 预处理所有测试样本
    print("正在预处理测试音频...")
    X_test = []
    # 注意：我们不打乱测试集，以保持 y_test_indices 的对应关系
    for filepath in X_test_paths:
        feature = load_audio_feature(filepath)
        if feature is not None:
            X_test.append(feature)
    
    X_test = np.array(X_test)
    
    if len(X_test) == 0:
        print("错误：未能成功处理任何测试音频文件。")
        return

    print(f"成功加载并处理了 {len(X_test)} 个测试样本。")

    # 执行预测
    print("模型正在对测试集进行预测...")
    predictions_proba = model.predict(X_test, batch_size=32)
    predicted_indices = np.argmax(predictions_proba, axis=1)

    # --- 4. 评估结果展示 ---

    print("\n" + "="*30)
    print("       最终模型性能评估报告 (测试集)")
    print("="*30 + "\n")
    
    # 打印分类报告
    print(classification_report(y_test_indices, predicted_indices, target_names=class_names))

    # 生成并保存混淆矩阵
    cm = confusion_matrix(y_test_indices, predicted_indices)
    plt.style.use('default') # 使用默认样式以获得清晰的图像
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=class_names, yticklabels=class_names)
    plt.title('Confusion Matrix on Independent Test Set')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    
    # 保存图像
    cm_path = os.path.join(RESULT_PATH, 'test_set_confusion_matrix.png')
    plt.savefig(cm_path)
    print(f"\n✅ 混淆矩阵图像已保存至: {cm_path}")
    # plt.show() # 在服务器后台运行时可以注释掉

if __name__ == '__main__':
    main()