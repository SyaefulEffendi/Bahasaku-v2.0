# debug_kamera.py
# ─────────────────────────────────────────────────────────────────────────────
# Jalankan ini untuk verifikasi apakah feature_extractor.py bekerja benar
# SEBELUM mulai rekam dataset.
#
# Yang perlu diuji:
#   Skenario 1 → Tangan kanan saja   : R=DETECTED, L=missing,   Tumpuk=tidak
#   Skenario 2 → Tangan kiri saja    : R=missing,  L=DETECTED,  Tumpuk=tidak
#   Skenario 3 → Kedua tangan terpisah: R=DETECTED, L=DETECTED, Tumpuk=tidak
#   Skenario 4 → Kedua tangan tumpuk  : R=DETECTED, L=DETECTED, Tumpuk=YA !!!
#
# Tombol:
#   C → cetak nilai jarak pergelangan saat ini ke terminal (untuk kalibrasi)
#   Q → keluar
# ─────────────────────────────────────────────────────────────────────────────

import cv2
import numpy as np
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from feature_extractor import FeatureExtractor, N_FITUR, OKLUSI_THRESHOLD

# Warna
HIJAU  = (0,   220, 100)
BIRU   = (0,   150, 255)
MERAH  = (0,   60,  220)
ORANYE = (0,   140, 255)
PUTIH  = (255, 255, 255)
ABU    = (150, 150, 150)


