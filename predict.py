import os
import numpy as np
import librosa
import joblib
from keras.models import load_model
import warnings

# Suppress TensorFlow informational messages
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
warnings.filterwarnings('ignore', category=UserWarning, module='librosa')

# --- Configuration: Paths and Parameters ---
MODEL_PATH = '/Users/zilongzeng/Research/Drone/saved_models/resnet_conformer_drone.keras'
LABEL_ENCODER_PATH = '/Users/zilongzeng/Research/Drone/saved_models/label_encoder.joblib'
TEST_DIR = '/Users/zilongzeng/Research/Drone/test'
TOP_K = 3 # Number of top predictions to display

# --- !! Critical Parameters !! ---
# These must be identical to the parameters used in your data_pre.py script.
SAMPLE_RATE = 16000
DURATION = 1.0
N_MELS = 256
DESIRED_FRAMES = 61
EXPECTED_SAMPLES = int(SAMPLE_RATE * DURATION)

def preprocess_audio(file_path):
    """
    Loads, processes, and transforms a single audio file into a format
    suitable for model prediction, matching the training preprocessing pipeline.
    """
    try:
        # 1. Load the audio file, resampling and setting duration
        audio, _ = librosa.load(file_path, sr=SAMPLE_RATE, duration=DURATION)

        # 2. Pad or truncate the audio to the expected length
        if len(audio) < EXPECTED_SAMPLES:
            audio = np.pad(audio, (0, EXPECTED_SAMPLES - len(audio)), mode='constant')
        else:
            audio = audio[:EXPECTED_SAMPLES]

        # 3. Extract Mel spectrogram features
        mel_spec = librosa.feature.melspectrogram(y=audio, sr=SAMPLE_RATE, n_mels=N_MELS)

        # 4. Convert to log scale (decibels) and normalize
        #    This normalization must match data_pre.py
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        mel_spec_db = mel_spec_db / 80.0 + 1.0

        # 5. Pad or truncate the frames (width) to a fixed size
        current_frames = mel_spec_db.shape[1]
        if current_frames < DESIRED_FRAMES:
            pad_width = ((0, 0), (0, DESIRED_FRAMES - current_frames))
            mel_spec_db = np.pad(mel_spec_db, pad_width, mode='constant')
        elif current_frames > DESIRED_FRAMES:
            mel_spec_db = mel_spec_db[:, :DESIRED_FRAMES]

        # 6. Reshape for the model input (batch, height, width, channels)
        #    Expected final shape: (1, 256, 61, 1)
        mel_spec_db = mel_spec_db[np.newaxis, ..., np.newaxis]

        return mel_spec_db

    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return None

def main():
    """
    Main function to run the inference process.
    """
    print("Loading model...")
    try:
        # Load the trained model and the label encoder
        model = load_model(MODEL_PATH, safe_mode=False)
        label_encoder = joblib.load(LABEL_ENCODER_PATH)
        num_classes = len(label_encoder.classes_)
    except Exception as e:
        print(f"Failed to load model or label encoder: {e}")
        return

    print("Model loaded successfully.")
    print(f"Starting inference on audio files in: '{TEST_DIR}'")
    print("-" * 50)

    # Iterate through all .wav files in the test directory
    for filename in sorted(os.listdir(TEST_DIR)):
        if filename.lower().endswith('.wav'):
            file_path = os.path.join(TEST_DIR, filename)

            # Preprocess the audio file
            processed_input = preprocess_audio(file_path)

            if processed_input is not None:
                # Get model predictions (probabilities)
                prediction = model.predict(processed_input, verbose=0)[0]

                # Get indices of the top-k predictions
                top_k_indices = np.argsort(prediction)[-TOP_K:][::-1]

                print(f"File: {filename}")
                for i, index in enumerate(top_k_indices):
                    label = label_encoder.classes_[index]
                    probability = prediction[index]
                    print(f"  - Top {i+1}: {label:<15} (Probability: {probability:.4f})")
                print("-" * 50)

if __name__ == '__main__':
    main()