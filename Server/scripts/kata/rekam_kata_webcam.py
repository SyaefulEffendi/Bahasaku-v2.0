# rekam_kata_webcam_v2.py
# ─────────────────────────────────────────────────────────────────────────────
# Rekam dataset kata BISINDO menggunakan pendekatan hybrid feature
# Mendukung: 1 tangan, 2 tangan, 2 tangan bertumpuk (oklusi)
#
# Perubahan dari V1:
#   - Menggunakan MediaPipe Holistic (bukan Hands saja)
#   - 156 fitur per frame (bukan 63/126)
#   - TIDAK membuang frame saat tangan bertumpuk
#   - Optical flow sebagai fitur gerakan
#   - Satu CSV universal untuk semua kata
#
# Jalankan: python rekam_kata_webcam_v2.py
# ─────────────────────────────────────────────────────────────────────────────

import cv2
import numpy as np
import pandas as pd
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from feature_extractor import FeatureExtractor, N_FITUR, pad_or_trim, normalize_sequence

# ════════════════════════════════════════════════════════════════════
#  KONFIGURASI — Ubah di sini setiap ganti kata
# ════════════════════════════════════════════════════════════════════
TARGET_KATA     = 'perkenalkan'  # kata yang akan direkam
TARGET_VIDEO    = 50             # target jumlah video per kata
FRAME_PER_VIDEO = 30             # frame per video (jangan diubah)

# Path output
CSV_DIR  = r'D:\Syaeful\Kuliah\Semester 4\Bahasaku V2\web\Server\dataset\kata'
CSV_PATH = os.path.join(CSV_DIR, 'dataset_kata_v2.csv')
os.makedirs(CSV_DIR, exist_ok=True)
# ════════════════════════════════════════════════════════════════════

# Nama kolom CSV (156 fitur + label)
FITUR_COLS = [f'f{i}' for i in range(N_FITUR)]
ALL_COLS   = FITUR_COLS + ['label']

# Load CSV yang sudah ada
if os.path.exists(CSV_PATH):
    df_lama    = pd.read_csv(CSV_PATH)
    video_lama = len(df_lama[df_lama['label'] == TARGET_KATA]) // FRAME_PER_VIDEO
else:
    df_lama    = pd.DataFrame(columns=ALL_COLS)
    video_lama = 0

print("=" * 55)
print(f"  REKAM KATA: {TARGET_KATA.upper()}")
print("=" * 55)
print(f"  Video sudah ada : {video_lama}/{TARGET_VIDEO}")
print(f"  Perlu tambah    : {max(0, TARGET_VIDEO - video_lama)} video")
print(f"  Fitur per frame : {N_FITUR}")
print()
print("  PETUNJUK:")
print(f"  1. Siapkan posisi")
print(f"  2. Tekan ENTER untuk mulai rekam")
print(f"  3. Lakukan gerakan '{TARGET_KATA}' saat MEREKAM")
print(f"  4. Rekam ulang jika gagal")
print(f"  5. Tekan Q untuk simpan & keluar")
print()
print("  TIPS TANGAN BERTUMPUK:")
print("  - Pastikan kedua pergelangan tangan terlihat kamera")
print("  - Lakukan gerakan perlahan di awal")
print("  - Status 'OKLUSI' di layar = tumpukan terdeteksi ✓")
print("=" * 55)


