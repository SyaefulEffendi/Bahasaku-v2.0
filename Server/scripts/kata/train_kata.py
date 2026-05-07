# train_kata_v2.py
# ─────────────────────────────────────────────────────────────────────────────
# Training model Bahasaku V2 dengan:
#   - Input: 156 fitur (hybrid: hand + pose + optical flow + flags)
#   - Model: Bidirectional LSTM + Multi-Head Attention
#   - Robust terhadap oklusi tangan
#
# Jalankan: python train_kata_v2.py
# ─────────────────────────────────────────────────────────────────────────────

import os
import sys
import numpy as np
import pandas as pd
import pickle
import matplotlib
matplotlib.use('Agg')  # non-interactive backend
import matplotlib.pyplot as plt

from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.preprocessing   import LabelEncoder
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics         import classification_report, confusion_matrix
import seaborn as sns

import tensorflow as tf
from tensorflow.keras.models  import Model
from tensorflow.keras.layers  import (
    Input, LSTM, Bidirectional, Dense, Dropout,
    LayerNormalization, MultiHeadAttention,
    GlobalAveragePooling1D, Concatenate, Masking
)
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from feature_extractor import N_FITUR

# ════════════════════════════════════════════════════════════════════
#  KONFIGURASI
# ════════════════════════════════════════════════════════════════════
FRAME_PER_VIDEO = 30
CSV_PATH = r'D:\Syaeful\Kuliah\Semester 4\Bahasaku V2\web\Server\dataset\kata\dataset_kata_v2.csv'
MODEL_DIR = r'D:\Syaeful\Kuliah\Semester 4\Bahasaku V2\web\Server\app\models_ml'
os.makedirs(MODEL_DIR, exist_ok=True)
# ════════════════════════════════════════════════════════════════════


# ─── 1. Load & Validasi Data ─────────────────────────────────────────────────

def load_dataset(csv_path):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV tidak ditemukan: {csv_path}")

    df     = pd.read_csv(csv_path)
    labels = df['label'].values
    coords = df.drop('label', axis=1).values

    print(f"Total baris CSV : {len(df)}")
    print(f"Fitur per baris : {coords.shape[1]} (expected {N_FITUR})")

    if coords.shape[1] != N_FITUR:
        raise ValueError(
            f"Jumlah fitur tidak sesuai: {coords.shape[1]} vs {N_FITUR}. "
            f"Pastikan dataset direkam dengan feature_extractor.py versi terbaru."
        )

    X, y = [], []
    for i in range(0, len(coords) - FRAME_PER_VIDEO + 1, FRAME_PER_VIDEO):
        chunk_labels = labels[i:i+FRAME_PER_VIDEO]
        if len(set(chunk_labels)) == 1:  # semua frame sama labelnya
            X.append(coords[i:i+FRAME_PER_VIDEO])
            y.append(chunk_labels[0])

    X = np.array(X, dtype=np.float32)  # (N, 30, 156)
    y = np.array(y)

    return X, y


print("=" * 55)
print("  BAHASAKU V2 - TRAINING")
print("=" * 55)

X, y = load_dataset(CSV_PATH)

print(f"\nShape dataset : {X.shape}")
print(f"Jumlah video  : {len(X)}")

# Distribusi kelas
unique, counts = np.unique(y, return_counts=True)
print("\nDistribusi kata:")
for kata, jml in zip(unique, counts):
    bar = "█" * jml
    print(f"  {kata:15s}: {jml:3d} video  {bar}")

if len(X) == 0:
    raise ValueError("Dataset kosong!")
if len(unique) < 2:
    raise ValueError(f"Butuh minimal 2 kata, hanya ada: {unique}")


# ─── 2. Encode Label ──────────────────────────────────────────────────────────

encoder   = LabelEncoder()
y_encoded = encoder.fit_transform(y)
n_classes = len(encoder.classes_)

print(f"\nKata dikenali ({n_classes}): {list(encoder.classes_)}")

# Simpan encoder
enc_path = os.path.join(MODEL_DIR, 'label_encoder_kata_v2.pkl')
with open(enc_path, 'wb') as f:
    pickle.dump(encoder, f)
print(f"Encoder disimpan: {enc_path}")


# ─── 3. Split Data ────────────────────────────────────────────────────────────

X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded,
    test_size=0.2,
    random_state=42,
    stratify=y_encoded
)

print(f"\nData training : {len(X_train)} video")
print(f"Data testing  : {len(X_test)} video")

# Class weights untuk data tidak seimbang
class_weights = compute_class_weight(
    class_weight='balanced',
    classes=np.unique(y_encoded),
    y=y_encoded
)
cw_dict = dict(enumerate(class_weights))
print(f"\nClass weights : {cw_dict}")


# ─── 4. Arsitektur Model ─────────────────────────────────────────────────────

