# src/data_pre.py
import os
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from collections import Counter
import joblib

# --- 配置 ---
RAW_DATA_PATH = "dataset/raw/"
PROCESSED_DATA_PATH = "dataset/processed/"
MODELS_PATH = "saved_models/"

# 只处理这三类
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

print(f"\n原始样本总数: {len(filepaths)}")
label_counts = Counter(labels)
print(f"原始分布: {dict(label_counts)}")

# --- 平衡数据集 (下采样到最少类别的样本量) ---
min_samples = min(label_counts.values())
print(f"\n下采样目标: 每类 {min_samples} 个样本")

balanced_filepaths = []
balanced_labels = []

for class_name in TARGET_CLASSES:
    # 获取当前类别的所有样本索引
    class_indices = [i for i, label in enumerate(labels) if label == class_name]
    
    # 随机采样到目标数量
    np.random.seed(42)  # 设置随机种子保证可复现
    sampled_indices = np.random.choice(class_indices, size=min_samples, replace=False)
    
    # 添加到平衡后的数据集
    for idx in sampled_indices:
        balanced_filepaths.append(filepaths[idx])
        balanced_labels.append(labels[idx])

print(f"\n平衡后样本总数: {len(balanced_filepaths)}")
balanced_counts = Counter(balanced_labels)
print(f"平衡后分布: {dict(balanced_counts)}")

# --- 编码与划分 ---
le = LabelEncoder()
labels_encoded = le.fit_transform(balanced_labels)
joblib.dump(le, os.path.join(MODELS_PATH, "label_encoder.joblib"))

# 划分数据集 (60% Train, 20% Val, 20% Test)
X_train, X_test, y_train, y_test = train_test_split(
    balanced_filepaths, labels_encoded, test_size=0.2, random_state=42, stratify=labels_encoded
)
X_train, X_val, y_train, y_val = train_test_split(
    X_train, y_train, test_size=0.25, random_state=42, stratify=y_train
)

print(f"\n数据集划分:")
print(f"  - 训练集: {len(X_train)} 个样本")
print(f"  - 验证集: {len(X_val)} 个样本")
print(f"  - 测试集: {len(X_test)} 个样本")

# 保存
np.savez(
    os.path.join(PROCESSED_DATA_PATH, 'data_paths.npz'),
    X_train=X_train, y_train=y_train,
    X_val=X_val, y_val=y_val,
    X_test=X_test, y_test=y_test
)
print(f"\n✅ 数据预处理完成 (已平衡)")