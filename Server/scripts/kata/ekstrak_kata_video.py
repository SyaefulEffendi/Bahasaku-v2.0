# ekstrak_kata_video.py
import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
import os

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.5
)

# ============================================================
# UBAH DI SINI setiap ganti kata
TARGET_KATA  = 'hallo'
FOLDER_VIDEO = r'D:\Syaeful\video_bisindo\hallo'  # ← path absolut, bebas taruh di mana saja
# ============================================================

KATA_1_TANGAN   = {'hallo', 'aku'}
IS_1_TANGAN     = TARGET_KATA.lower() in KATA_1_TANGAN
N_FITUR         = 63 if IS_1_TANGAN else 126
FRAME_PER_VIDEO = 30

CSV_DIR  = '../../dataset/kata'
CSV_PATH = os.path.join(CSV_DIR, f'dataset_kata_{"1t" if IS_1_TANGAN else "2t"}.csv')
os.makedirs(CSV_DIR, exist_ok=True)

if IS_1_TANGAN:
    COLS = [f'{a}{i}' for i in range(21) for a in ['x','y','z']] + ['label']
else:
    COLS = [f'{a}{i}'   for i in range(21) for a in ['x','y','z']] + \
           [f'{a}{i}_2' for i in range(21) for a in ['x','y','z']] + ['label']

if os.path.exists(CSV_PATH):
    df_lama = pd.read_csv(CSV_PATH)
else:
    df_lama = pd.DataFrame(columns=COLS)

# Proses semua file video di folder
video_files = [f for f in os.listdir(FOLDER_VIDEO)
               if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))]

print(f"Kata target   : {TARGET_KATA.upper()}")
print(f"Folder video  : {FOLDER_VIDEO}")
print(f"Video ditemukan: {len(video_files)} file")
print()

data_baru   = []
berhasil    = 0
gagal       = 0

for nama_file in video_files:
    path_video = os.path.join(FOLDER_VIDEO, nama_file)
    cap        = cv2.VideoCapture(path_video)
    total_frame = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps         = cap.get(cv2.CAP_PROP_FPS) or 30

    print(f"Memproses: {nama_file} ({total_frame} frame, {fps:.0f}fps)")

    # Ambil FRAME_PER_VIDEO frame yang tersebar merata
    # agar video 1 detik dan 3 detik punya jumlah frame sama
    indices = np.linspace(0, total_frame - 1, FRAME_PER_VIDEO, dtype=int)
    buffer  = []

    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            continue

        rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)
        coords  = []

        if results.multi_hand_landmarks:
            jml = len(results.multi_hand_landmarks)

            if IS_1_TANGAN and jml >= 1:
                for lm in results.multi_hand_landmarks[0].landmark:
                    coords.extend([lm.x, lm.y, lm.z])

            elif not IS_1_TANGAN and jml >= 2:
                for hl in results.multi_hand_landmarks[:2]:
                    for lm in hl.landmark:
                        coords.extend([lm.x, lm.y, lm.z])

        if len(coords) == N_FITUR:
            buffer.append(coords)

    cap.release()

    if len(buffer) == FRAME_PER_VIDEO:
        for coords in buffer:
            data_baru.append(coords + [TARGET_KATA])
        berhasil += 1
        print(f"  ✓ Berhasil ({FRAME_PER_VIDEO} frame)")
    else:
        gagal += 1
        print(f"  ✗ Gagal — hanya {len(buffer)} frame valid "
            f"(tangan tidak terdeteksi di beberapa frame)")

# Simpan CSV
print(f"\nHasil: {berhasil} video berhasil, {gagal} video gagal")

if data_baru:
    df_baru   = pd.DataFrame(data_baru, columns=COLS)
    df_gabung = pd.concat([df_lama, df_baru], ignore_index=True)
    df_gabung.to_csv(CSV_PATH, index=False)
    total_video = len(df_gabung[df_gabung['label'] == TARGET_KATA]) // FRAME_PER_VIDEO
    print(f"Total video '{TARGET_KATA}' di CSV: {total_video}")
    print(f"Disimpan di: {CSV_PATH}")
else:
    print("Tidak ada data baru yang disimpan.")