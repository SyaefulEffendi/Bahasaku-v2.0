# rekam_kata_webcam.py
# ─────────────────────────────────────────────────────────────────────────────
# CARA PAKAI:
#   1. Ubah TARGET_KATA di bawah sesuai kata yang mau direkam
#   2. Jalankan: python rekam_kata_webcam.py
#   3. Tekan ENTER untuk mulai rekam 1 video
#   4. Lakukan gerakan kata saat "MEREKAM" muncul
#   5. Ulangi sampai 50 video
#   6. Tekan Q untuk simpan dan keluar
#   7. Ganti TARGET_KATA, ulangi untuk kata berikutnya
# ─────────────────────────────────────────────────────────────────────────────

import cv2
import numpy as np
import pandas as pd
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from feature_extractor import FeatureExtractor, N_FITUR, sesuaikan_panjang, normalisasi_sekuens

# ════════════════════════════════════════════════════════════════════
#   UBAH INI setiap ganti kata
TARGET_KATA  = 'halo'        # kata yang akan direkam
TARGET_VIDEO = 50            # jumlah video per kata (jangan dikurangi)
# ════════════════════════════════════════════════════════════════════

FRAME_PER_VIDEO = 30
CSV_DIR  = r'D:\Syaeful\Kuliah\Semester 4\Bahasaku V2\web\Server\dataset\kata'
CSV_PATH = os.path.join(CSV_DIR, 'dataset_kata.csv')
os.makedirs(CSV_DIR, exist_ok=True)

# Kolom CSV: f0, f1, ..., f155, label
KOLOM = [f'f{i}' for i in range(N_FITUR)] + ['label']

# Hitung video yang sudah ada untuk kata ini
if os.path.exists(CSV_PATH):
    df_lama    = pd.read_csv(CSV_PATH)
    video_lama = len(df_lama[df_lama['label'] == TARGET_KATA]) // FRAME_PER_VIDEO
else:
    df_lama    = pd.DataFrame(columns=KOLOM)
    video_lama = 0

print("=" * 50)
print(f"  REKAM KATA: {TARGET_KATA.upper()}")
print(f"  Sudah ada  : {video_lama}/{TARGET_VIDEO} video")
print(f"  Perlu tambah: {max(0, TARGET_VIDEO - video_lama)} video")
print("=" * 50)
print("  ENTER = mulai rekam  |  Q = simpan & keluar")
print()


def gambar_ui(frame, total, info_tangan, sedang_rekam=False,
              frame_ke=0, tumpuk=False, kecepatan=0.0):
    h, w = frame.shape[:2]
    cv2.rectangle(frame, (0, 0), (w, 95), (25, 25, 25), -1)

    # Progress bar keseluruhan
    pct  = total / TARGET_VIDEO
    bx2  = 20 + int(pct * (w - 40))
    cv2.rectangle(frame, (20, 8),  (w-20, 22), (60, 60, 60), -1)
    cv2.rectangle(frame, (20, 8),  (bx2,  22), (0, 210, 120), -1)
    cv2.putText(frame, f"{TARGET_KATA.upper()}  {total}/{TARGET_VIDEO} video",
                (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,255,255), 2)

    if info_tangan:
        cv2.putText(frame, info_tangan, (20, 76),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0,220,100), 1)
    else:
        cv2.putText(frame, "Arahkan tangan ke kamera...",
                    (20, 76), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (100,100,255), 1)

    if sedang_rekam:
        # Progress bar rekam
        prog = int((frame_ke / FRAME_PER_VIDEO) * (w - 40))
        cv2.rectangle(frame, (20, 103), (w-20, 116), (40,40,40), -1)
        cv2.rectangle(frame, (20, 103), (20+prog, 116), (0,80,255), -1)
        cv2.putText(frame, f"MEREKAM  {frame_ke}/{FRAME_PER_VIDEO}",
                    (20, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0,80,255), 2)
        if tumpuk:
            cv2.rectangle(frame, (20, 148), (340, 172), (0,0,180), -1)
            cv2.putText(frame, "TUMPUKAN TERDETEKSI",
                        (25, 166), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255,255,255), 1)
        # Indikator gerakan
        bar_g = int(min(kecepatan * 500, w - 40))
        cv2.rectangle(frame, (20, 178), (w-20, 190), (40,40,40), -1)
        cv2.rectangle(frame, (20, 178), (20+bar_g, 190), (255,130,0), -1)
        cv2.putText(frame,
                    f"Gerakan: {'Bergerak' if kecepatan > 0.02 else 'Diam'}",
                    (20, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,200), 1)
    else:
        if total < TARGET_VIDEO:
            cv2.putText(frame, "ENTER = mulai rekam",
                        (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0,220,100), 2)
        else:
            cv2.putText(frame, "TARGET TERCAPAI!  Q = keluar",
                        (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0,255,200), 2)
    return frame


