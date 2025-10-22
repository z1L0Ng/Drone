# src/data_pre.py

import os
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import joblib

# --- 1. 定义路径 ---
# 原始音频文件所在的根目录
RAW_DATA_PATH = "dataset/raw/"
# 处理后的数据索引文件保存路径
PROCESSED_DATA_PATH = "dataset/processed/"
# 模型相关文件保存路径
MODELS_PATH = "saved_models/"

# 确保输出目录存在
os.makedirs(PROCESSED_DATA_PATH, exist_ok=True)
os.makedirs(MODELS_PATH, exist_ok=True)


# --- 2. 递归收集所有音频文件的路径和标签 ---
filepaths = []
labels = []

print(f"正在从 '{RAW_DATA_PATH}' 目录递归扫描所有子文件夹...")

# 检查路径是否存在
if not os.path.exists(RAW_DATA_PATH):
    raise FileNotFoundError(f"错误：找不到指定的 RAW_DATA_PATH '{RAW_DATA_PATH}'。请确认路径是否正确。")

# 遍历 RAW_DATA_PATH 下的顶级目录 (emergency, movement, noise)
for class_name in os.listdir(RAW_DATA_PATH):
    class_dir = os.path.join(RAW_DATA_PATH, class_name)
    
    # 确保它是一个目录
    if os.path.isdir(class_dir):
        print(f"  - 正在处理类别: '{class_name}'")
        # 使用 os.walk() 递归遍历该类别下的所有子文件夹
        for root, dirs, files in os.walk(class_dir):
            for filename in files:
                # 确保是 .wav 音频文件
                if filename.endswith(".wav"):
                    filepath = os.path.join(root, filename)
                    filepaths.append(filepath)
                    # 标签是顶级的文件夹名
                    labels.append(class_name)

print(f"\n成功找到 {len(filepaths)} 个音频文件。")
if len(filepaths) == 0:
    raise ValueError(f"在 '{RAW_DATA_PATH}' 的任何子目录下都没有找到 .wav 文件。请检查您的数据路径和文件结构。")

# --- 3. 标签编码 ---
le = LabelEncoder()
labels_encoded = le.fit_transform(labels)
print(f"\n发现的标签类别映射: {list(zip(le.classes_, range(len(le.classes_))))}")

# 保存标签编码器，这在预测时非常重要
encoder_path = os.path.join(MODELS_PATH, "label_encoder.joblib")
joblib.dump(le, encoder_path)
print(f"标签编码器已保存至: {encoder_path}")


# --- 4. 划分训练集、验证集和测试集 ---
# stratify=labels_encoded 确保在划分时，每个集合中的类别比例与原始数据集相同
X_train, X_test, y_train, y_test = train_test_split(
    filepaths, 
    labels_encoded, 
    test_size=0.2, 
    random_state=42, 
    stratify=labels_encoded
)

X_train, X_val, y_train, y_val = train_test_split(
    X_train, 
    y_train, 
    test_size=0.25, # 0.25 * (1-0.2) = 0.2, 使得最终比例为 60% 训练, 20% 验证, 20% 测试
    random_state=42, 
    stratify=y_train
)

print(f"\n数据集划分结果:")
print(f"训练集样本数: {len(X_train)}")
print(f"验证集样本数: {len(X_val)}")
print(f"测试集样本数: {len(X_test)}")


# --- 5. 保存文件路径列表 ---
output_npz_path = os.path.join(PROCESSED_DATA_PATH, 'data_paths.npz')
np.savez(
    output_npz_path,
    X_train=X_train,
    y_train=y_train,
    X_val=X_val,
    y_val=y_val,
    X_test=X_test,
    y_test=y_test
)

print(f"\n✅ 数据集索引文件已成功生成并保存至: {output_npz_path}")