def gambar_panel(frame, info):
    """Panel status di sebelah kanan layar."""
    h, w   = frame.shape[:2]
    px     = w - 310  # posisi x mulai panel
    y      = 20

    # Background panel
    cv2.rectangle(frame, (px, 0), (w, h), (30, 30, 30), -1)
    cv2.line(frame, (px, 0), (px, h), (60, 60, 60), 1)

    def tulis(teks, warna=PUTIH, ukuran=0.52):
        nonlocal y
        cv2.putText(frame, teks, (px + 10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, ukuran, warna, 1)
        y += int(ukuran * 42)

    # ── Deteksi tangan ──────────────────────────────────────────
    tulis("=== DETEKSI ===")
    tulis(f"Tangan Kanan : {'DETECTED' if info['ada_kanan'] else 'missing'}",
          HIJAU if info['ada_kanan'] else ABU)
    tulis(f"Tangan Kiri  : {'DETECTED' if info['ada_kiri'] else 'missing'}",
          BIRU if info['ada_kiri'] else ABU)
    tulis(f"Tumpuk       : {'YA !!!' if info['tumpuk'] else 'tidak'}",
          MERAH if info['tumpuk'] else ABU)

    # ── Tipe ────────────────────────────────────────────────────
    y += 5
    k, ki, t = info['ada_kanan'], info['ada_kiri'], info['tumpuk']
    if k and ki and t:
        tipe, wt = "TIPE: 2 TANGAN TUMPUK",    MERAH
    elif k and ki:
        tipe, wt = "TIPE: 2 TANGAN TERPISAH",  HIJAU
    elif t:
        tipe, wt = "TIPE: 2 TANGAN TUMPUK",    MERAH
    elif k:
        tipe, wt = "TIPE: 1 TANGAN KANAN",     HIJAU
    elif ki:
        tipe, wt = "TIPE: 1 TANGAN KIRI",      BIRU
    else:
        tipe, wt = "TIPE: tidak ada tangan",   ABU
    tulis(tipe, wt)

    # ── Jarak pergelangan ───────────────────────────────────────
    y += 8
    tulis("=== PERGELANGAN ===")

    hasil = info['hasil_mediapipe']
    if hasil.pose_landmarks:
        pg_ki = hasil.pose_landmarks.landmark[15]
        pg_ka = hasil.pose_landmarks.landmark[16]
        jarak = np.sqrt((pg_ki.x - pg_ka.x)**2 + (pg_ki.y - pg_ka.y)**2)
        pct   = round(jarak * 100, 1)
        vis_l = round(pg_ki.visibility, 2)
        vis_r = round(pg_ka.visibility, 2)

        # Bar jarak
        BAR_MAX = 0.5
        bar_len = int(min(jarak / BAR_MAX, 1.0) * 250)
        bar_c   = MERAH if jarak < OKLUSI_THRESHOLD else HIJAU
        cv2.rectangle(frame, (px+10, y),     (px+260, y+12), (60,60,60), -1)
        cv2.rectangle(frame, (px+10, y),     (px+10+bar_len, y+12), bar_c, -1)
        tx = px + 10 + int(OKLUSI_THRESHOLD / BAR_MAX * 250)
        cv2.line(frame, (tx, y-2), (tx, y+14), ORANYE, 2)
        y += 18
        tulis(f"Jarak: {pct}%  (threshold:{int(OKLUSI_THRESHOLD*100)}%)", bar_c)
        tulis(f"Vis kiri:{vis_l}  kanan:{vis_r}",
              ABU if vis_l < 0.3 or vis_r < 0.3 else PUTIH)
    else:
        tulis("Pose tidak terdeteksi", ABU)

    # ── Optical flow ────────────────────────────────────────────
    y += 8
    tulis("=== OPTICAL FLOW ===")
    tulis(f"Kecepatan : {info['flow_kecepatan']:.3f}", ORANYE)
    bergerak = "Bergerak" if info['flow_kecepatan'] > 0.02 else "Diam"
    tulis(f"Status    : {bergerak}", HIJAU if bergerak == "Bergerak" else ABU)

    # ── Info fitur ──────────────────────────────────────────────
    y += 8
    tulis("=== FITUR ===")
    tulis(f"Total per frame : {N_FITUR}")

    return frame


def gambar_header(frame):
    h, w = frame.shape[:2]
    cv2.rectangle(frame, (0, 0), (w - 310, 75), (25, 25, 25), -1)
    cv2.putText(frame, "BAHASAKU V2 - DEBUG",
                (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2)
    cv2.putText(frame, "Uji 4 skenario: 1 tangan kanan | 1 tangan kiri | 2 terpisah | 2 tumpuk",
                (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (170, 170, 170), 1)
    cv2.putText(frame, "C = cetak jarak ke terminal  |  Q = keluar",
                (10, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (170, 170, 170), 1)


def main():
    print("=" * 55)
    print("  BAHASAKU V2 - DEBUG KAMERA")
    print("=" * 55)
    print("  Uji 4 skenario ini satu per satu:")
    print("  1. Tangan kanan saja")
    print("  2. Tangan kiri saja")
    print("  3. Kedua tangan terpisah")
    print("  4. Kedua tangan ditumpuk")
    print()
    print("  Tekan C saat tangan TUMPUK untuk kalibrasi threshold")
    print("  Tekan Q untuk keluar")
    print("=" * 55)

    extractor = FeatureExtractor()
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # PENTING: flip dulu sebelum extract
        frame = cv2.flip(frame, 1)

        fitur, info = extractor.extract(frame)
        frame = extractor.gambar_landmark(frame, info)
        frame = gambar_panel(frame, info)
        gambar_header(frame)

        # Banner tumpuk
        if info['tumpuk']:
            h, w = frame.shape[:2]
            cv2.rectangle(frame, (0, 78), (w - 310, 108), (0, 0, 180), -1)
            cv2.putText(frame, "TANGAN BERTUMPUK TERDETEKSI",
                        (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.65, PUTIH, 2)

        cv2.imshow("Bahasaku V2 - Debug", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('c'):
            hasil = info['hasil_mediapipe']
            if hasil.pose_landmarks:
                pg_ki = hasil.pose_landmarks.landmark[15]
                pg_ka = hasil.pose_landmarks.landmark[16]
                jarak = np.sqrt((pg_ki.x - pg_ka.x)**2 + (pg_ki.y - pg_ka.y)**2)
                print(f"\n[KALIBRASI] Jarak pergelangan saat ini: {jarak:.4f} ({jarak*100:.1f}%)")
                print(f"  Vis kiri={pg_ki.visibility:.2f}  kanan={pg_ka.visibility:.2f}")
                if jarak < 0.25:
                    saran = jarak + 0.05
                    print(f"  → Jika ini posisi TUMPUK, ubah OKLUSI_THRESHOLD = {saran:.2f}")
                    print(f"    di file feature_extractor.py baris: OKLUSI_THRESHOLD = ...")
                else:
                    print(f"  → Jarak masih jauh. Tumpukkan tangan lebih rapat.")

    extractor.tutup()
    cap.release()
    cv2.destroyAllWindows()
    print("\nDebug selesai.")


if __name__ == '__main__':
    main()