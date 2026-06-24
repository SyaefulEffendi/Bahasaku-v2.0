# train_kata.py
# Jalankan dari folder kata/: python train_kata.py

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
                                       MultiHeadAttention, GlobalAveragePooling1D)
# CATATAN: Masking layer dihapus — tidak kompatibel Keras 3

from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from feature_extractor import N_FITUR

# ════════════════════════════════════════════════════════════════════
CSV_PATH  = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'dataset', 'kata', 'dataset_kata.csv'))
MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'app', 'models_ml'))
FRAME_PER_VIDEO = 30
# ════════════════════════════════════════════════════════════════════

os.makedirs(MODEL_DIR, exist_ok=True)

print("=" * 50)
print("  BAHASAKU V2 - TRAINING KATA")
print("=" * 50)

if not os.path.exists(CSV_PATH):
    print(f"ERROR: {CSV_PATH} tidak ditemukan.")
    sys.exit(1)

df     = pd.read_csv(CSV_PATH)
labels = df['label'].values
data   = df.drop('label', axis=1).values

print(f"Total baris : {len(df)}")
print(f"Fitur/baris : {data.shape[1]} (harus {N_FITUR})")

if data.shape[1] != N_FITUR:
    print("ERROR: Jumlah fitur salah!")
    sys.exit(1)

# Kelompokkan per video
X, y = [], []
for i in range(0, len(data) - FRAME_PER_VIDEO + 1, FRAME_PER_VIDEO):
    blok = labels[i:i+FRAME_PER_VIDEO]
    if len(set(blok)) == 1:
        X.append(data[i:i+FRAME_PER_VIDEO])
        y.append(blok[0])

X = np.array(X, dtype=np.float32)
y = np.array(y)

print(f"Total video : {len(X)}")

kata_unik, jumlah = np.unique(y, return_counts=True)
print("\nDistribusi:")
for kata, jml in zip(kata_unik, jumlah):
    print(f"  {kata:15s}: {jml} video")

if len(X) == 0 or len(kata_unik) < 2:
    print("ERROR: Dataset kosong atau kurang dari 2 kata.")
    sys.exit(1)

# Encode
encoder   = LabelEncoder()
y_encoded = encoder.fit_transform(y)
n_kelas   = len(encoder.classes_)
print(f"\nKata ({n_kelas}): {list(encoder.classes_)}")

enc_path = os.path.join(MODEL_DIR, 'label_encoder_kata.pkl')
with open(enc_path, 'wb') as f:
    pickle.dump(encoder, f)

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)
print(f"Training : {len(X_train)} | Testing : {len(X_test)}")

cw      = compute_class_weight('balanced', classes=np.unique(y_encoded), y=y_encoded)
cw_dict = dict(enumerate(cw))

# Model TANPA Masking layer
def buat_model(panjang_seq, n_fitur, n_kelas):
    inp = Input(shape=(panjang_seq, n_fitur))

    x = Bidirectional(LSTM(128, return_sequences=True,
                           dropout=0.1, recurrent_dropout=0.1))(inp)
    x = LayerNormalization()(x)
    x = Dropout(0.3)(x)

    attn = MultiHeadAttention(num_heads=4, key_dim=32)(x, x)
    x    = x + attn
    x    = LayerNormalization()(x)

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

model_path = os.path.join(MODEL_DIR, 'model_kata.keras')
callbacks  = [
    EarlyStopping(monitor='val_accuracy', patience=30,
                  restore_best_weights=True, verbose=1),
    ReduceLROnPlateau(monitor='val_loss', factor=0.5,
                      patience=10, min_lr=1e-6, verbose=1),
    ModelCheckpoint(model_path, monitor='val_accuracy',
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

loss, acc = model.evaluate(X_test, y_test, verbose=0)
print(f"\n{'='*40}")
print(f"  Akurasi : {acc*100:.2f}%")
print(f"  Loss    : {loss:.4f}")
print(f"{'='*40}")

y_pred = np.argmax(model.predict(X_test, verbose=0), axis=1)
print("\nDetail per kata:")
print(classification_report(y_test, y_pred, target_names=list(encoder.classes_)))

cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(max(6, n_kelas), max(5, n_kelas)))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=encoder.classes_, yticklabels=encoder.classes_)
plt.title('Confusion Matrix - Kata')
plt.tight_layout()
plt.savefig(os.path.join(MODEL_DIR, 'confusion_matrix_kata.png'))
print(f"Confusion matrix disimpan.")

model.save(model_path)
print(f"\nModel   : {model_path}")
print(f"Encoder : {enc_path}")

if acc >= 0.85:
    print("\n✓ Akurasi bagus! Lanjut ke uji_kamera.py")
elif acc >= 0.70:
    print("\n~ Akurasi cukup.")
else:
    print("\n✗ Akurasi rendah. Cek confusion matrix untuk tahu kata mana yang bermasalah.")