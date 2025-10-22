import os
import numpy as np
import tensorflow as tf
from keras.optimizers import Adam
from keras.callbacks import ModelCheckpoint, EarlyStopping
from model import build_model
import matplotlib.pyplot as plt

#TODO: 数据集扩展，增加生成数据集代码
#TODO： 迁移代码到服务器侧
#TODO： 删除local branch
# --- 1. Define Paths and Parameters ---
PROCESSED_DATA_PATH = "dataset/processed/"
MODELS_PATH = "saved_models/"
HISTORY_PATH = "saved_models/training_history.npy"
PLOT_PATH = "result/training_history.png" # The plot will be saved in the project root directory

# Training parameters
EPOCHS = 50
BATCH_SIZE = 32
LEARNING_RATE = 0.0001

# --- 2. Load Data ---
def load_data(path):
    """Load features and labels from a .npz file."""
    with np.load(path) as data:
        return data['features'], data['labels']

print("Loading datasets...")
X_train, y_train = load_data(os.path.join(PROCESSED_DATA_PATH, 'train_data.npz'))
X_val, y_val = load_data(os.path.join(PROCESSED_DATA_PATH, 'val_data.npz'))
X_test, y_test = load_data(os.path.join(PROCESSED_DATA_PATH, 'test_data.npz'))

print(f"Training set shape: {X_train.shape}")
print(f"Validation set shape: {X_val.shape}")

# --- 3. Prepare Data for the Model ---

# Get number of classes and input shape
NUM_CLASSES = len(np.unique(y_train))
INPUT_SHAPE = X_train.shape[1:]

# Convert labels to one-hot encoding
y_train_one_hot = tf.keras.utils.to_categorical(y_train, num_classes=NUM_CLASSES)
y_val_one_hot = tf.keras.utils.to_categorical(y_val, num_classes=NUM_CLASSES)
y_test_one_hot = tf.keras.utils.to_categorical(y_test, num_classes=NUM_CLASSES)

print(f"Number of classes: {NUM_CLASSES}")
print(f"Model input shape: {INPUT_SHAPE}")

# --- 4. Build, Compile, and Train the Model ---

# Build the model
model = build_model(input_shape=INPUT_SHAPE, num_classes=NUM_CLASSES)

# Compile the model
model.compile(
    optimizer=Adam(learning_rate=LEARNING_RATE),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

model.summary()

# Define callbacks
checkpoint_path = os.path.join(MODELS_PATH, "resnet_conformer_drone.keras")
model_checkpoint = ModelCheckpoint(
    filepath=checkpoint_path,
    save_best_only=True,
    monitor='val_accuracy',
    mode='max',
    verbose=1
)

early_stopping = EarlyStopping(
    monitor='val_accuracy',
    patience=10,
    verbose=1,
    restore_best_weights=True
)

# Train the model
print("\nStarting model training...")

history = model.fit(
    X_train,     y_train_one_hot,
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    validation_data=(X_val, y_val_one_hot),
    callbacks=[model_checkpoint, early_stopping]
)





print("\n✅ Training complete.")

# --- 5. Evaluate the Model ---
print("\nEvaluating model performance on the test set...")
test_loss, test_accuracy = model.evaluate(X_test, y_test_one_hot, verbose=0)
print(f"Test Set Loss: {test_loss:.4f}")
print(f"Test Set Accuracy: {test_accuracy:.4f}")

# --- 6. Save and Plot Training History ---
print("\nSaving training history and generating plots...")

# Save history object
np.save(HISTORY_PATH, history.history)
print(f"Training history saved to: {HISTORY_PATH}")

# Plot accuracy and loss curves
plt.style.use('seaborn-v0_8-whitegrid')
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# Plot training & validation accuracy values
ax1.plot(history.history['accuracy'])
ax1.plot(history.history['val_accuracy'])
ax1.set_title('Model Accuracy')
ax1.set_ylabel('Accuracy')
ax1.set_xlabel('Epoch')
ax1.legend(['Train', 'Validation'], loc='upper left')

# Plot training & validation loss values
ax2.plot(history.history['loss'])
ax2.plot(history.history['val_loss'])
ax2.set_title('Model Loss')
ax2.set_ylabel('Loss')
ax2.set_xlabel('Epoch')
ax2.legend(['Train', 'Validation'], loc='upper left')

# Save the figure
plt.savefig(PLOT_PATH)
print(f"Training plot saved to: {PLOT_PATH}")
plt.show()