def build_model(seq_len, feat_dim, num_classes):
    """
    Bidirectional LSTM + Multi-Head Attention
    
    Keunggulan untuk kasus oklusi:
    - Bi-LSTM: melihat konteks maju DAN mundur (frame sebelum & sesudah oklusi)
    - Attention: belajar mengabaikan frame yang 'noisy' saat oklusi
    - LayerNorm: stabilkan training dengan data yang tidak konsisten
    """
    inputs = Input(shape=(seq_len, feat_dim), name='input_sequence')

    # Masking: abaikan frame yang semua nol (zero-padding)
    x = Masking(mask_value=0.0)(inputs)

    # ── Layer 1: Bi-LSTM ──────────────────────────────────────────
    x = Bidirectional(
        LSTM(128, return_sequences=True, dropout=0.1, recurrent_dropout=0.1),
        name='bilstm_1'
    )(x)
    x = LayerNormalization()(x)
    x = Dropout(0.3)(x)

    # ── Attention Layer ───────────────────────────────────────────
    # Model belajar fokus ke frame penting, abaikan frame oklusi
    attn_out = MultiHeadAttention(
        num_heads=4, key_dim=32, name='multi_head_attention'
    )(x, x)
    x = x + attn_out  # residual connection
    x = LayerNormalization()(x)

    # ── Layer 2: Bi-LSTM ──────────────────────────────────────────
    x = Bidirectional(
        LSTM(64, return_sequences=True, dropout=0.1),
        name='bilstm_2'
    )(x)
    x = LayerNormalization()(x)

    # ── Global pooling ────────────────────────────────────────────
    x = GlobalAveragePooling1D()(x)

    # ── Dense head ────────────────────────────────────────────────
    x = Dense(128, activation='relu')(x)
    x = Dropout(0.3)(x)
    x = Dense(64, activation='relu')(x)
    x = Dropout(0.2)(x)

    outputs = Dense(num_classes, activation='softmax', name='output')(x)

    model = Model(inputs, outputs)
    return model


print("\nMembangun model Bi-LSTM + Attention...")
model = build_model(FRAME_PER_VIDEO, N_FITUR, n_classes)
model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)
model.summary()

total_params = model.count_params()
print(f"\nTotal parameter: {total_params:,}")


# ─── 5. Training ─────────────────────────────────────────────────────────────

best_model_path = os.path.join(MODEL_DIR, 'model_kata_v2_best.h5')

callbacks = [
    EarlyStopping(
        monitor='val_accuracy',
        patience=30,
        restore_best_weights=True,
        verbose=1
    ),
    ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=10,
        min_lr=1e-6,
        verbose=1
    ),
    ModelCheckpoint(
        best_model_path,
        monitor='val_accuracy',
        save_best_only=True,
        verbose=0
    )
]

print("\nMulai training...\n")
history = model.fit(
    X_train, y_train,
    epochs=200,
    batch_size=16,
    validation_data=(X_test, y_test),
    callbacks=callbacks,
    class_weight=cw_dict,
    verbose=1
)


# ─── 6. Evaluasi ─────────────────────────────────────────────────────────────

loss, acc = model.evaluate(X_test, y_test, verbose=0)
print(f"\n{'='*40}")
print(f"Akurasi Test  : {acc * 100:.2f}%")
print(f"Loss Test     : {loss:.4f}")
print(f"{'='*40}")

# Classification report
y_pred    = np.argmax(model.predict(X_test, verbose=0), axis=1)
kata_list = list(encoder.classes_)
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=kata_list))

# Confusion matrix
cm = confusion_matrix(y_test, y_pred)
print("Confusion Matrix:")
print(cm)

# Plot confusion matrix
plt.figure(figsize=(max(6, n_classes), max(5, n_classes)))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=kata_list, yticklabels=kata_list)
plt.title('Confusion Matrix - Bahasaku V2')
plt.ylabel('True Label')
plt.xlabel('Predicted Label')
cm_path = os.path.join(MODEL_DIR, 'confusion_matrix_v2.png')
plt.tight_layout()
plt.savefig(cm_path)
print(f"\nConfusion matrix disimpan: {cm_path}")

# Plot training history
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
ax1.plot(history.history['accuracy'],     label='Train')
ax1.plot(history.history['val_accuracy'], label='Validation')
ax1.set_title('Accuracy')
ax1.legend()
ax2.plot(history.history['loss'],     label='Train')
ax2.plot(history.history['val_loss'], label='Validation')
ax2.set_title('Loss')
ax2.legend()
hist_path = os.path.join(MODEL_DIR, 'training_history_v2.png')
plt.tight_layout()
plt.savefig(hist_path)
print(f"Training history disimpan: {hist_path}")


# ─── 7. Simpan Model ─────────────────────────────────────────────────────────

final_path = os.path.join(MODEL_DIR, 'model_kata_v2.h5')
model.save(final_path)
print(f"\nModel disimpan: {final_path}")
print(f"Encoder disimpan: {enc_path}")
print(f"\nSelesai! Akurasi final: {acc * 100:.2f}%")

# Saran jika akurasi rendah
if acc < 0.70:
    print("\n⚠  Akurasi masih rendah. Saran:")
    print("   1. Tambah data: minimal 50 video per kata")
    print("   2. Pastikan variasi kecepatan & sudut tangan")
    print("   3. Cek distribusi kelas — jangan terlalu tidak seimbang")
    print("   4. Jalankan debug_kamera.py untuk verifikasi fitur")
elif acc < 0.85:
    print("\n~  Akurasi cukup. Untuk meningkatkan:")
    print("   1. Tambah 20-30 video per kata")
    print("   2. Rekam dari beberapa orang berbeda")
else:
    print("\n✓  Akurasi bagus! Model siap digunakan.")
