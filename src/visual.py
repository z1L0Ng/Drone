# visualize_augmentations_gui.py
#
# 目的：
# 通过简单的 True/False 开关，可视化 train.py 中的数据增强效果，
# 用于向您的老师进行演示。

import os
import numpy as np
import librosa
import librosa.display
import matplotlib.pyplot as plt

# --- 1. 从 train.py 导入核心参数 ---
SAMPLE_RATE = 16000 # 采样率
DURATION = 1       # 音频时长（秒）
TARGET_LENGTH = DURATION * SAMPLE_RATE # 16000


# ================================================================
# --- ⚙️ 配置区域：请在这里修改 ---
# ================================================================

# --- 1. 文件路径 ---
# (请确保路径正确)
FILE_PATH_ORIGINAL = "dataset/raw/emergency/stop/0a5636ca_nohash_0.wav" # 示例：加载一个测试文件
FILE_PATH_NOISE    = "/files1/Zilong/Drone/datav1/20251029_185958.wav" # 示例：请替换为您5秒噪音文件的真实路径

# --- 2. 增强开关 (True = 应用, False = 不应用) ---
DO_TIME_STRETCH = False  # 时间拉伸 (20% 概率逻辑)
DO_PITCH_SHIFT  = False  # 音高变换 (20% 概率逻辑)
DO_ADD_NOISE    = True  # 添加背景噪音 (50% 概率逻辑)

# --- 3. 噪声参数 ---
# (仅在 DO_ADD_NOISE = True 时生效)
TARGET_SNR_DB = 5   # 演示时使用的信噪比 (dB)，越小噪音越大

# --- 4. 输出 ---
OUTPUT_PLOT_PATH = "augmentation_demo.png" # 结果图保存路径

# ================================================================
# --- 脚本主体 ---
# ================================================================

def load_audio(path, duration):
    """加载原始音频并裁剪/填充到目标长度"""
    try:
        audio, _ = librosa.load(path, sr=SAMPLE_RATE, duration=duration)
        if len(audio) < TARGET_LENGTH:
             audio = np.pad(audio, (0, TARGET_LENGTH - len(audio)))
        return audio
    except Exception as e:
        print(f"错误：加载原始音频文件失败 {path}: {e}")
        return None

def load_noise(path, target_length):
    """
    加载噪音音频（例如 5 秒长），并从中 *随机截取* 目标长度（1 秒）。
    这完全复制了 train.py 中的逻辑。
    """
    try:
        # 1. 加载完整时长的噪音（例如 5 秒）
        noise_audio, _ = librosa.load(path, sr=SAMPLE_RATE)
    except Exception as e:
        print(f"错误：加载噪音文件失败 {path}: {e}")
        return None
    
    # 2. 随机截取 1 秒
    if len(noise_audio) < target_length:
        # 噪音不够 1 秒，循环填充
        padding = target_length - len(noise_audio)
        return np.pad(noise_audio, (0, padding), mode='wrap')
    else:
        # 噪音长于 1 秒（例如 5 秒），随机截取
        start_idx = np.random.randint(0, len(noise_audio) - target_length + 1)
        return noise_audio[start_idx : start_idx + target_length]

def _mix_audio(signal, noise, snr_db):
    """根据 SNR (dB) 将信号和噪声混合 (与 train.py 一致)"""
    signal_rms = np.sqrt(np.mean(signal**2)) + 1e-8
    noise_rms = np.sqrt(np.mean(noise**2)) + 1e-8
    
    scale = 10**(snr_db / 20)
    desired_noise_rms = signal_rms / scale
    gain = desired_noise_rms / noise_rms
    
    return signal + (noise * gain)

def plot_waveforms(original_audio, augmented_audio, sr, title, output_plot_path):
    """绘制波形对比图"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=True, sharey=True)
    
    # 绘制原始波形
    librosa.display.waveshow(original_audio, sr=sr, ax=ax1, color='blue', alpha=0.8)
    ax1.set_title("Original Waveform", fontsize=14)
    ax1.set_xlabel(None)
    
    # 绘制增强后波形
    librosa.display.waveshow(augmented_audio, sr=sr, ax=ax2, color='red', alpha=0.8)
    ax2.set_title(f"Augmented: {title}", fontsize=14)
    
    fig.suptitle(f"Audio Augmentation Demo\n(File: {os.path.basename(FILE_PATH_ORIGINAL)})", fontsize=16, y=1.02)
    plt.tight_layout()
    plt.savefig(output_plot_path)
    print(f"\n波形图已保存至: {output_plot_path}")
    print("正在显示图表...")
    plt.show()

def main():
    print("--- 开始可视化数据增强 ---")
    
    # 1. 加载原始音频
    original_audio = load_audio(FILE_PATH_ORIGINAL, DURATION)
    if original_audio is None:
        return
        
    # 复制一份用于操作
    augmented_audio = original_audio.copy()
    
    # 标题
    title_parts = []
    
    # --- 2. 按顺序应用增强 ---
    
    # 【增强 1：时间拉伸】
    # train.py 中的逻辑是 20% 概率
    if DO_TIME_STRETCH:
        rate = np.random.uniform(0.9, 1.1)
        augmented_audio = librosa.effects.time_stretch(y=augmented_audio, rate=rate)
        # 拉伸后修复长度
        if len(augmented_audio) < TARGET_LENGTH:
             augmented_audio = np.pad(augmented_audio, (0, TARGET_LENGTH - len(augmented_audio)))
        else:
             augmented_audio = augmented_audio[:TARGET_LENGTH]
        title_parts.append(f"Time Stretch (Rate {rate:.2f})")
        print(f"应用：时间拉伸 (Rate {rate:.2f})")

    # 【增强 2：音高变换】
    # train.py 中的逻辑是 20% 概率
    if DO_PITCH_SHIFT:
        n_steps = np.random.randint(-2, 3)
        augmented_audio = librosa.effects.pitch_shift(y=augmented_audio, sr=SAMPLE_RATE, n_steps=n_steps)
        title_parts.append(f"Pitch Shift ({n_steps} steps)")
        print(f"应用：音高变换 ({n_steps} steps)")

    # 【增强 3：噪声叠加】
    # train.py 中的逻辑是 50% 概率
    if DO_ADD_NOISE:
        print(f"正在加载并截取噪音文件: {FILE_PATH_NOISE}...")
        noise_audio = load_noise(FILE_PATH_NOISE, TARGET_LENGTH)
        
        if noise_audio is not None:
            augmented_audio = _mix_audio(augmented_audio, noise_audio, TARGET_SNR_DB)
            title_parts.append(f"Noise ({TARGET_SNR_DB}dB SNR)")
            print(f"应用：噪声叠加 (SNR {TARGET_SNR_DB}dB)")
        else:
            print("警告：无法加载噪音，已跳过噪声叠加。")

    if not title_parts:
        final_title = "No Augmentation Applied"
        print("\n未选择任何增强。")
    else:
        final_title = " + ".join(title_parts)

    # 3. 绘制波形图
    plot_waveforms(original_audio, augmented_audio, SAMPLE_RATE, final_title, OUTPUT_PLOT_PATH)

# --- 脚本入口 ---
if __name__ == "__main__":
    main()