def draw_ui(frame, total_done, tangan_info, recording=False,
            frame_ke=0, occlusion=False, flow_mag=0.0):
    h, w = frame.shape[:2]

    # Header bar
    cv2.rectangle(frame, (0, 0), (w, 100), (25, 25, 25), -1)

    # Progress bar
    progress_pct = total_done / TARGET_VIDEO
    bar_x2 = 20 + int(progress_pct * (w - 40))
    cv2.rectangle(frame, (20, 10), (w - 20, 26), (60, 60, 60), -1)
    cv2.rectangle(frame, (20, 10), (bar_x2, 26),
                  (0, 210, 120) if total_done < TARGET_VIDEO else (0, 255, 200), -1)

    # Teks kata & progress
    cv2.putText(frame, f"{TARGET_KATA.upper()}  {total_done}/{TARGET_VIDEO} video",
                (20, 54), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

    # Status tangan
    th_c = (0, 220, 100) if tangan_info else (100, 100, 255)
    cv2.putText(frame, tangan_info if tangan_info else "Arahkan tangan ke kamera...",
                (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.55, th_c, 1)

    if recording:
        # Rekam progress bar
        prog = int((frame_ke / FRAME_PER_VIDEO) * (w - 40))
        cv2.rectangle(frame, (20, 108), (w - 20, 122), (40, 40, 40), -1)
        cv2.rectangle(frame, (20, 108), (20 + prog, 122), (0, 80, 255), -1)
        cv2.putText(frame, f"● MEREKAM  {frame_ke}/{FRAME_PER_VIDEO} frame",
                    (20, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 80, 255), 2)

        if occlusion:
            cv2.rectangle(frame, (20, 155), (380, 180), (0, 0, 180), -1)
            cv2.putText(frame, "TUMPUKAN TERDETEKSI ✓",
                        (25, 173), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

        # Flow indicator
        bar_flow = int(min(flow_mag * 500, w - 40))
        cv2.rectangle(frame, (20, 185), (w - 20, 198), (40, 40, 40), -1)
        cv2.rectangle(frame, (20, 185), (20 + bar_flow, 198), (255, 130, 0), -1)
        cv2.putText(frame, f"Gerakan: {'Bergerak' if flow_mag > 0.02 else 'Diam'}",
                    (20, 215), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    else:
        if total_done < TARGET_VIDEO:
            cv2.putText(frame, "ENTER = mulai rekam",
                        (20, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.65,
                        (0, 220, 100) if tangan_info else (100, 100, 100), 2)
        else:
            cv2.putText(frame, "TARGET TERCAPAI!  Q = simpan & keluar",
                        (20, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 200), 2)

    return frame


def main():
    extractor  = FeatureExtractor(min_detection_confidence=0.5,
                                  min_tracking_confidence=0.5)
    cap        = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    data_baru  = []
    video_done = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame    = cv2.flip(frame, 1)
        features, debug_info = extractor.extract(frame)
        frame    = extractor.draw_landmarks(frame, debug_info)

        total_done  = video_lama + video_done
        rh          = debug_info['rh_det']
        lh          = debug_info['lh_det']
        occ         = debug_info['occlusion']

        if rh and lh:
            tangan_info = "Kedua tangan terdeteksi ✓"
        elif rh or lh:
            tangan_info = f"{'Kanan' if rh else 'Kiri'} terdeteksi" + \
                          (" | TUMPUKAN?" if occ else "")
        elif occ:
            tangan_info = "Tangan bertumpuk terdeteksi ✓ (via pose)"
        else:
            tangan_info = None

        any_detected = rh or lh or occ or debug_info['results'].pose_landmarks

        frame = draw_ui(frame, total_done, tangan_info)
        cv2.imshow(f'Rekam: {TARGET_KATA.upper()}', frame)

        key = cv2.waitKey(1) & 0xFF

        if key == 13 and any_detected and total_done < TARGET_VIDEO:
            # ── MULAI REKAM 1 VIDEO ──────────────────────────────────
            extractor.reset_buffers()
            buffer   = []
            frame_ke = 0

            while frame_ke < FRAME_PER_VIDEO and cap.isOpened():
                ret2, frame2 = cap.read()
                if not ret2:
                    break

                frame2             = cv2.flip(frame2, 1)
                features2, dinfo2  = extractor.extract(frame2)
                frame2             = extractor.draw_landmarks(frame2, dinfo2)

                # Simpan fitur — TIDAK dibuang walau tangan bertumpuk
                # Pose landmarks memastikan ada data bahkan saat oklusi
                pose_ok = dinfo2['results'].pose_landmarks is not None
                if pose_ok or dinfo2['rh_det'] or dinfo2['lh_det']:
                    buffer.append(features2)
                    frame_ke += 1

                frame2 = draw_ui(frame2, total_done, None,
                                 recording=True, frame_ke=frame_ke,
                                 occlusion=dinfo2['occlusion'],
                                 flow_mag=dinfo2['flow_mag'])
                cv2.imshow(f'Rekam: {TARGET_KATA.upper()}', frame2)
                cv2.waitKey(1)

            # ── Evaluasi hasil rekam ──────────────────────────────────
            if len(buffer) >= FRAME_PER_VIDEO * 0.8:  # toleransi 80%
                # Pad/trim ke tepat 30 frame
                seq = pad_or_trim(buffer, FRAME_PER_VIDEO)
                # Normalisasi
                seq = normalize_sequence(seq)

                for i, feat in enumerate(seq):
                    data_baru.append(list(feat) + [TARGET_KATA])

                video_done += 1
                print(f"  ✓ Video {video_lama + video_done}/{TARGET_VIDEO} tersimpan "
                      f"({len(buffer)} frame valid)")
            else:
                print(f"  ✗ Gagal — hanya {len(buffer)}/{FRAME_PER_VIDEO} frame valid")
                print(f"    Pastikan tangan/tubuh terlihat kamera saat rekam")

        elif key == ord('q'):
            break

    extractor.release()
    cap.release()
    cv2.destroyAllWindows()

    # ── Simpan CSV ────────────────────────────────────────────────────
    if data_baru:
        df_baru   = pd.DataFrame(data_baru, columns=ALL_COLS)
        df_gabung = pd.concat([df_lama, df_baru], ignore_index=True)
        df_gabung.to_csv(CSV_PATH, index=False)
        total = len(df_gabung[df_gabung['label'] == TARGET_KATA]) // FRAME_PER_VIDEO
        print(f"\n✓ Berhasil menyimpan {video_done} video baru")
        print(f"  Total '{TARGET_KATA}': {total}/{TARGET_VIDEO} video")
        print(f"  Disimpan: {CSV_PATH}")
    else:
        print("\nTidak ada data baru yang disimpan.")


if __name__ == '__main__':
    main()
