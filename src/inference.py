# src/inference.py

import os
import numpy as np
import tensorflow as tf
import librosa
import joblib
from model import build_model
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt

# --- 1. 参数配置 (与 train_mfcc.py 保持一致) ---
# 路径 (相对于项目根目录)
TESTDATA_DIR = "/Users/zilongzeng/Research/Drone/testdataset"
MODELS_PATH = "saved_models/aligned/"
MODEL_NAME = "mfcc_best.weights.h5"
ENCODER_PATH = "saved_models/label_encoder.joblib"
RESULT_PATH = "result/aligned/"

# ==================== MFCC 前端参数 ====================
SAMPLE_RATE = 16000
DURATION = 1
N_MFCC = 40
N_MELS = 256
N_FFT = 1024
HOP_LENGTH = 512
CENTER = False
FMIN = 50
FMAX = None
TARGET_LEN = int(DURATION * SAMPLE_RATE)
MAX_FRAMES = int(DURATION * SAMPLE_RATE / HOP_LENGTH) + 1

# --- 2. 数据加载与预处理函数 ---

def load_audio_feature(filepath):
    """
    加载并预处理单个音频文件，返回 MFCC。
    这个函数严格复制了 train_mfcc.py 中 DataGenerator 的处理逻辑。
    """
    try:
        audio, _ = librosa.load(filepath, sr=SAMPLE_RATE, mono=True, duration=DURATION)
        if len(audio) < TARGET_LEN:
            audio = np.pad(audio, (0, TARGET_LEN - len(audio)))
        else:
            audio = audio[:TARGET_LEN]

        mfcc = librosa.feature.mfcc(
            y=audio,
            sr=SAMPLE_RATE,
            n_mfcc=N_MFCC,
            n_mels=N_MELS,
            n_fft=N_FFT,
            hop_length=HOP_LENGTH,
            center=CENTER,
            fmin=FMIN,
            fmax=FMAX
        )

        if mfcc.shape[1] < MAX_FRAMES:
            mfcc = np.pad(mfcc, ((0, 0), (0, MAX_FRAMES - mfcc.shape[1])), mode='constant')
        else:
            mfcc = mfcc[:, :MAX_FRAMES]

        return np.expand_dims(mfcc.astype(np.float32), axis=-1)
        
    except Exception as e:
        print(f"处理文件时出错 {filepath}: {e}")
        return None

def collect_testdata_paths(testdata_dir, class_names):
    """
    递归读取测试集，标签取路径中最接近音频文件的 class 目录名。
    支持结构如 testdataset/<group>/<class_name>/*.wav（以及更深层子目录）。
    """
    filepaths = []
    labels = []
    class_set = set(class_names)
    for root, _, files in os.walk(testdata_dir):
        for filename in files:
            if not filename.lower().endswith(".wav"):
                continue
            rel_parts = os.path.relpath(root, testdata_dir).split(os.sep)
            label = None
            for part in reversed(rel_parts):
                if part in class_set:
                    label = part
                    break
            if label is None:
                continue
            filepaths.append(os.path.join(root, filename))
            labels.append(label)
    return filepaths, labels

# --- 3. 主执行逻辑 ---

def main():
    print("--- 开始在独立的测试集上评估最终模型 ---")

    # 组合路径
    model_path = os.path.join(MODELS_PATH, MODEL_NAME)
    os.makedirs(RESULT_PATH, exist_ok=True)

    # 加载标签编码器
    print(f"正在加载标签编码器: {ENCODER_PATH}")
    if not os.path.exists(ENCODER_PATH):
        print(f"错误: 找不到标签编码器 '{ENCODER_PATH}'。请先运行 data_pre.py。")
        return
    label_encoder = joblib.load(ENCODER_PATH)
    class_names = label_encoder.classes_
    num_classes = len(class_names)

    # 加载模型权重
    print(f"正在加载模型权重: {model_path}")
    if not os.path.exists(model_path):
        print(f"错误: 找不到模型权重文件 '{model_path}'。请先运行 train_mfcc.py 进行训练。")
        return
    model = build_model((N_MFCC, MAX_FRAMES, 1), num_classes)
    model.load_weights(model_path)

    # 加载独立测试集文件路径
    print(f"正在加载独立测试集目录: {TESTDATA_DIR}")
    if not os.path.isdir(TESTDATA_DIR):
        print(f"错误: 找不到测试集目录 '{TESTDATA_DIR}'。")
        return
    X_test_paths, y_test_labels = collect_testdata_paths(TESTDATA_DIR, class_names)
    if len(X_test_paths) == 0:
        print(f"错误: 在 '{TESTDATA_DIR}' 下未找到任何 .wav 文件。")
        return
    y_test_indices = label_encoder.transform(y_test_labels)

    # 预处理所有测试样本
    print("正在预处理测试音频...")
    X_test = []
    y_test_filtered = []
    # 注意：我们不打乱测试集，以保持 y_test_indices 的对应关系
    for filepath, y_idx in zip(X_test_paths, y_test_indices):
        feature = load_audio_feature(filepath)
        if feature is not None:
            X_test.append(feature)
            y_test_filtered.append(y_idx)
    
    X_test = np.array(X_test, dtype=np.float32)
    y_test_filtered = np.array(y_test_filtered, dtype=int)
    
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
    print(classification_report(y_test_filtered, predicted_indices, target_names=class_names))

    # 生成并保存混淆矩阵
    cm = confusion_matrix(y_test_filtered, predicted_indices)
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