def main():
    extractor  = FeatureExtractor()
    cap        = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    data_baru  = []
    video_done = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        fitur, info = extractor.extract(frame)
        frame = extractor.gambar_landmark(frame, info)

        total     = video_lama + video_done
        ada_k     = info['ada_kanan']
        ada_ki    = info['ada_kiri']
        tumpuk    = info['tumpuk']
        ada_pose  = info['hasil_mediapipe'].pose_landmarks is not None

        if ada_k and ada_ki:
            info_tangan = "Kedua tangan terdeteksi ✓"
        elif tumpuk:
            info_tangan = "Tangan bertumpuk terdeteksi ✓"
        elif ada_k or ada_ki:
            sisi = "Kanan" if ada_k else "Kiri"
            info_tangan = f"1 tangan ({sisi}) terdeteksi ✓"
        else:
            info_tangan = None

        ada_sesuatu = ada_k or ada_ki or tumpuk or ada_pose

        frame = gambar_ui(frame, total, info_tangan)
        cv2.imshow(f'Rekam: {TARGET_KATA.upper()}', frame)

        key = cv2.waitKey(1) & 0xFF

        # ── Tekan ENTER → mulai rekam 1 video ────────────────────────────
        if key == 13 and ada_sesuatu and total < TARGET_VIDEO:
            extractor.reset()
            buffer   = []
            frame_ke = 0

            while frame_ke < FRAME_PER_VIDEO and cap.isOpened():
                ret2, frame2 = cap.read()
                if not ret2:
                    break

                frame2 = cv2.flip(frame2, 1)
                fitur2, info2 = extractor.extract(frame2)
                frame2 = extractor.gambar_landmark(frame2, info2)

                # Terima frame selama pose terdeteksi (tidak buang frame oklusi)
                pose_ok = info2['hasil_mediapipe'].pose_landmarks is not None
                if pose_ok or info2['ada_kanan'] or info2['ada_kiri']:
                    buffer.append(fitur2)
                    frame_ke += 1

                frame2 = gambar_ui(frame2, total, None,
                                   sedang_rekam=True, frame_ke=frame_ke,
                                   tumpuk=info2['tumpuk'],
                                   kecepatan=info2['flow_kecepatan'])
                cv2.imshow(f'Rekam: {TARGET_KATA.upper()}', frame2)
                cv2.waitKey(1)

            # Evaluasi: minimal 24 dari 30 frame harus valid (80%)
            if len(buffer) >= int(FRAME_PER_VIDEO * 0.8):
                seq = sesuaikan_panjang(buffer, FRAME_PER_VIDEO)
                seq = normalisasi_sekuens(seq)
                for baris in seq:
                    data_baru.append(list(baris) + [TARGET_KATA])
                video_done += 1
                print(f"  ✓ Video {video_lama+video_done}/{TARGET_VIDEO} "
                      f"({len(buffer)} frame valid)")
            else:
                print(f"  ✗ Gagal — {len(buffer)}/{FRAME_PER_VIDEO} frame "
                      f"(tangan tidak terdeteksi, coba lagi)")

        elif key == ord('q'):
            break

    extractor.tutup()
    cap.release()
    cv2.destroyAllWindows()

    # Simpan ke CSV
    if data_baru:
        df_baru   = pd.DataFrame(data_baru, columns=KOLOM)
        df_gabung = pd.concat([df_lama, df_baru], ignore_index=True)
        df_gabung.to_csv(CSV_PATH, index=False)
        total_video = len(df_gabung[df_gabung['label'] == TARGET_KATA]) // FRAME_PER_VIDEO
        print(f"\n✓ Tersimpan {video_done} video baru")
        print(f"  Total '{TARGET_KATA}': {total_video}/{TARGET_VIDEO}")
        print(f"  File: {CSV_PATH}")
    else:
        print("\nTidak ada data yang disimpan.")


if __name__ == '__main__':
    main()