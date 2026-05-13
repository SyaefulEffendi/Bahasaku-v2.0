# train_kata.py
# ─────────────────────────────────────────────────────────────────────────────
# Training model dari dataset yang sudah direkam.
# Jalankan SETELAH semua kata selesai direkam.
#
# Jalankan: python train_kata.py
# ─────────────────────────────────────────────────────────────────────────────

import os, sys, pickle
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from sklearn.model_selection     import train_test_split
from sklearn.preprocessing       import LabelEncoder
from sklearn.utils.class_weight  import compute_class_weight
from sklearn.metrics             import classification_report, confusion_matrix
import seaborn as sns

import tensorflow as tf
from tensorflow.keras.models  import Model
from tensorflow.keras.layers  import (Input, LSTM, Bidirectional, Dense,
                                       Dropout, LayerNormalization,
                                       MultiHeadAttention, GlobalAveragePooling1D,
                                       Masking)
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from feature_extractor import N_FITUR

# ════════════════════════════════════════════════════════════════════
CSV_PATH  = r'D:\Syaeful\Kuliah\Semester 4\Bahasaku V2\web\Server\dataset\kata\dataset_kata.csv'
MODEL_DIR = r'D:\Syaeful\Kuliah\Semester 4\Bahasaku V2\web\Server\app\models_ml'
FRAME_PER_VIDEO = 30
# ════════════════════════════════════════════════════════════════════

os.makedirs(MODEL_DIR, exist_ok=True)

# ── 1. Load dataset ──────────────────────────────────────────────────────────
print("=" * 50)
print("  BAHASAKU V2 - TRAINING")
print("=" * 50)

if not os.path.exists(CSV_PATH):
    print(f"ERROR: File tidak ditemukan: {CSV_PATH}")
    print("Jalankan rekam_kata_webcam.py terlebih dahulu.")
    sys.exit(1)

df     = pd.read_csv(CSV_PATH)
labels = df['label'].values
data   = df.drop('label', axis=1).values

print(f"Total baris  : {len(df)}")
print(f"Fitur/baris  : {data.shape[1]} (harus {N_FITUR})")

if data.shape[1] != N_FITUR:
    print(f"ERROR: Jumlah fitur salah! Rekam ulang dataset dengan feature_extractor terbaru.")
    sys.exit(1)

# Kelompokkan per video (setiap 30 baris = 1 video)
X, y = [], []
for i in range(0, len(data) - FRAME_PER_VIDEO + 1, FRAME_PER_VIDEO):
    blok_label = labels[i:i+FRAME_PER_VIDEO]
    if len(set(blok_label)) == 1:   # semua baris dalam blok sama labelnya
        X.append(data[i:i+FRAME_PER_VIDEO])
        y.append(blok_label[0])

X = np.array(X, dtype=np.float32)  # (N_video, 30, 156)
y = np.array(y)

print(f"\nTotal video  : {len(X)}")
print(f"Shape        : {X.shape}")

# Distribusi per kata
kata_unik, jumlah = np.unique(y, return_counts=True)
print("\nDistribusi:")
for kata, jml in zip(kata_unik, jumlah):
    bar = "█" * jml
    print(f"  {kata:15s}: {jml:3d}  {bar}")

if len(X) == 0 or len(kata_unik) < 2:
    print("\nERROR: Dataset terlalu sedikit atau hanya 1 kata.")
    sys.exit(1)

# ── 2. Encode label ──────────────────────────────────────────────────────────
encoder   = LabelEncoder()
y_encoded = encoder.fit_transform(y)
n_kelas   = len(encoder.classes_)
print(f"\nKata ({n_kelas}): {list(encoder.classes_)}")

enc_path = os.path.join(MODEL_DIR, 'label_encoder_kata.pkl')
with open(enc_path, 'wb') as f:
    pickle.dump(encoder, f)

