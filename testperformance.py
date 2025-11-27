# test_robustness.py
#
# 目的：
# 1. 加载已训练的模型。
# 2. 加载“干净”的测试集索引。
# 3. 加载您指定的“真实无人机噪音”（来自 datav1/）。
# 4. 在给定的 SNR (信噪比) 下，将噪音与 *所有* 测试音频混合。
# 5. 在加噪后的完整测试集上评估模型性能。
#
# 如何运行：
# (确保您的环境已激活)
#
# python testperformance.py --snr 15
#

import os
import numpy as np
import tensorflow as tf
import librosa
import joblib
import argparse
from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report

# --- 1. 从 train.py 导入核心参数和路径 ---
# (确保这些参数与 train.py 中的设置完全一致)
PROCESSED_DATA_PATH = "dataset/processed/data_paths.npz"
MODELS_PATH = "saved_models/"
ENCODER_PATH = os.path.join(MODELS_PATH, "label_encoder.joblib")
MODEL_FILE_PATH = os.path.join(MODELS_PATH, "resnet_conformer_drone.keras")

# 结果保存路径（使用新文件夹以免覆盖）
RESULT_PATH = "result/robustness_test/"
os.makedirs(RESULT_PATH, exist_ok=True)

# 音频处理参数
SAMPLE_RATE = 16000 # 采样率
DURATION = 1       # 音频时长（秒）
N_MELS = 256       # Mel Spectrogram 的频带数
MAX_FRAMES = int(DURATION * SAMPLE_RATE / 512) + 1 # 帧数
TARGET_LENGTH = DURATION * SAMPLE_RATE

# --- 2. 借用 train.py 的辅助函数 ---
# (这些函数与 DataGenerator 中的实现相同)

def _load_random_noise(noise_filepaths):
    """从噪声路径列表中随机选择一个，加载并截取 1 秒。"""
    if not noise_filepaths:
        return np.zeros(TARGET_LENGTH)
        
    noise_path = np.random.choice(noise_filepaths)
    try:
        noise_audio, _ = librosa.load(noise_path, sr=SAMPLE_RATE)
    except Exception as e:
        print(f"警告：加载噪声文件失败 {noise_path}: {e}")
        return np.zeros(TARGET_LENGTH)
    
    # 随机截取 1 秒
    if len(noise_audio) < TARGET_LENGTH:
        padding = TARGET_LENGTH - len(noise_audio)
        return np.pad(noise_audio, (0, padding), mode='wrap')
    else:
        start_idx = np.random.randint(0, len(noise_audio) - TARGET_LENGTH + 1)
        return noise_audio[start_idx : start_idx + TARGET_LENGTH]

def _mix_audio(signal, noise, snr_db):
    """根据 SNR (dB) 将信号和噪声混合"""
    signal_rms = np.sqrt(np.mean(signal**2)) + 1e-8
    noise_rms = np.sqrt(np.mean(noise**2)) + 1e-8
    
    scale = 10**(snr_db / 20)
    desired_noise_rms = signal_rms / scale
    gain = desired_noise_rms / noise_rms
    
    return signal + (noise * gain)

def _extract_features(y):
    """（不变）特征提取"""
    mel_spec = librosa.feature.melspectrogram(y=y, sr=SAMPLE_RATE, n_mels=N_MELS)
    mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
    
    if mel_spec_db.shape[1] < MAX_FRAMES:
        pad_width = MAX_FRAMES - mel_spec_db.shape[1]
        mel_spec_db = np.pad(mel_spec_db, ((0, 0), (0, pad_width)), mode='constant')
    else:
        mel_spec_db = mel_spec_db[:, :MAX_FRAMES]
    
    # 添加通道维度
    return np.expand_dims(mel_spec_db, axis=-1)


