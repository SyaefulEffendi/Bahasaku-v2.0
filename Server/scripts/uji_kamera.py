# uji_kamera.py
# Mode HURUF dan KATA dalam 1 file
# Letakkan di: scripts/uji_kamera.py

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import cv2
import numpy as np
import pickle
import sys
import tensorflow as tf
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kata'))
from feature_extractor import FeatureExtractor, N_FITUR, normalisasi_sekuens

# ════════════════════════════════════════════════════════════════
MODEL_DIR       = r'D:\Syaeful\Kuliah\Semester 4\Bahasaku V2\web\Server\app\models_ml'
CONFIDENCE_HURUF = 0.65
CONFIDENCE_KATA  = 0.65
FRAME_PER_KATA   = 30
# ════════════════════════════════════════════════════════════════

# Load model huruf (model baru .keras)
print("Memuat model huruf...")
model_huruf   = tf.keras.models.load_model(os.path.join(MODEL_DIR, 'model_huruf.keras'))
encoder_huruf = pickle.load(open(os.path.join(MODEL_DIR, 'label_encoder_huruf.pkl'), 'rb'))
print(f"Huruf: {list(encoder_huruf.classes_)}")

# Load model kata
print("Memuat model kata...")
model_kata   = tf.keras.models.load_model(os.path.join(MODEL_DIR, 'model_kata.keras'))
encoder_kata = pickle.load(open(os.path.join(MODEL_DIR, 'label_encoder_kata.pkl'), 'rb'))
print(f"Kata : {list(encoder_kata.classes_)}")

extractor    = FeatureExtractor()
buffer_kata  = deque(maxlen=FRAME_PER_KATA)
hasil        = ""
confidence_v = 0.0
mode         = 'huruf'   # mulai dengan mode huruf

print("\nKamera aktif!")
print("  H → mode HURUF  |  K → mode KATA  |  R → reset  |  Q → keluar")

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)


def prediksi_huruf(fitur, info):
    """Prediksi huruf dari 1 frame — pakai model Dense baru."""
    ada_tangan = info['ada_kanan'] or info['ada_kiri'] or info['tumpuk']
    if not ada_tangan:
        return None, 0.0

    inp        = fitur[np.newaxis, ...]               # (1, 156)
    pred       = model_huruf.predict(inp, verbose=0)
    idx        = np.argmax(pred)
    conf       = float(pred[0][idx])

    if conf < CONFIDENCE_HURUF:
        return None, conf

    return encoder_huruf.inverse_transform([idx])[0], conf


while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    fitur, info = extractor.extract(frame)
    frame = extractor.gambar_landmark(frame, info)

    ada_kanan  = info['ada_kanan']
    ada_kiri   = info['ada_kiri']
    tumpuk     = info['tumpuk']
    ada_pose   = info['hasil_mediapipe'].pose_landmarks is not None
    ada_sesuatu = ada_kanan or ada_kiri or tumpuk or ada_pose

    h_f, w_f = frame.shape[:2]

    # ── Header ─────────────────────────────────────────────────────────────
    warna_mode = (0, 200, 255) if mode == 'huruf' else (0, 200, 100)
    cv2.rectangle(frame, (0, 0), (w_f, 45), (25, 25, 25), -1)
    cv2.putText(frame,
                f"MODE: {mode.upper()}  |  H=huruf  K=kata  R=reset  Q=keluar",
                (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.55, warna_mode, 2)

    # ── MODE HURUF ──────────────────────────────────────────────────────────
    if mode == 'huruf':
        teks_hasil, confidence_v = prediksi_huruf(fitur, info)
        if teks_hasil:
            hasil = teks_hasil

        if hasil:
            cv2.putText(frame, hasil,
                        (20, 200), cv2.FONT_HERSHEY_SIMPLEX, 5.0,
                        (0, 200, 255), 8, cv2.LINE_AA)
            conf_c = (0, 220, 100) if confidence_v > 0.8 else \
                     (0, 165, 255) if confidence_v > 0.65 else (0, 80, 200)
            cv2.putText(frame, f"Confidence: {int(confidence_v*100)}%",
                        (20, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, conf_c, 2)

    # ── MODE KATA ───────────────────────────────────────────────────────────
    else:
        if ada_sesuatu:
            buffer_kata.append(fitur)

        # Progress bar buffer
        prog = int((len(buffer_kata) / FRAME_PER_KATA) * (w_f - 40))
        cv2.rectangle(frame, (20, 52), (w_f-20, 64), (60, 60, 60), -1)
        cv2.rectangle(frame, (20, 52), (20+prog, 64), (0, 200, 100), -1)
        cv2.putText(frame, f"Buffer: {len(buffer_kata)}/{FRAME_PER_KATA}",
                    (20, 82), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

        # Prediksi saat buffer penuh
        if len(buffer_kata) == FRAME_PER_KATA:
            seq       = np.array(list(buffer_kata))
            seq       = normalisasi_sekuens(seq)
            seq_input = seq[np.newaxis, ...]

            pred         = model_kata.predict(seq_input, verbose=0)
            idx          = np.argmax(pred)
            confidence_v = float(pred[0][idx])

            if confidence_v > CONFIDENCE_KATA:
                hasil = encoder_kata.inverse_transform([idx])[0].upper()
            else:
                hasil = "?"

            buffer_kata.clear()
            extractor.reset()

        if hasil:
            cv2.putText(frame, hasil,
                        (20, 200), cv2.FONT_HERSHEY_SIMPLEX, 3.0,
                        (0, 200, 100), 5, cv2.LINE_AA)
            conf_c = (0, 220, 100) if confidence_v > 0.8 else \
                     (0, 165, 255) if confidence_v > 0.65 else (0, 80, 200)
            cv2.putText(frame, f"Confidence: {int(confidence_v*100)}%",
                        (20, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, conf_c, 2)

    # Status tangan
    rh_c  = (0, 220, 100) if ada_kanan else (80, 80, 80)
    lh_c  = (0, 150, 255) if ada_kiri  else (80, 80, 80)
    occ_c = (0, 80,  255) if tumpuk    else (80, 80, 80)
    cv2.putText(frame, f"Kanan:{'✓' if ada_kanan else '○'}",
                (20, 108), cv2.FONT_HERSHEY_SIMPLEX, 0.45, rh_c, 1)
    cv2.putText(frame, f"Kiri:{'✓' if ada_kiri else '○'}",
                (120, 108), cv2.FONT_HERSHEY_SIMPLEX, 0.45, lh_c, 1)
    cv2.putText(frame, f"Tumpuk:{'YA' if tumpuk else '-'}",
                (210, 108), cv2.FONT_HERSHEY_SIMPLEX, 0.45, occ_c, 1)

    cv2.imshow('BAHASAKU V2', frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('h'):
        mode = 'huruf'
        hasil = ""
        buffer_kata.clear()
        extractor.reset()
        print("Mode: HURUF")
    elif key == ord('k'):
        mode = 'kata'
        hasil = ""
        buffer_kata.clear()
        extractor.reset()
        print("Mode: KATA")
    elif key == ord('r'):
        hasil = ""
        buffer_kata.clear()
        extractor.reset()
        print("Reset.")

extractor.tutup()
cap.release()
cv2.destroyAllWindows()