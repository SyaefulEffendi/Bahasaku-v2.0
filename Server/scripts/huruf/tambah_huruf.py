# rekam_huruf.py
import cv2
import mediapipe as mp
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
# Untuk mengganti huruf yang ingin ditambahkan
TARGET_HURUF = 'Z'   # Ganti huruf yang ingin direkam
TARGET_JUMLAH = 750  # Jumlah sampel yang ingin dikumpulkan
# ============================================================

HURUF_1_TANGAN = {'C','E','I','J','L','O','R','U','V','Z'}
IS_1_TANGAN    = TARGET_HURUF.upper() in HURUF_1_TANGAN
BUTUH_TANGAN   = 1 if IS_1_TANGAN else 2

# Tentukan file CSV tujuan otomatis berdasarkan huruf
if IS_1_TANGAN:
    CSV_PATH = 'dataset/dataset_1tangan.csv'
    N_FITUR  = 63
    COLS     = [f'{a}{i}' for i in range(21) for a in ['x','y','z']] + ['label']
else:
    CSV_PATH = 'dataset/dataset_2tangan.csv'
    N_FITUR  = 126
    COLS     = [f'{a}{i}' for i in range(21) for a in ['x','y','z']] + \
               [f'{a}{i}_2' for i in range(21) for a in ['x','y','z']] + ['label']

# Hitung sampel yang sudah ada untuk huruf ini
if os.path.exists(CSV_PATH):
    df_lama   = pd.read_csv(CSV_PATH)
    ada_skrng = len(df_lama[df_lama['label'] == TARGET_HURUF.upper()])
else:
    df_lama   = pd.DataFrame(columns=COLS)
    ada_skrng = 0

perlu = TARGET_JUMLAH - ada_skrng

print(f"Huruf target  : {TARGET_HURUF.upper()}")
print(f"Tipe          : {'1 tangan' if IS_1_TANGAN else '2 tangan'}")
print(f"Sudah ada     : {ada_skrng} sampel")
print(f"Target        : {TARGET_JUMLAH} sampel")
print(f"Perlu tambah  : {perlu} sampel")
print(f"Simpan ke     : {CSV_PATH}")
print()
print("PETUNJUK:")
print(f"  - Bentuk huruf {TARGET_HURUF.upper()} dengan {BUTUH_TANGAN} tangan")
print(f"  - Tunggu tulisan hijau 'Tangan OK'")
print(f"  - Tekan SPASI untuk simpan 1 sampel")
print(f"  - Variasikan posisi tangan tiap beberapa sampel")
print(f"  - Tekan Q untuk selesai & simpan")

if perlu <= 0:
    print(f"\nHuruf {TARGET_HURUF} sudah mencapai target {TARGET_JUMLAH} sampel!")
    print("Ganti TARGET_HURUF di script jika ingin rekam huruf lain.")
    exit()

cap       = cv2.VideoCapture(0)
data_baru = []

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame      = cv2.flip(frame, 1)
    h, w, _    = frame.shape
    rgb        = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results    = hands.process(rgb)

    tangan_ok  = False
    coords_row = None

    if results.multi_hand_landmarks:
        jml = len(results.multi_hand_landmarks)

        for hl in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hl, mp_hands.HAND_CONNECTIONS)

        if IS_1_TANGAN and jml >= 1:
            tangan_ok = True
            coords    = []
            for lm in results.multi_hand_landmarks[0].landmark:
                coords.extend([lm.x, lm.y, lm.z])
            coords_row = coords + [TARGET_HURUF.upper()]

        elif not IS_1_TANGAN and jml >= 2:
            tangan_ok = True
            coords    = []
            for hl in results.multi_hand_landmarks[:2]:
                for lm in hl.landmark:
                    coords.extend([lm.x, lm.y, lm.z])
            coords_row = coords + [TARGET_HURUF.upper()]

    # UI
    sudah    = ada_skrng + len(data_baru)
    progress = int((sudah / TARGET_JUMLAH) * (w - 40))

    cv2.rectangle(frame, (0, 0), (w, 115), (30, 30, 30), -1)
    cv2.rectangle(frame, (20, 12), (w - 20, 30), (70, 70, 70), -1)
    cv2.rectangle(frame, (20, 12), (20 + progress, 30), (0, 210, 120), -1)

    cv2.putText(frame, f"Huruf: {TARGET_HURUF.upper()}   {sudah}/{TARGET_JUMLAH}",
                (20, 62), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 2)
    cv2.putText(frame, f"Butuh {BUTUH_TANGAN} tangan  |  sisa {TARGET_JUMLAH - sudah} sampel",
                (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (170, 170, 170), 1)

    if tangan_ok:
        cv2.putText(frame, "Tangan OK  -  SPASI = simpan",
                    (20, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 230, 100), 2)
    else:
        cv2.putText(frame, f"Arahkan {BUTUH_TANGAN} tangan ke kamera...",
                    (20, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 130, 255), 2)

    if sudah >= TARGET_JUMLAH:
        cv2.putText(frame, "TARGET TERCAPAI!  Tekan Q untuk simpan",
                    (20, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 200), 2)

    cv2.imshow(f'Rekam Huruf {TARGET_HURUF.upper()}', frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord(' ') and tangan_ok and coords_row:
        data_baru.append(coords_row)
        terkumpul = ada_skrng + len(data_baru)
        print(f"  Tersimpan! {terkumpul}/{TARGET_JUMLAH}")

    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# Simpan ke CSV
if data_baru:
    df_baru   = pd.DataFrame(data_baru, columns=COLS)
    df_gabung = pd.concat([df_lama, df_baru], ignore_index=True)
    df_gabung.to_csv(CSV_PATH, index=False)

    print(f"\nBerhasil menambah {len(data_baru)} sampel")
    print(f"Total sampel {TARGET_HURUF.upper()} sekarang: "
         f"{len(df_gabung[df_gabung['label'] == TARGET_HURUF.upper()])}")
    print(f"Disimpan di: {CSV_PATH}")
else:
    print("\nTidak ada data baru yang disimpan.")