# Drone

## 📌 Project Overview
This project is a deep learning-based voice recognition system designed to identify specific drone control commands from **clean (low-noise) audio streams**.  
The system can load audio files, extract their acoustic features, and classify them using a pre-trained model to recognize **emergency commands** and **movement commands**.

---

## ✅ Implemented Features

### 1. Audio Data Processing
- Supports loading audio files in **`.wav`** format.
- Converts raw audio signals into **Mel Spectrograms** as input features for the model.
- Classifies commands into:
  - **Emergency commands** (e.g., `stop`)
  - **Movement commands** (e.g., `left`, `right`, `up`, `down`)

### 2. Deep Learning Model
- Built with **TensorFlow** and **Keras**, using a **ResNet-Conformer** Sound Event Detection (SELD) model.
- Combines the strengths of **ResNet** (convolutional feature extraction) and **Conformer** (long-term sequence modeling).

### 3. Model Training and Evaluation
- Includes a complete training script **`train.py`**.
- After training, the system can save:
  - Model file (`.keras` format)
  - Label encoder (for later inference)
- Provides an evaluation script:
  - Loads the trained model for prediction
  - Calculates recognition accuracy

---

## 🛠 Tech Stack

| Technology | Purpose |
|------------|---------|
| **Python** | Main programming language |
| **TensorFlow / Keras** | Building and training deep learning models |
| **Librosa** | Audio loading and Mel Spectrogram feature extraction |
| **NumPy** | Efficient numerical computations |
| **Scikit-learn** | Data processing and evaluation (`LabelEncoder`, `accuracy_score`, etc.) |

---