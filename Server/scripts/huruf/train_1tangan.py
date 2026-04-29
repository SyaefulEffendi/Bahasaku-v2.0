import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
import pickle
import os

print("Membaca dataset 1 tangan...")
df = pd.read_csv('../../dataset/dataset_1tangan.csv')

print(f"Total sampel : {len(df)}")
print(f"Distribusi  :\n{df['label'].value_counts().to_string()}\n")

X = df.drop('label', axis=1).values
y = df['label'].values

assert X.shape[1] == 63, f"Fitur harus 63, dapat {X.shape[1]}"

encoder = LabelEncoder()
y_encoded = encoder.fit_transform(y)

os.makedirs('../../app/models_ml', exist_ok=True)
with open('../../app/models_ml/label_encoder_1tangan.pkl', 'wb') as f:
    pickle.dump(encoder, f)
print(f"Huruf dikenali: {list(encoder.classes_)}\n")

X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)

model = Sequential([
    Dense(128, activation='relu', input_shape=(63,)),
    BatchNormalization(),
    Dropout(0.3),
    Dense(64, activation='relu'),
    BatchNormalization(),
    Dropout(0.2),
    Dense(32, activation='relu'),
    Dense(len(encoder.classes_), activation='softmax')
])

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

callbacks = [
    EarlyStopping(monitor='val_accuracy', patience=10, restore_best_weights=True),
    ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-6)
]

print("Mulai training model 1 tangan...\n")
model.fit(
    X_train, y_train,
    epochs=100,
    batch_size=32,
    validation_data=(X_test, y_test),
    callbacks=callbacks
)

loss, acc = model.evaluate(X_test, y_test, verbose=0)
print(f"\nAkurasi model 1 tangan: {acc * 100:.2f}%")

model.save('../../app/models_ml/model_1tangan.h5')
print("Model disimpan di ../../app/models_ml/model_1tangan.h5")