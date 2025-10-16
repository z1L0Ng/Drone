import os
import librosa
import numpy as np
import tensorflow as tf
import joblib
from collections import deque
from src.model import build_model # 引用我们现有的模型结构

# --- 1. 定义路径和常量 ---
TEST_AUDIO_DIR = "test/"
MODEL_PATH = "saved_models/resnet_conformer_drone.keras"
ENCODER_PATH = "saved_models/label_encoder.joblib"
SAMPLE_RATE = 16000
N_MELS = 256
# 模型在训练时期望的输入形状
INPUT_SHAPE = (N_MELS, 61, 1)

# --- 2. 加载模型和编码器 ---
print("正在加载模型和标签编码器...")
try:
    # 假设有3个类别: emergency, movement, noise
    model = build_model(input_shape=INPUT_SHAPE, num_classes=3)
    model.load_weights(MODEL_PATH)
    label_encoder = joblib.load(ENCODER_PATH)
    print("模型和编码器加载成功。")
except Exception as e:
    print(f"错误：无法加载模型或编码器。请确保路径正确。")
    print(f"详细信息: {e}")
    exit()

# --- 3. 优化后的推理参数 ---
WINDOW_DURATION = 1.0  # 窗口时长1秒，与训练数据一致
STEP_DURATION = 0.5    # 每0.5秒滑动一次窗口
CONFIDENCE_THRESHOLD = 0.92 # 采用更严格的置信度门槛
VOTE_THRESHOLD = 3     # 常规指令确认需要的投票数
SHORT_AUDIO_THRESHOLD_S = 2.0 # 用于区分长/短音频的阈值（秒）
# ENERGY_THRESHOLD = 0.005 # <-- 已移除能量检测

# --- 4. 简化的音频处理函数 ---
def process_audio_chunk(audio_chunk):
    """
    处理单个音频块: 1. 特征提取 -> 2. 模型预测
    """
    # 步骤1: 特征提取
    mel_spec = librosa.feature.melspectrogram(y=audio_chunk, sr=SAMPLE_RATE, n_mels=N_MELS)
    mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
    mel_spec_db = mel_spec_db / 80.0 + 1.0

    if mel_spec_db.shape[1] > INPUT_SHAPE[1]:
        mel_spec_db = mel_spec_db[:, :INPUT_SHAPE[1]]
    else:
        pad_width = INPUT_SHAPE[1] - mel_spec_db.shape[1]
        mel_spec_db = np.pad(mel_spec_db, ((0, 0), (0, pad_width)), mode='constant')
        
    feature = mel_spec_db[..., np.newaxis]
    feature = np.expand_dims(feature, axis=0)

    # 步骤2: 模型预测
    prediction = model.predict(feature, verbose=0)[0]
    return prediction

# --- 5. 核心推理函数 ---
def run_inference_on_audio(file_path):
    """
    根据音频长度自动选择合适的推理策略，并优先处理紧急指令。
    """
    try:
        audio, _ = librosa.load(file_path, sr=SAMPLE_RATE)
    except Exception as e:
        print(f"无法加载音频文件 {file_path}: {e}")
        return
    
    duration_s = librosa.get_duration(y=audio, sr=SAMPLE_RATE)
    print(f"\n===== 开始处理文件: {os.path.basename(file_path)} (时长: {duration_s:.2f}s) =====")

    # --- 策略选择 ---
    if duration_s < SHORT_AUDIO_THRESHOLD_S:
        # **单次模式 (Single-Shot Mode) for Short Audio**
        print("策略: 短音频，使用单次预测模式。")
        probabilities = process_audio_chunk(audio)
        
        if np.max(probabilities) > CONFIDENCE_THRESHOLD:
            predicted_index = np.argmax(probabilities)
            predicted_label = label_encoder.classes_[predicted_index]
            if predicted_label != 'noise':
                print(f"\n✅ 指令确认! -> 执行指令: ** {predicted_label.upper()} ** (置信度: {np.max(probabilities):.2f})\n")
            else:
                print("结果: 检测到噪音或无指令。")
        else:
            print(f"结果: 未检测到高置信度的指令 (最高: {np.max(probabilities):.2f})。")
    else:
        # **流式模式 (Streaming Mode) for Long Audio**
        print("策略: 长音频，使用滑动窗口模式（带紧急指令优先）。")
        window_samples = int(SAMPLE_RATE * WINDOW_DURATION)
        step_samples = int(SAMPLE_RATE * STEP_DURATION)
        recent_predictions = deque(maxlen=VOTE_THRESHOLD + 2)
        has_detection = False
        
        for i in range(0, len(audio) - window_samples + 1, step_samples):
            start_time = i / SAMPLE_RATE
            end_time = (i + window_samples) / SAMPLE_RATE
            chunk = audio[i : i + window_samples]
            probabilities = process_audio_chunk(chunk)
            
            if np.max(probabilities) > CONFIDENCE_THRESHOLD:
                predicted_index = np.argmax(probabilities)
                predicted_label = label_encoder.classes_[predicted_index]
                if predicted_label != 'noise':
                    has_detection = True
                    print(f"[{start_time:.2f}s - {end_time:.2f}s] 检测到可能指令: {predicted_label} (置信度: {np.max(probabilities):.2f})")
                    recent_predictions.append(predicted_label)

            # --- 决策逻辑 ---
            # 1. 紧急指令优先判断
            if len(recent_predictions) >= 2 and list(recent_predictions)[-1] == 'emergency' and list(recent_predictions)[-2] == 'emergency':
                print(f"\n🚨 高优先级指令确认! -> 立即执行指令: ** EMERGENCY **\n")
                recent_predictions.clear()
                continue

            # 2. 常规指令投票判断
            if len(recent_predictions) >= VOTE_THRESHOLD:
                most_common = max(set(recent_predictions), key=list(recent_predictions).count)
                if list(recent_predictions).count(most_common) >= VOTE_THRESHOLD:
                    print(f"\n✅ 指令确认! -> 执行指令: ** {most_common.upper()} **\n")
                    recent_predictions.clear()
        
        if not has_detection:
            print("未检测到高置信度的指令。")

    print(f"===== 文件处理完毕: {os.path.basename(file_path)} =====\n")

# --- 6. 批处理主程序 ---
if __name__ == '__main__':
    if not os.path.isdir(TEST_AUDIO_DIR):
        print(f"错误: 测试文件夹 '{TEST_AUDIO_DIR}' 不存在。")
    else:
        audio_files = [f for f in os.listdir(TEST_AUDIO_DIR) if f.endswith('.wav')]
        if not audio_files:
            print(f"在文件夹 '{TEST_AUDIO_DIR}' 中没有找到 .wav 音频文件。")
        else:
            print(f"在 '{TEST_AUDIO_DIR}' 中找到 {len(audio_files)} 个音频文件进行测试。")
            for audio_file in sorted(audio_files): # 使用sorted确保处理顺序一致
                full_path = os.path.join(TEST_AUDIO_DIR, audio_file)
                run_inference_on_audio(full_path)