import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import cv2
import mediapipe as mp
import numpy as np
import pickle
import tensorflow as tf

mp_hands   = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

print("Memuat model...")
model_1t = tf.keras.models.load_model('app/models_ml/model_1tangan.h5')
model_2t = tf.keras.models.load_model('app/models_ml/model_2tangan.h5')

with open('app/models_ml/label_encoder_1tangan.pkl', 'rb') as f:
    encoder_1t = pickle.load(f)
with open('app/models_ml/label_encoder_2tangan.pkl', 'rb') as f:
    encoder_2t = pickle.load(f)

CONFIDENCE = 0.65

print("Kamera aktif... (Tekan Q untuk keluar)")
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame      = cv2.flip(frame, 1)
    h, w, _    = frame.shape
    rgb        = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results    = hands.process(rgb)

    if results.multi_hand_landmarks:
        jumlah_tangan = len(results.multi_hand_landmarks)

        for hl in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hl, mp_hands.HAND_CONNECTIONS)

        if jumlah_tangan == 1:
            # Pakai model 1 tangan
            coords = []
            for lm in results.multi_hand_landmarks[0].landmark:
                coords.extend([lm.x, lm.y, lm.z])

            pred       = model_1t.predict(np.array([coords]), verbose=0)
            idx        = np.argmax(pred)
            confidence = pred[0][idx]
            huruf      = encoder_1t.inverse_transform([idx])[0] if confidence > CONFIDENCE else "?"
            info       = "1 tangan"

        else:
            # Pakai model 2 tangan
            coords = []
            for hl in results.multi_hand_landmarks[:2]:
                for lm in hl.landmark:
                    coords.extend([lm.x, lm.y, lm.z])

            pred       = model_2t.predict(np.array([coords]), verbose=0)
            idx        = np.argmax(pred)
            confidence = pred[0][idx]
            huruf      = encoder_2t.inverse_transform([idx])[0] if confidence > CONFIDENCE else "?"
            info       = "2 tangan"

        teks = f"{huruf}  {int(confidence * 100)}%  [{info}]"
        cv2.putText(frame, teks, (20, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 100), 3, cv2.LINE_AA)

    cv2.imshow('BAHASAKU - Uji Kamera', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()