def run_test(target_snr, noise_dir):
    """
    在指定的 SNR 下运行完整的鲁棒性测试。
    """
    print(f"\n--- 正在开始测试，目标 SNR: {target_snr} dB ---")

    # --- 3. 加载资源 ---
    print("加载模型...")
    # 如果加载失败，提示可能需要导入自定义层
    # 但由于 model.py 只是函数式 API，通常不需要
    try:
        model = tf.keras.models.load_model(MODEL_FILE_PATH, safe_mode=False)
    except Exception as e:
        print(f"错误：加载模型失败。")
        print(f"如果模型包含自定义层，请确保在脚本中导入 'from src.model import *'。")
        print(f"错误详情: {e}")
        return
    model.summary()

    print("加载标签编码器和测试集索引...")
    le = joblib.load(ENCODER_PATH)
    class_names = le.classes_
    NUM_CLASSES = len(class_names)
    
    with np.load(PROCESSED_DATA_PATH, allow_pickle=True) as data:
        X_test_paths, y_test = data['X_test'], data['y_test']
    
    print("加载无人机噪音文件...")
    noise_filepaths = []
    if os.path.exists(noise_dir):
        for root, _, files in os.walk(noise_dir):
            for f in files:
                if f.endswith('.wav'):
                    noise_filepaths.append(os.path.join(root, f))
    
    if not noise_filepaths:
        print(f"错误：在 '{noise_dir}' 中找不到任何 .wav 噪音文件。")
        return
        
    print(f"成功加载 {len(noise_filepaths)} 个噪音文件用于测试。")

    # --- 4. 创建加噪的测试集 ---
    # 我们不使用 DataGenerator，而是“一次性”处理所有测试样本
    # 这样可以保证 100% 的样本都被评估
    
    print("正在生成加噪的测试数据集...")
    X_test_processed = []
    y_test_processed = []

    for i in tqdm(range(len(X_test_paths)), desc="处理测试样本"):
        filepath = X_test_paths[i]
        label = y_test[i]
        
        # 1. 加载干净音频
        try:
            audio, _ = librosa.load(filepath, sr=SAMPLE_RATE, duration=DURATION)
            if len(audio) < TARGET_LENGTH:
                 audio = np.pad(audio, (0, TARGET_LENGTH - len(audio)))
        except Exception as e:
            print(f"警告：加载音频 {filepath} 失败，跳过。")
            continue
            
        # 2. 加载随机噪音
        noise_audio = _load_random_noise(noise_filepaths)
        
        # 3. 混合（100% 概率）
        mixed_audio = _mix_audio(audio, noise_audio, target_snr)
        
        # 4. 提取特征
        features = _extract_features(mixed_audio)
        
        X_test_processed.append(features)
        y_test_processed.append(label)

    # 转换为 Numpy 数组
    X_test_np = np.array(X_test_processed)
    y_true = np.array(y_test_processed)
    y_true_categorical = tf.keras.utils.to_categorical(y_true, num_classes=NUM_CLASSES)

    print(f"added noise to {len(X_test_np)} test samples.")

    # --- 5. 评估和预测 ---
    print("\n在加噪的测试集上评估模型...")
    test_loss, test_accuracy = model.evaluate(X_test_np, y_true_categorical, verbose=1)
    print(f"\n--- SNR: {target_snr} dB ---")
    print(f"test_loss: {test_loss:.4f}")
    print(f"test_accuracy: {test_accuracy:.4f}")

    print("predicting on the test set...")
    y_pred_probs = model.predict(X_test_np)
    y_pred = np.argmax(y_pred_probs, axis=1)

    # --- 6. 生成报告和混淆矩阵 ---
    
    # 动态生成保存路径
    report_filename = os.path.join(RESULT_PATH, f"classification_report_snr_{target_snr}dB.txt")
    matrix_filename = os.path.join(RESULT_PATH, f"confusion_matrix_snr_{target_snr}dB.png")

    # 生成分类报告
    report = classification_report(y_true, y_pred, target_names=class_names, digits=4)
    print("\n--- 分类报告 ---")
    print(report)
    with open(report_filename, 'w') as f:
        f.write(f"SNR: {target_snr} dB\n")
        f.write(f"Test Loss: {test_loss:.4f}\n")
        f.write(f"Test Accuracy: {test_accuracy:.4f}\n\n")
        f.write(report)
    print(f"分类报告已保存至: {report_filename}")

    # 生成混淆矩阵
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=class_names, yticklabels=class_names)
    plt.title(f'Confusion Matrix (SNR = {target_snr} dB)')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.savefig(matrix_filename)
    plt.close()
    print(f"混淆矩阵图表已保存至: {matrix_filename}")
    print(f"\n--- SNR {target_snr} dB 测试完成 ---")


# --- 7. 命令行入口 ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="在特定 SNR 下使用真实噪音测试模型的鲁棒性。"
    )
    
    parser.add_argument(
        "--snr",
        type=float,
        required=True,
        help="要测试的信噪比 (SNR)，单位 dB (例如: 15, 10, 5, 0, -5)"
    )
    
    parser.add_argument(
        "--noise_dir",
        type=str,
        default="datav1/",  # 按照您的要求，默认为 datav1/
        help="包含真实无人机噪音 .wav 文件的文件夹路径"
    )
    
    args = parser.parse_args()
    
    run_test(args.snr, args.noise_dir)