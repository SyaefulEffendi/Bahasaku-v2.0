# feature_extractor.py
# ─────────────────────────────────────────────────────────────────────────────
# Tugasnya SATU: ambil 1 frame dari kamera, kembalikan angka-angka (fitur)
# yang merepresentasikan posisi & gerakan tangan di frame tersebut.
#
# Total fitur per frame: 156
#   [0  – 62 ] = 63 angka → posisi 21 titik tangan KANAN (x,y,z tiap titik)
#   [63 – 125] = 63 angka → posisi 21 titik tangan KIRI  (x,y,z tiap titik)
#   [126– 149] = 24 angka → posisi bahu, siku, pergelangan (dari pose)
#   [150– 151] =  2 angka → optical flow (seberapa cepat & ke arah mana gerakan)
#   [152– 155] =  4 angka → flag (tangan kanan ada?, tangan kiri ada?,
#                                  tangan tumpuk?, keduanya ada?)
# ─────────────────────────────────────────────────────────────────────────────

import cv2
import mediapipe as mp
import numpy as np

# Setup MediaPipe
mp_holistic       = mp.solutions.holistic
mp_drawing        = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Index pose landmark yang kita ambil:
# 11=bahu kiri, 12=bahu kanan, 13=siku kiri, 14=siku kanan,
# 15=pergelangan kiri, 16=pergelangan kanan
POSE_IDX = [11, 12, 13, 14, 15, 16]

# Total fitur per frame
N_FITUR = 156

# Jarak maksimal pergelangan agar dianggap "tangan bertumpuk"
# Angka ini dalam koordinat normalisasi (0.0 - 1.0)
# Dari pengujian: tangan tumpuk = ~0.16, tangan terpisah = jauh lebih besar
OKLUSI_THRESHOLD = 0.19  # dikalibrasi: tangan tumpuk = 13.5%, threshold = 13.5+5 = 19%


