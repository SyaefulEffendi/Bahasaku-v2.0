# rekam_kata_webcam.py
import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
import os

mp_hands   = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.5
)

# ============================================================
# UBAH DI SINI setiap ganti kata
TARGET_KATA   = 'hallo'      # ← ganti: 'hallo' / 'perkenalkan' / 'nama' / 'aku'
TARGET_VIDEO  = 30           # jumlah video per kata (jangan diubah)
FRAME_PER_VIDEO = 30         # jumlah frame per video (jangan diubah)
# ============================================================

# Konfigurasi otomatis berdasarkan kata
KATA_1_TANGAN = {'hallo', 'aku'}
KATA_2_TANGAN = {'perkenalkan', 'nama'}

IS_1_TANGAN  = TARGET_KATA.lower() in KATA_1_TANGAN
BUTUH_TANGAN = 1 if IS_1_TANGAN else 2
N_FITUR      = 63 if IS_1_TANGAN else 126

# Path CSV output
CSV_DIR  = '../../dataset/kata'
CSV_PATH = os.path.join(CSV_DIR, f'dataset_kata_{"1t" if IS_1_TANGAN else "2t"}.csv')
os.makedirs(CSV_DIR, exist_ok=True)

# Buat nama kolom
if IS_1_TANGAN:
    COLS = [f'{a}{i}' for i in range(21) for a in ['x','y','z']] + ['label']
else:
    COLS = [f'{a}{i}'   for i in range(21) for a in ['x','y','z']] + \
           [f'{a}{i}_2' for i in range(21) for a in ['x','y','z']] + ['label']

# Hitung video yang sudah ada
if os.path.exists(CSV_PATH):
    df_lama    = pd.read_csv(CSV_PATH)
    video_lama = len(df_lama[df_lama['label'] == TARGET_KATA]) // FRAME_PER_VIDEO
else:
    df_lama    = pd.DataFrame(columns=COLS)
    video_lama = 0

print(f"Kata target   : {TARGET_KATA.upper()}")
print(f"Tipe          : {'1 tangan' if IS_1_TANGAN else '2 tangan'}")
print(f"Video ada     : {video_lama}/{TARGET_VIDEO}")
print(f"Perlu tambah  : {TARGET_VIDEO - video_lama} video")
print()
print("PETUNJUK:")
print(f"  ENTER → mulai rekam 1 video ({FRAME_PER_VIDEO} frame)")
print(f"  Lakukan gerakan '{TARGET_KATA}' saat countdown dimulai")
print(f"  Q     → keluar & simpan")

cap        = cv2.VideoCapture(0)
data_baru  = []
video_done = 0  # video yang berhasil direkam sesi ini

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame      = cv2.flip(frame, 1)
    h, w, _    = frame.shape
    rgb        = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results    = hands.process(rgb)

    # Cek tangan
    tangan_ok = False
    if results.multi_hand_landmarks:
        jml = len(results.multi_hand_landmarks)
        for hl in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hl, mp_hands.HAND_CONNECTIONS)
        tangan_ok = (jml >= 1) if IS_1_TANGAN else (jml >= 2)

    # UI
    total_done = video_lama + video_done
    cv2.rectangle(frame, (0, 0), (w, 100), (30, 30, 30), -1)
    progress = int((total_done / TARGET_VIDEO) * (w - 40))
    cv2.rectangle(frame, (20, 10), (w - 20, 26), (70, 70, 70), -1)
    cv2.rectangle(frame, (20, 10), (20 + progress, 26), (0, 210, 120), -1)
    cv2.putText(frame, f"{TARGET_KATA.upper()}  {total_done}/{TARGET_VIDEO} video",
                (20, 56), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
    cv2.putText(frame, f"Butuh {BUTUH_TANGAN} tangan",
                (20, 82), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (170, 170, 170), 1)

    if tangan_ok:
        cv2.putText(frame, "Tangan OK  -  ENTER = mulai rekam",
                    (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 230, 100), 2)
    else:
        cv2.putText(frame, f"Arahkan {BUTUH_TANGAN} tangan ke kamera...",
                    (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 130, 255), 2)

    if total_done >= TARGET_VIDEO:
        cv2.putText(frame, "TARGET TERCAPAI!  Tekan Q",
                    (20, 165), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 200), 2)

    cv2.imshow(f'Rekam Kata - {TARGET_KATA.upper()}', frame)

    key = cv2.waitKey(1) & 0xFF

    if key == 13 and tangan_ok and total_done < TARGET_VIDEO:
        # ── MULAI REKAM 1 VIDEO ──
        buffer        = []
        frame_ke      = 0
        rekam_aktif   = True

        while rekam_aktif and cap.isOpened():
            ret2, frame2 = cap.read()
            if not ret2:
                break

            frame2     = cv2.flip(frame2, 1)
            rgb2       = cv2.cvtColor(frame2, cv2.COLOR_BGR2RGB)
            results2   = hands.process(rgb2)

            # Countdown visual
            sisa = FRAME_PER_VIDEO - frame_ke
            cv2.rectangle(frame2, (0, 0), (frame2.shape[1], 70), (20, 20, 20), -1)
            cv2.putText(frame2, f"MEREKAM... frame {frame_ke+1}/{FRAME_PER_VIDEO}",
                        (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 80, 255), 2)
            cv2.putText(frame2, "Lakukan gerakan sekarang!",
                        (20, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 2)

            if results2.multi_hand_landmarks:
                for hl in results2.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(frame2, hl, mp_hands.HAND_CONNECTIONS)

                jml2 = len(results2.multi_hand_landmarks)
                coords = []

                if IS_1_TANGAN and jml2 >= 1:
                    for lm in results2.multi_hand_landmarks[0].landmark:
                        coords.extend([lm.x, lm.y, lm.z])

                elif not IS_1_TANGAN and jml2 >= 2:
                    for hl in results2.multi_hand_landmarks[:2]:
                        for lm in hl.landmark:
                            coords.extend([lm.x, lm.y, lm.z])

                if len(coords) == N_FITUR:
                    buffer.append(coords)
                    frame_ke += 1

            cv2.imshow(f'Rekam Kata - {TARGET_KATA.upper()}', frame2)
            cv2.waitKey(1)

            if frame_ke >= FRAME_PER_VIDEO:
                rekam_aktif = False

        # Simpan buffer jika lengkap 30 frame
        if len(buffer) == FRAME_PER_VIDEO:
            for coords in buffer:
                data_baru.append(coords + [TARGET_KATA])
            video_done += 1
            print(f"  Video {video_lama + video_done}/{TARGET_VIDEO} tersimpan!")
        else:
            print(f"  Video gagal ({len(buffer)} frame) — tangan hilang saat rekam, coba lagi")

    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# Simpan CSV
if data_baru:
    df_baru   = pd.DataFrame(data_baru, columns=COLS)
    df_gabung = pd.concat([df_lama, df_baru], ignore_index=True)
    df_gabung.to_csv(CSV_PATH, index=False)
    total_video = len(df_gabung[df_gabung['label'] == TARGET_KATA]) // FRAME_PER_VIDEO
    print(f"\nBerhasil menyimpan {video_done} video baru")
    print(f"Total video '{TARGET_KATA}' : {total_video}/{TARGET_VIDEO}")
    print(f"Disimpan di : {CSV_PATH}")
else:
    print("\nTidak ada data baru yang disimpan.")