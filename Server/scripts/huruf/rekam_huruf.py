# rekam_huruf.py
# Rekam dataset huruf BISINDO dengan metode BARU (MediaPipe Holistic)
# 156 fitur per frame, 1 frame per sampel (bukan 30 seperti kata)
#
# CARA PAKAI:
#   1. Ubah TARGET_HURUF di bawah
#   2. Jalankan: python rekam_huruf.py
#   3. Bentuk huruf → tahan → tekan SPASI untuk simpan 1 sampel
#   4. Ulangi sampai target tercapai, lalu tekan Q

import cv2
import numpy as np
import pandas as pd
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'kata'))
from feature_extractor import FeatureExtractor, N_FITUR

# ════════════════════════════════════════════════════════════════
TARGET_HURUF  = 'D'     # ← UBAH INI setiap ganti huruf (A-Z)
TARGET_JUMLAH = 200     # jumlah sampel per huruf
CSV_DIR  = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'dataset', 'huruf'))
# ════════════════════════════════════════════════════════════════

CSV_PATH = os.path.join(CSV_DIR, 'dataset_huruf.csv')
os.makedirs(CSV_DIR, exist_ok=True)
KOLOM = [f'f{i}' for i in range(N_FITUR)] + ['label']

# Hitung sampel yang sudah ada
if os.path.exists(CSV_PATH):
    df_lama   = pd.read_csv(CSV_PATH)
    ada_skrng = len(df_lama[df_lama['label'] == TARGET_HURUF.upper()])
else:
    df_lama   = pd.DataFrame(columns=KOLOM)
    ada_skrng = 0

print(f"Huruf: {TARGET_HURUF.upper()} | Ada: {ada_skrng}/{TARGET_JUMLAH} | Perlu: {max(0, TARGET_JUMLAH - ada_skrng)}")
print("SPASI = simpan 1 sampel | Q = simpan & keluar")


def main():
    extractor = FeatureExtractor()
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    data_baru = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        fitur, info = extractor.extract(frame)
        frame = extractor.gambar_landmark(frame, info)

        ada_kanan = info['ada_kanan']
        ada_kiri  = info['ada_kiri']
        tumpuk    = info['tumpuk']
        ada_tangan = ada_kanan or ada_kiri or tumpuk

        sudah = ada_skrng + len(data_baru)
        h, w  = frame.shape[:2]

        # Header
        cv2.rectangle(frame, (0, 0), (w, 95), (25, 25, 25), -1)
        progress = int((sudah / TARGET_JUMLAH) * (w - 40))
        cv2.rectangle(frame, (20, 8), (w-20, 22), (60, 60, 60), -1)
        cv2.rectangle(frame, (20, 8), (20+progress, 22),
                      (0, 210, 120) if sudah < TARGET_JUMLAH else (0, 255, 200), -1)
        cv2.putText(frame, f"Huruf: {TARGET_HURUF.upper()}   {sudah}/{TARGET_JUMLAH} sampel",
                    (20, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        status = "Tangan OK  -  SPASI = simpan" if ada_tangan else "Arahkan tangan ke kamera..."
        warna  = (0, 220, 100) if ada_tangan else (100, 100, 255)
        cv2.putText(frame, status, (20, 82), cv2.FONT_HERSHEY_SIMPLEX, 0.55, warna, 1)
        if sudah >= TARGET_JUMLAH:
            cv2.putText(frame, "TARGET TERCAPAI!  Q = keluar",
                        (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 200), 2)

        cv2.imshow(f'Rekam Huruf: {TARGET_HURUF.upper()}', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord(' ') and ada_tangan and sudah < TARGET_JUMLAH:
            data_baru.append(list(fitur) + [TARGET_HURUF.upper()])
            print(f"  ✓ {ada_skrng + len(data_baru)}/{TARGET_JUMLAH}")
        elif key == ord('q'):
            break

    extractor.tutup()
    cap.release()
    cv2.destroyAllWindows()

    if data_baru:
        df_baru   = pd.DataFrame(data_baru, columns=KOLOM)
        df_gabung = pd.concat([df_lama, df_baru], ignore_index=True)
        df_gabung.to_csv(CSV_PATH, index=False)
        total = len(df_gabung[df_gabung['label'] == TARGET_HURUF.upper()])
        print(f"\n✓ Tersimpan {len(data_baru)} sampel | Total '{TARGET_HURUF.upper()}': {total}")
    else:
        print("\nTidak ada data baru.")

if __name__ == '__main__':
    main()