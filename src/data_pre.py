import os
import librosa
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import joblib

# --- 1. 定义路径和参数 ---

RAW_DATA_PATH = "data/raw/"
PROCESSED_DATA_PATH = "data/processed/"
MODELS_PATH = "saved_models/"

SAMPLE_RATE = 16000
DURATION = 1.0
N_MELS = 256
DESIRED_FRAMES = 61

# --- 2. 音频处理函数 ---

def process_audio_file(file_path):
    """加载音频文件，统一长度，并提取梅尔频谱图特征"""
    try:
        audio, _ = librosa.load(file_path, sr=SAMPLE_RATE, duration=DURATION)
        if len(audio) < SAMPLE_RATE * DURATION:
            audio = np.pad(audio, (0, int(SAMPLE_RATE * DURATION) - len(audio)), mode='constant')
        else:
            audio = audio[:int(SAMPLE_RATE * DURATION)]

        mel_spec = librosa.feature.melspectrogram(y=audio, sr=SAMPLE_RATE, n_mels=N_MELS)
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        mel_spec_db = mel_spec_db / 80.0 + 1.0
        return mel_spec_db
    except Exception as e:
        print(f"处理文件失败 {file_path}: {e}")
        return None

# --- 3. 数据加载与处理主流程 ---

def prepare_dataset():
    """执行完整的数据准备流程"""
    if not os.path.exists(PROCESSED_DATA_PATH):
        os.makedirs(PROCESSED_DATA_PATH)
    if not os.path.exists(MODELS_PATH):
        os.makedirs(MODELS_PATH)

    features = []
    labels = []
    
    categories = ["emergency", "movement", "noise"]

    print("开始加载和处理音频数据...")
    for category in categories:
        category_path = os.path.join(RAW_DATA_PATH, category)
        if not os.path.isdir(category_path):
            print(f"警告：找不到目录 {category_path}，跳过该类别。")
            continue
            
        # *** 修改部分：使用 os.walk() 遍历所有子文件夹 ***
        for root, _, files in os.walk(category_path):
            for file_name in files:
                if file_name.endswith(".wav"):
                    file_path = os.path.join(root, file_name)
                    
                    mel_spec = process_audio_file(file_path)
                    
                    if mel_spec is not None:
                        features.append(mel_spec)
                        labels.append(category)
    
    print(f"音频处理完成。共加载了 {len(features)} 个文件。")

    # --- 4. 标签编码 ---
    
    print("正在进行标签编码...")
    label_encoder = LabelEncoder()
    labels_encoded = label_encoder.fit_transform(labels)
    
    encoder_path = os.path.join(MODELS_PATH, 'label_encoder.joblib')
    joblib.dump(label_encoder, encoder_path)
    print(f"标签编码器已保存至: {encoder_path}")
    print(f"类别: {label_encoder.classes_}")

    # --- 5. 数据塑形和划分 ---

    X = np.array(features)
    
    current_frames = X.shape[2]
    if current_frames < DESIRED_FRAMES:
        pad_width = ((0, 0), (0, 0), (0, DESIRED_FRAMES - current_frames))
        X = np.pad(X, pad_width, mode='constant')
    elif current_frames > DESIRED_FRAMES:
        X = X[:, :, :DESIRED_FRAMES]

    X = X[..., np.newaxis]
    y = labels_encoded
    
    print(f"最终特征形状: {X.shape}")

    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
    )

    print(f"数据划分完成:")
    print(f" - 训练集: {len(X_train)} 个样本")
    print(f" - 验证集: {len(X_val)} 个样本")
    print(f" - 测试集: {len(X_test)} 个样本")

    # --- 6. 保存处理好的数据 ---
    
    print("正在保存处理好的数据集...")
    np.savez_compressed(os.path.join(PROCESSED_DATA_PATH, 'train_data.npz'), features=X_train, labels=y_train)
    np.savez_compressed(os.path.join(PROCESSED_DATA_PATH, 'val_data.npz'), features=X_val, labels=y_val)
    np.savez_compressed(os.path.join(PROCESSED_DATA_PATH, 'test_data.npz'), features=X_test, labels=y_test)
    
    print("所有数据已成功处理并保存！")


if __name__ == '__main__':
    prepare_dataset()