class FeatureExtractor:

    def __init__(self):
        self.holistic = mp_holistic.Holistic(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=1,
        )
        # Simpan frame sebelumnya untuk optical flow
        self._frame_sebelumnya = None

        # Simpan posisi tangan terakhir yang terdeteksi
        # Digunakan untuk mengisi saat tangan sesaat tidak terdeteksi
        self._tangan_kanan_terakhir = np.zeros(63)
        self._tangan_kiri_terakhir  = np.zeros(63)

    def extract(self, frame_bgr):
        """
        Masukkan 1 frame (cv2.flip sudah dilakukan di luar),
        kembalikan:
          - fitur: np.array bentuk (156,)
          - info:  dict berisi status deteksi untuk ditampilkan di layar
        """
        rgb   = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        hasil = self.holistic.process(rgb)

        tangan_kanan, tangan_kiri, ada_kanan, ada_kiri = self._ambil_fitur_tangan(hasil)
        pose                                            = self._ambil_fitur_pose(hasil)
        flow_kecepatan, flow_arah                       = self._hitung_optical_flow(frame_bgr)
        tumpuk                                          = self._deteksi_tumpuk(hasil, ada_kanan, ada_kiri)

        flags = np.array([
            1.0 if ada_kanan else 0.0,
            1.0 if ada_kiri  else 0.0,
            1.0 if tumpuk    else 0.0,
            1.0 if (ada_kanan and ada_kiri) else 0.0,
        ])
        flow  = np.array([flow_kecepatan, flow_arah])

        fitur = np.concatenate([tangan_kanan, tangan_kiri, pose, flow, flags])

        info = {
            'hasil_mediapipe': hasil,
            'ada_kanan':       ada_kanan,
            'ada_kiri':        ada_kiri,
            'tumpuk':          tumpuk,
            'flow_kecepatan':  flow_kecepatan,
            'flow_arah':       flow_arah,
        }
        return fitur, info

    def reset(self):
        """Panggil ini setiap kali mau mulai rekam kata baru."""
        self._frame_sebelumnya      = None
        self._tangan_kanan_terakhir = np.zeros(63)
        self._tangan_kiri_terakhir  = np.zeros(63)

    def tutup(self):
        """Panggil ini saat program selesai."""
        self.holistic.close()

    # ── Fungsi-fungsi internal ────────────────────────────────────────────────

    def _ambil_fitur_tangan(self, hasil):
        """
        Ambil 63 angka untuk tangan kanan dan 63 angka untuk tangan kiri.

        Masalah label kiri/kanan di MediaPipe:
        Setelah frame di-flip, MediaPipe kadang menukar label kiri/kanan.
        Solusi: kita tentukan sendiri mana kanan & kiri berdasarkan posisi
        di layar — tangan yang ada di KANAN layar = tangan kanan.
        """
        lm_kanan = hasil.right_hand_landmarks
        lm_kiri  = hasil.left_hand_landmarks

        # Jika kedua tangan terdeteksi, cek apakah label perlu ditukar
        if lm_kanan and lm_kiri:
            x_kanan = lm_kanan.landmark[0].x
            x_kiri  = lm_kiri.landmark[0].x
            # Setelah flip: tangan kanan pengguna ada di KIRI layar (x lebih kecil)
            # karena MediaPipe label berdasarkan anatomi, bukan posisi layar.
            # Jika x_kanan > x_kiri → label terbalik → tukar
            if x_kanan > x_kiri:
                lm_kanan, lm_kiri = lm_kiri, lm_kanan

        # Tangan kanan
        if lm_kanan:
            fitur_kanan = np.array(
                [[lm.x, lm.y, lm.z] for lm in lm_kanan.landmark]
            ).flatten()
            self._tangan_kanan_terakhir = fitur_kanan.copy()
            ada_kanan = True
        else:
            # Posisi terakhir yang memudar perlahan (decay 0.85)
            self._tangan_kanan_terakhir = self._tangan_kanan_terakhir * 0.85
            fitur_kanan = self._tangan_kanan_terakhir.copy()
            ada_kanan = False

        # Tangan kiri
        if lm_kiri:
            fitur_kiri = np.array(
                [[lm.x, lm.y, lm.z] for lm in lm_kiri.landmark]
            ).flatten()
            self._tangan_kiri_terakhir = fitur_kiri.copy()
            ada_kiri = True
        else:
            self._tangan_kiri_terakhir = self._tangan_kiri_terakhir * 0.85
            fitur_kiri = self._tangan_kiri_terakhir.copy()
            ada_kiri = False

        return fitur_kanan, fitur_kiri, ada_kanan, ada_kiri

    def _ambil_fitur_pose(self, hasil):
        """
        Ambil 24 angka dari pose landmark (bahu, siku, pergelangan).
        Pose SELALU terdeteksi walau tangan bertumpuk.
        """
        if hasil.pose_landmarks:
            fitur_pose = np.array([
                [hasil.pose_landmarks.landmark[i].x,
                 hasil.pose_landmarks.landmark[i].y,
                 hasil.pose_landmarks.landmark[i].z,
                 hasil.pose_landmarks.landmark[i].visibility]
                for i in POSE_IDX
            ]).flatten()  # 6 titik x 4 angka = 24
        else:
            fitur_pose = np.zeros(24)
        return fitur_pose

    def _hitung_optical_flow(self, frame_bgr):
        """
        Hitung seberapa cepat dan ke arah mana gerakan terjadi di frame.
        Tidak peduli berapa tangan yang terlihat.
        """
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

        if self._frame_sebelumnya is None:
            self._frame_sebelumnya = gray
            return 0.0, 0.0

        flow = cv2.calcOpticalFlowFarneback(
            self._frame_sebelumnya, gray, None,
            pyr_scale=0.5, levels=3, winsize=15,
            iterations=3, poly_n=5, poly_sigma=1.2, flags=0
        )
        self._frame_sebelumnya = gray

        kecepatan, arah = cv2.cartToPolar(flow[..., 0], flow[..., 1])

        # Fokus ke bagian tengah frame
        h, w   = kecepatan.shape
        cy, cx = h // 2, w // 2
        area   = kecepatan[cy-80:cy+80, cx-80:cx+80]
        area_a = arah[cy-80:cy+80, cx-80:cx+80]

        kec_rata  = float(area.mean())   if area.size   > 0 else float(kecepatan.mean())
        arah_rata = float(area_a.mean()) if area_a.size > 0 else float(arah.mean())

        kec_norm  = min(kec_rata / 20.0, 1.0)
        arah_norm = arah_rata / (2 * np.pi)

        return kec_norm, arah_norm

    def _deteksi_tumpuk(self, hasil, ada_kanan, ada_kiri):
        """
        Deteksi apakah kedua tangan sedang bertumpuk.
        Caranya: ukur jarak pergelangan kanan-kiri dari pose landmark.
        Jika jarak < OKLUSI_THRESHOLD maka dianggap tumpuk.
        """
        if not hasil.pose_landmarks:
            return False

        pg_kiri  = hasil.pose_landmarks.landmark[15]
        pg_kanan = hasil.pose_landmarks.landmark[16]

        jarak = np.sqrt(
            (pg_kiri.x - pg_kanan.x) ** 2 +
            (pg_kiri.y - pg_kanan.y) ** 2
        )

        terlihat = pg_kiri.visibility > 0.3 and pg_kanan.visibility > 0.3

        if not terlihat:
            # Fallback: cek jarak hand wrist jika pose tidak jelas
            if ada_kanan and ada_kiri and hasil.right_hand_landmarks and hasil.left_hand_landmarks:
                lm_k = hasil.right_hand_landmarks
                lm_ki = hasil.left_hand_landmarks
                if lm_k.landmark[0].x > lm_ki.landmark[0].x:
                    lm_k, lm_ki = lm_ki, lm_k
                jarak_hand = np.sqrt(
                    (lm_k.landmark[0].x - lm_ki.landmark[0].x) ** 2 +
                    (lm_k.landmark[0].y - lm_ki.landmark[0].y) ** 2
                )
                return jarak_hand < 0.15
            return False

        return jarak < OKLUSI_THRESHOLD

    def gambar_landmark(self, frame, info):
        """Gambar titik-titik tangan dan pose di atas frame."""
        hasil    = info['hasil_mediapipe']

        if hasil.pose_landmarks:
            mp_drawing.draw_landmarks(
                frame, hasil.pose_landmarks, mp_holistic.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
            )

        lm_kanan = hasil.right_hand_landmarks
        lm_kiri  = hasil.left_hand_landmarks
        if lm_kanan and lm_kiri:
            # Sama dengan logika di _ambil_fitur_tangan:
            # setelah flip, tangan kanan ada di KIRI layar (x lebih kecil)
            if lm_kanan.landmark[0].x > lm_kiri.landmark[0].x:
                lm_kanan, lm_kiri = lm_kiri, lm_kanan

        if lm_kanan:
            mp_drawing.draw_landmarks(
                frame, lm_kanan, mp_holistic.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )
            h, w = frame.shape[:2]
            wx = int(lm_kanan.landmark[0].x * w)
            wy = int(lm_kanan.landmark[0].y * h)
            cv2.putText(frame, "R", (wx - 10, wy - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 220, 100), 2)

        if lm_kiri:
            mp_drawing.draw_landmarks(
                frame, lm_kiri, mp_holistic.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )
            h, w = frame.shape[:2]
            wx = int(lm_kiri.landmark[0].x * w)
            wy = int(lm_kiri.landmark[0].y * h)
            cv2.putText(frame, "L", (wx - 10, wy - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 150, 255), 2)

        return frame


