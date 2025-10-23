# predict_v2.py

import os
import numpy as np
import tensorflow as tf
import librosa
import joblib
from src.model import build_model
import argparse

# --- 1. 定义与 train.py 完全一致的参数 ---
# 模型路径
MODEL_PATH = "saved_models/resnet_conformer_drone.keras"
ENCODER_PATH = "saved_models/label_encoder.joblib"
# 【修改一】: 将测试文件夹路径固定
TEST_FOLDER_PATH = "test/"

# 音频处理参数 (必须与 train.py 中的设置一模一样)
SAMPLE_RATE = 16000 # 采样率
DURATION = 1       # 音频时长（秒）
N_MELS = 128       # Mel Spectrogram 的频带数
MAX_FRAMES = int(DURATION * SAMPLE_RATE / 512) + 1 # 帧数

# --- 2. 定义与 train.py 完全一致的特征提取函数 ---
def extract_features(audio_path):
    """从单个音频文件加载、处理并提取特征"""
    try:
        # 加载音频并统一长度
        audio, _ = librosa.load(audio_path, sr=SAMPLE_RATE, duration=DURATION)
        if len(audio) < DURATION * SAMPLE_RATE:
            audio = np.pad(audio, (0, DURATION * SAMPLE_RATE - len(audio)), mode='constant')

        # 提取Mel频谱图
        mel_spec = librosa.feature.melspectrogram(y=audio, sr=SAMPLE_RATE, n_mels=N_MELS)
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)

        # 尺寸对齐
        if mel_spec_db.shape[1] < MAX_FRAMES:
            pad_width = MAX_FRAMES - mel_spec_db.shape[1]
            mel_spec_db = np.pad(mel_spec_db, ((0, 0), (0, pad_width)), mode='constant')
        else:
            mel_spec_db = mel_spec_db[:, :MAX_FRAMES]
        
        # 增加批次和通道维度以符合模型输入要求
        features = np.expand_dims(mel_spec_db, axis=0)
        features = np.expand_dims(features, axis=-1)
        
        return features
    except Exception as e:
        print(f"处理文件 {os.path.basename(audio_path)} 时出错: {e}")
        return None

# --- 3. 主预测逻辑 ---
def main():
    print("正在加载模型和标签编码器...")
    try:
        # 加载标签编码器
        le = joblib.load(ENCODER_PATH)
        num_classes = len(le.classes_)
        
        # 构建模型架构 (使用与训练时相同的参数)
        input_shape = (N_MELS, MAX_FRAMES, 1)
        model = build_model(input_shape=input_shape, num_classes=num_classes)
        
        # 加载训练好的权重
        model.load_weights(MODEL_PATH)

        print("模型加载成功！")

    except Exception as e:
        print(f"错误：无法加载模型或编码器。请确保路径正确。")
        print(f"详细信息: {e}")
        return

    # 【修改二】: 检查测试文件夹是否存在并遍历
    if not os.path.exists(TEST_FOLDER_PATH):
        print(f"错误：找不到测试文件夹 '{TEST_FOLDER_PATH}'")
        return

    print(f"\n--- 开始批量预测: 目标文件夹 '{TEST_FOLDER_PATH}' ---\n")
    
    # 遍历文件夹中的所有文件
    for filename in sorted(os.listdir(TEST_FOLDER_PATH)):
        # 只处理 .wav 文件
        if filename.endswith(".wav"):
            audio_file_path = os.path.join(TEST_FOLDER_PATH, filename)
            
            print(f"正在对文件 '{filename}' 进行预测...")
            
            # 提取特征
            features = extract_features(audio_file_path)
            
            if features is not None:
                # 进行预测
                predictions = model.predict(features, verbose=0) # 设置 verbose=0 避免每个文件都打印进度条
                
                # 获取概率最高的类别
                predicted_index = np.argmax(predictions, axis=1)[0]
                predicted_label = le.inverse_transform([predicted_index])[0]
                confidence = predictions[0][predicted_index]
                
                print(f"  └── 预测结果: {predicted_label} (置信度: {confidence:.2%})\n")
    
    print("--- 批量预测完成 ---")

if __name__ == '__main__':
    # 【修改三】: 移除了命令行参数解析，直接调用 main 函数
    main()