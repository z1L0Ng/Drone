# src/data_pre.py
import os
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import joblib

# --- 配置 ---
RAW_DATA_PATH = "dataset/raw/"
PROCESSED_DATA_PATH = "dataset/processed/"
MODELS_PATH = "saved_models/"

# 【核心修改】只处理这三类，background/drone/tellonoise 只作为噪声源忽略
TARGET_CLASSES = ['emergency', 'movement', 'unknown']

os.makedirs(PROCESSED_DATA_PATH, exist_ok=True)
os.makedirs(MODELS_PATH, exist_ok=True)

# --- 扫描文件 ---
filepaths = []
labels = []
print(f"扫描目标类别: {TARGET_CLASSES} ...")

for class_name in TARGET_CLASSES:
    class_dir = os.path.join(RAW_DATA_PATH, class_name)
    if os.path.isdir(class_dir):
        count = 0
        for root, _, files in os.walk(class_dir):
            for filename in files:
                if filename.lower().endswith(".wav"):
                    filepaths.append(os.path.join(root, filename))
                    labels.append(class_name)
                    count += 1
        print(f"  - {class_name}: {count} 个样本")

# --- 编码与划分 ---
le = LabelEncoder()
labels_encoded = le.fit_transform(labels)
joblib.dump(le, os.path.join(MODELS_PATH, "label_encoder.joblib"))

# 划分数据集 (60% Train, 20% Val, 20% Test)
X_train, X_test, y_train, y_test = train_test_split(
    filepaths, labels_encoded, test_size=0.2, random_state=42, stratify=labels_encoded
)
X_train, X_val, y_train, y_val = train_test_split(
    X_train, y_train, test_size=0.25, random_state=42, stratify=y_train
)

# 保存
np.savez(
    os.path.join(PROCESSED_DATA_PATH, 'data_paths.npz'),
    X_train=X_train, y_train=y_train,
    X_val=X_val, y_val=y_val,
    X_test=X_test, y_test=y_test
)
print(f"✅ 数据预处理完成。总样本数: {len(filepaths)}")