# ── Fungsi utilitas ───────────────────────────────────────────────────────────

def sesuaikan_panjang(buffer, target=30):
    """Pastikan panjang buffer selalu tepat 'target' frame."""
    n = len(buffer)
    if n == target:
        return np.array(buffer)
    elif n > target:
        idx = np.linspace(0, n - 1, target, dtype=int)
        return np.array(buffer)[idx]
    else:
        buf = list(buffer)
        while len(buf) < target:
            buf.append(buf[-1])
        return np.array(buf)


def normalisasi_sekuens(seq):
    """
    Buat fitur relatif terhadap posisi tubuh.
    Tujuan: gerakan yang sama tapi dilakukan di posisi berbeda di layar
    tetap menghasilkan angka yang mirip.
    """
    seq = seq.copy().astype(np.float32)

    IDX_BAHU_KIRI_X  = 126
    IDX_BAHU_KIRI_Y  = 127
    IDX_BAHU_KANAN_X = 130
    IDX_BAHU_KANAN_Y = 131

    for t in range(len(seq)):
        bkx = seq[t, IDX_BAHU_KIRI_X]
        bky = seq[t, IDX_BAHU_KIRI_Y]
        bkax = seq[t, IDX_BAHU_KANAN_X]
        bkay = seq[t, IDX_BAHU_KANAN_Y]

        pusat_x = (bkx + bkax) / 2
        pusat_y = (bky + bkay) / 2

        jarak_bahu = np.sqrt((bkx - bkax)**2 + (bky - bkay)**2)
        skala = jarak_bahu if jarak_bahu > 0.01 else 1.0

        for i in range(0, 126, 3):
            if seq[t, i] != 0 or seq[t, i+1] != 0:
                seq[t, i]   = (seq[t, i]   - pusat_x) / skala
                seq[t, i+1] = (seq[t, i+1] - pusat_y) / skala

    return seq