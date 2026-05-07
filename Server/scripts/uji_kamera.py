# uji_kamera_v2.py
# ─────────────────────────────────────────────────────────────────────────────
# Uji model Bahasaku V2 secara real-time
# Mendukung: huruf (YOLO V1) + kata (Bi-LSTM V2 dengan 156 fitur)
#
# Jalankan: python uji_kamera_v2.py
# ─────────────────────────────────────────────────────────────────────────────

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import cv2
import numpy as np
import pickle
import sys
import tensorflow as tf
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from feature_extractor import FeatureExtractor, N_FITUR, normalize_sequence

# ════════════════════════════════════════════════════════════════════
#  KONFIGURASI
# ════════════════════════════════════════════════════════════════════
MODEL_DIR        = r'D:\Syaeful\Kuliah\Semester 4\Bahasaku V2\web\Server\app\models_ml'
CONFIDENCE_KATA  = 0.65     # threshold confidence untuk menampilkan prediksi
FRAME_PER_VIDEO  = 30
MODE             = 'kata'   # 'huruf' atau 'kata'
# ════════════════════════════════════════════════════════════════════

# ─── Load model kata V2 ───────────────────────────────────────────────────────
print("Memuat model kata V2...")
model_kata = tf.keras.models.load_model(
    os.path.join(MODEL_DIR, 'model_kata_v2.h5')
)
with open(os.path.join(MODEL_DIR, 'label_encoder_kata_v2.pkl'), 'rb') as f:
    encoder_kata = pickle.load(f)
print(f"Kata yang dikenali: {list(encoder_kata.classes_)}")

# ─── (Opsional) Load model huruf V1 ─────────────────────────────────────────
# Uncomment jika mau mode huruf juga aktif
# import mediapipe as mp
# import pickle as pkl
# mp_hands = mp.solutions.hands
# hands    = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7)
# model_1t = tf.keras.models.load_model(os.path.join(MODEL_DIR, 'model_1tangan.h5'))
# model_2t = tf.keras.models.load_model(os.path.join(MODEL_DIR, 'model_2tangan.h5'))
# with open(os.path.join(MODEL_DIR, 'label_encoder_1tangan.pkl'), 'rb') as f:
#     encoder_1t = pkl.load(f)
# with open(os.path.join(MODEL_DIR, 'label_encoder_2tangan.pkl'), 'rb') as f:
#     encoder_2t = pkl.load(f)

# ─── Setup ───────────────────────────────────────────────────────────────────
extractor    = FeatureExtractor(min_detection_confidence=0.5)
buffer_kata  = deque(maxlen=FRAME_PER_VIDEO)
hasil_kata   = ""
confidence_k = 0.0
mode         = MODE

print("\nKamera aktif!")
print("  H → mode HURUF")
print("  K → mode KATA")
print("  R → reset buffer")
print("  Q → keluar")


def draw_mode_header(frame, mode):
    h, w = frame.shape[:2]
    c = (0, 200, 255) if mode == 'huruf' else (255, 150, 0)
    cv2.rectangle(frame, (0, 0), (w, 50), (25, 25, 25), -1)
    cv2.putText(frame,
                f"BAHASAKU V2  |  MODE: {mode.upper()}  |  H=huruf  K=kata  R=reset  Q=keluar",
                (10, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.55, c, 2)


def draw_kata_result(frame, hasil, confidence, buffer_len, occ, rh, lh):
    h, w = frame.shape[:2]

    # Progress bar buffer
    prog = int((buffer_len / FRAME_PER_VIDEO) * (w - 40))
    cv2.rectangle(frame, (20, 58), (w - 20, 73), (60, 60, 60), -1)
    cv2.rectangle(frame, (20, 58), (20 + prog, 73), (255, 150, 0), -1)
    cv2.putText(frame, f"Buffer: {buffer_len}/{FRAME_PER_VIDEO}",
                (20, 92), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

    # Status tangan
    rh_c = (0, 220, 100) if rh else (100, 100, 100)
    lh_c = (0, 150, 255) if lh else (100, 100, 100)
    occ_c = (0, 80, 255) if occ else (100, 100, 100)
    cv2.putText(frame, f"RH: {'✓' if rh else '○'}",
                (20, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.5, rh_c, 1)
    cv2.putText(frame, f"LH: {'✓' if lh else '○'}",
                (80, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.5, lh_c, 1)
    cv2.putText(frame, f"TUMPUK: {'YA' if occ else 'tidak'}",
                (140, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.5, occ_c, 1)

    # Hasil kata
    if hasil:
        cv2.putText(frame, hasil,
                    (20, 185), cv2.FONT_HERSHEY_SIMPLEX, 3.0,
                    (255, 150, 0), 5, cv2.LINE_AA)
        conf_c = (0, 220, 100) if confidence > 0.8 else \
                 (0, 165, 255) if confidence > 0.65 else (0, 80, 200)
        cv2.putText(frame, f"Confidence: {int(confidence * 100)}%",
                    (20, 225), cv2.FONT_HERSHEY_SIMPLEX, 0.8, conf_c, 2)


cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    features, debug_info = extractor.extract(frame)
    frame = extractor.draw_landmarks(frame, debug_info)

    rh  = debug_info['rh_det']
    lh  = debug_info['lh_det']
    occ = debug_info['occlusion']

    draw_mode_header(frame, mode)

    # ── MODE KATA ───────────────────────────────────────────────────────────
    if mode == 'kata':
        # Terima frame jika ada tangan/pose — tidak buang frame oklusi
        any_det = rh or lh or occ or (debug_info['results'].pose_landmarks is not None)
        if any_det:
            buffer_kata.append(features)

        # Prediksi saat buffer penuh
        if len(buffer_kata) == FRAME_PER_VIDEO:
            seq = np.array(list(buffer_kata))           # (30, 156)
            seq = normalize_sequence(seq)               # normalisasi
            seq_input = seq[np.newaxis, ...]            # (1, 30, 156)

            pred         = model_kata.predict(seq_input, verbose=0)
            idx          = np.argmax(pred)
            confidence_k = float(pred[0][idx])

            if confidence_k > CONFIDENCE_KATA:
                hasil_kata = encoder_kata.inverse_transform([idx])[0].upper()
            else:
                hasil_kata = "?"
            
            buffer_kata.clear()
            extractor.reset_buffers()

        draw_kata_result(frame, hasil_kata, confidence_k,
                        len(buffer_kata), occ, rh, lh)

    # ── MODE HURUF (V1 — dipertahankan) ────────────────────────────────────
    # elif mode == 'huruf':
    #     ... (kode V1 tetap di sini)

    cv2.imshow('BAHASAKU V2', frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('k'):
        mode = 'kata'
        hasil_kata = ""
        buffer_kata.clear()
        extractor.reset_buffers()
    elif key == ord('h'):
        mode = 'huruf'
        hasil_kata = ""
        buffer_kata.clear()
        extractor.reset_buffers()
    elif key == ord('r'):
        hasil_kata = ""
        buffer_kata.clear()
        extractor.reset_buffers()
        print("Buffer direset.")

extractor.release()
cap.release()
cv2.destroyAllWindows()