# ── 3. Split data ────────────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)
print(f"\nTraining : {len(X_train)} video")
print(f"Testing  : {len(X_test)} video")

cw = compute_class_weight('balanced', classes=np.unique(y_encoded), y=y_encoded)
cw_dict = dict(enumerate(cw))

# ── 4. Bangun model ──────────────────────────────────────────────────────────
def buat_model(panjang_seq, n_fitur, n_kelas):
    inp = Input(shape=(panjang_seq, n_fitur))
    # Catatan: tidak pakai Masking layer karena tidak kompatibel Keras 3

    # Bi-LSTM layer 1
    x = Bidirectional(LSTM(128, return_sequences=True,
                           dropout=0.1, recurrent_dropout=0.1))(inp)
    x = LayerNormalization()(x)
    x = Dropout(0.3)(x)

    # Attention — fokus ke frame penting, abaikan frame oklusi
    attn = MultiHeadAttention(num_heads=4, key_dim=32)(x, x)
    x    = x + attn
    x    = LayerNormalization()(x)

    # Bi-LSTM layer 2
    x = Bidirectional(LSTM(64, return_sequences=True, dropout=0.1))(x)
    x = GlobalAveragePooling1D()(x)

    x = Dense(128, activation='relu')(x)
    x = Dropout(0.3)(x)
    x = Dense(64,  activation='relu')(x)
    x = Dropout(0.2)(x)

    out = Dense(n_kelas, activation='softmax')(x)
    return Model(inp, out)

print("\nMembangun model Bi-LSTM + Attention...")
model = buat_model(FRAME_PER_VIDEO, N_FITUR, n_kelas)
model.compile(
    optimizer=tf.keras.optimizers.Adam(0.001),
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)
model.summary()

# ── 5. Training ──────────────────────────────────────────────────────────────
model_terbaik = os.path.join(MODEL_DIR, 'model_kata.keras')
callbacks = [
    EarlyStopping(monitor='val_accuracy', patience=30,
                  restore_best_weights=True, verbose=1),
    ReduceLROnPlateau(monitor='val_loss', factor=0.5,
                      patience=10, min_lr=1e-6, verbose=1),
    ModelCheckpoint(model_terbaik, monitor='val_accuracy',
                    save_best_only=True, verbose=0),
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

# ── 6. Evaluasi ──────────────────────────────────────────────────────────────
loss, acc = model.evaluate(X_test, y_test, verbose=0)
print(f"\n{'='*40}")
print(f"  Akurasi  : {acc*100:.2f}%")
print(f"  Loss     : {loss:.4f}")
print(f"{'='*40}")

y_pred = np.argmax(model.predict(X_test, verbose=0), axis=1)
print("\nDetail per kata:")
print(classification_report(y_test, y_pred, target_names=list(encoder.classes_)))

# Confusion matrix
cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(max(6, n_kelas), max(5, n_kelas)))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=encoder.classes_, yticklabels=encoder.classes_)
plt.title('Confusion Matrix')
plt.ylabel('Benar')
plt.xlabel('Prediksi')
plt.tight_layout()
plt.savefig(os.path.join(MODEL_DIR, 'confusion_matrix_kata.png'))
print(f"Confusion matrix → {MODEL_DIR}\\confusion_matrix_kata.png")

# ── 7. Simpan model ──────────────────────────────────────────────────────────
model_path = os.path.join(MODEL_DIR, 'model_kata.keras')
model.save(model_path)
print(f"\nModel disimpan  : {model_path}")
print(f"Encoder disimpan: {enc_path}")

if acc >= 0.85:
    print("\n✓ Akurasi bagus! Lanjut ke uji_kamera.py")
elif acc >= 0.70:
    print("\n~ Akurasi cukup. Tambah data jika mau lebih baik.")
else:
    print("\n✗ Akurasi rendah. Rekam lebih banyak video (min 50/kata).")
    print("  Pastikan gerakan dilakukan dengan konsisten.")