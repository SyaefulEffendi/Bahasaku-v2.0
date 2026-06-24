# train_huruf.py
# Training model huruf dari dataset baru (156 fitur, 1 frame per sampel)
# Jalankan: python train_huruf.py

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
from tensorflow.keras.models   import Model
from tensorflow.keras.layers   import Input, Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'kata'))
from feature_extractor import N_FITUR

# ════════════════════════════════════════════════════════════════
CSV_PATH  = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'dataset', 'huruf', 'dataset_huruf.csv'))
MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'app', 'models_ml'))
# ════════════════════════════════════════════════════════════════

os.makedirs(MODEL_DIR, exist_ok=True)

# Load dataset
print("=" * 50)
print("  TRAINING MODEL HURUF")
print("=" * 50)

if not os.path.exists(CSV_PATH):
    print(f"ERROR: {CSV_PATH} tidak ditemukan.")
    print("Jalankan rekam_huruf.py terlebih dahulu.")
    sys.exit(1)

df = pd.read_csv(CSV_PATH)
print(f"Total baris  : {len(df)}")
print(f"Fitur/baris  : {df.shape[1]-1} (harus {N_FITUR})")

if df.shape[1]-1 != N_FITUR:
    print(f"ERROR: Fitur tidak sesuai! Rekam ulang dengan feature_extractor terbaru.")
    sys.exit(1)

X = df.drop('label', axis=1).values.astype(np.float32)
y = df['label'].values

# Distribusi
huruf_unik, jumlah = np.unique(y, return_counts=True)
print("\nDistribusi huruf:")
for h, j in zip(huruf_unik, jumlah):
    print(f"  {h}: {j} sampel")

if len(huruf_unik) < 2:
    print("\nERROR: Butuh minimal 2 huruf.")
    sys.exit(1)

# Encode
encoder   = LabelEncoder()
y_encoded = encoder.fit_transform(y)
n_kelas   = len(encoder.classes_)
print(f"\nTotal huruf: {n_kelas} → {list(encoder.classes_)}")

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)
print(f"Training: {len(X_train)} | Testing: {len(X_test)}")

cw = compute_class_weight('balanced', classes=np.unique(y_encoded), y=y_encoded)
cw_dict = dict(enumerate(cw))

# Model — huruf = 1 frame = klasifikasi biasa (Dense, bukan LSTM)
def buat_model(n_fitur, n_kelas):
    inp = Input(shape=(n_fitur,))
    x   = Dense(512, activation='relu')(inp)
    x   = BatchNormalization()(x)
    x   = Dropout(0.4)(x)
    x   = Dense(256, activation='relu')(x)
    x   = BatchNormalization()(x)
    x   = Dropout(0.3)(x)
    x   = Dense(128, activation='relu')(x)
    x   = Dropout(0.3)(x)
    x   = Dense(64,  activation='relu')(x)
    out = Dense(n_kelas, activation='softmax')(x)
    return Model(inp, out)

print("\nMembangun model Dense...")
model = buat_model(N_FITUR, n_kelas)
model.compile(
    optimizer=tf.keras.optimizers.Adam(0.001),
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)
model.summary()

model_path = os.path.join(MODEL_DIR, 'model_huruf.keras')
callbacks  = [
    EarlyStopping(monitor='val_accuracy', patience=20,
                  restore_best_weights=True, verbose=1),
    ReduceLROnPlateau(monitor='val_loss', factor=0.5,
                      patience=8, min_lr=1e-6, verbose=1),
    ModelCheckpoint(model_path, monitor='val_accuracy',
                    save_best_only=True, verbose=0),
]

print("\nMulai training...\n")
history = model.fit(
    X_train, y_train,
    epochs=150,
    batch_size=32,
    validation_data=(X_test, y_test),
    callbacks=callbacks,
    class_weight=cw_dict,
    verbose=1
)

# Evaluasi
loss, acc = model.evaluate(X_test, y_test, verbose=0)
print(f"\n{'='*40}")
print(f"  Akurasi  : {acc*100:.2f}%")
print(f"  Loss     : {loss:.4f}")
print(f"{'='*40}")

y_pred = np.argmax(model.predict(X_test, verbose=0), axis=1)
print("\nDetail per huruf:")
print(classification_report(y_test, y_pred, target_names=list(encoder.classes_)))

# Confusion matrix
cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(max(8, n_kelas), max(7, n_kelas)))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=encoder.classes_, yticklabels=encoder.classes_)
plt.title('Confusion Matrix - Huruf')
plt.ylabel('Benar')
plt.xlabel('Prediksi')
plt.tight_layout()
plt.savefig(os.path.join(MODEL_DIR, 'confusion_matrix_huruf.png'))
print(f"Confusion matrix disimpan.")

# Simpan
model.save(model_path)
enc_path = os.path.join(MODEL_DIR, 'label_encoder_huruf.pkl')
with open(enc_path, 'wb') as f:
    pickle.dump(encoder, f)

print(f"\nModel   : {model_path}")
print(f"Encoder : {enc_path}")

if acc >= 0.85:
    print("\n✓ Akurasi bagus!")
elif acc >= 0.70:
    print("\n~ Akurasi cukup. Tambah data untuk hasil lebih baik.")
else:
    print("\n✗ Akurasi rendah. Tambah sampel per huruf (min 200).")