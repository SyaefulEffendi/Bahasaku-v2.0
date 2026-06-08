"""
ai_routes.py
Mendukung DUA mode prediksi (sesuai uji_kamera.py):
  1. POST /ai/predict/huruf  → model huruf Dense (1 frame, 156 fitur)
  2. POST /ai/predict/kata   → model kata LSTM   (buffer 30 frame, 156 fitur)
  3. POST /ai/predict        → backward-compatible, diteruskan ke /huruf
  4. POST /ai/predict/reset  → reset session (buffer + extractor)

Semua mode menggunakan FeatureExtractor yang persisten per-session,
sama seperti uji_kamera.py yang hanya membuat 1 extractor.
"""

import os
import sys
import pickle
import threading
from collections import deque

import cv2
import numpy as np
from flask import Blueprint, request, jsonify
from app.models.kosa_kata_model import KosaKata

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import tensorflow as tf

# ── Path model ────────────────────────────────────────────────────────────────
MODEL_DIR = os.path.join(os.getcwd(), 'app', 'models_ml')

# ── Import feature_extractor dari scripts/kata/ ───────────────────────────────
_FE_DIR = os.path.join(os.getcwd(), 'scripts', 'kata')
if not os.path.isdir(_FE_DIR):
    _FE_DIR = os.path.join(os.getcwd(), '..', 'scripts', 'kata')
sys.path.insert(0, os.path.abspath(_FE_DIR))

try:
    from feature_extractor import FeatureExtractor, normalisasi_sekuens, sesuaikan_panjang
    FE_AVAILABLE = True
except ImportError as e:
    FE_AVAILABLE = False
    print(f"[ai_routes] PERINGATAN: Tidak bisa import feature_extractor → {e}")
    print(f"[ai_routes] Pastikan feature_extractor.py ada di: {_FE_DIR}")

# ─────────────────────────────────────────────────────────────────────────────
# Konstanta — disesuaikan dengan uji_kamera.py
# ─────────────────────────────────────────────────────────────────────────────
CONFIDENCE_HURUF = 0.65
CONFIDENCE_KATA  = 0.65
FRAME_PER_VIDEO  = 30

# ─────────────────────────────────────────────────────────────────────────────
# Load semua model (sekali saat startup)
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 55)
print("[ai_routes] Memuat model ML...")

# --- Model huruf ---
try:
    _huruf_path = os.path.join(MODEL_DIR, 'model_huruf.keras')
    if not os.path.exists(_huruf_path):
        _huruf_path = os.path.join(MODEL_DIR, 'model_huruf.h5')

    _model_huruf = tf.keras.models.load_model(_huruf_path)
    with open(os.path.join(MODEL_DIR, 'label_encoder_huruf.pkl'), 'rb') as f:
        _encoder_huruf = pickle.load(f)

    MODEL_HURUF_READY = True
    print(f"[ai_routes] ✓ Model huruf berhasil dimuat dari {os.path.basename(_huruf_path)}")
    print(f"[ai_routes]   Huruf: {list(_encoder_huruf.classes_)}")
except Exception as e:
    MODEL_HURUF_READY = False
    print(f"[ai_routes] ✗ Gagal memuat model huruf: {e}")

# --- Model kata ---
try:
    if not FE_AVAILABLE:
        raise ImportError("feature_extractor tidak tersedia")
    _kata_path = os.path.join(MODEL_DIR, 'model_kata.keras')
    if not os.path.exists(_kata_path):
        _kata_path = os.path.join(MODEL_DIR, 'model_kata.h5')
    _model_kata = tf.keras.models.load_model(_kata_path)
    with open(os.path.join(MODEL_DIR, 'label_encoder_kata.pkl'), 'rb') as f:
        _encoder_kata = pickle.load(f)
    MODEL_KATA_READY = True
    print(f"[ai_routes] ✓ Model kata dimuat dari {os.path.basename(_kata_path)}")
    print(f"[ai_routes]   Kata: {list(_encoder_kata.classes_)}")
except Exception as e:
    MODEL_KATA_READY = False
    print(f"[ai_routes] ✗ Gagal memuat model kata: {e}")

print("=" * 55)

# ─────────────────────────────────────────────────────────────────────────────
# Session buffer — satu session menyimpan extractor + buffer kata
# Sama seperti uji_kamera.py yang hanya punya 1 extractor global
# ─────────────────────────────────────────────────────────────────────────────
_sessions: dict = {}
_sessions_lock  = threading.Lock()


def _get_session(session_id: str) -> dict:
    with _sessions_lock:
        if session_id not in _sessions:
            _sessions[session_id] = {
                'buffer':      deque(maxlen=FRAME_PER_VIDEO),
                'extractor':   FeatureExtractor() if FE_AVAILABLE else None,
            }
        # Bersihkan session lama jika terlalu banyak
        if len(_sessions) > 50:
            oldest = next(iter(_sessions))
            try:
                if _sessions[oldest]['extractor']:
                    _sessions[oldest]['extractor'].tutup()
            except Exception:
                pass
            del _sessions[oldest]
        return _sessions[session_id]


# ─────────────────────────────────────────────────────────────────────────────
# Helper: baca gambar dari request
# ─────────────────────────────────────────────────────────────────────────────
def _read_frame() -> np.ndarray | None:
    if 'image' not in request.files:
        return None
    raw   = request.files['image'].read()
    nparr = np.frombuffer(raw, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return frame


def _extract_landmarks(info):
    """
    Ambil koordinat landmark dari hasil MediaPipe untuk dikirim ke frontend.
    Ringan (hanya angka), frontend gambar sendiri di canvas.
    Koordinat sudah dalam ruang frame yang di-flip (sama dengan tampilan user).
    """
    hasil = info['hasil_mediapipe']
    landmarks = {}

    # Ambil landmark tangan — swap label jika perlu (sama seperti gambar_landmark)
    lm_kanan = hasil.right_hand_landmarks
    lm_kiri  = hasil.left_hand_landmarks
    if lm_kanan and lm_kiri:
        if lm_kanan.landmark[0].x > lm_kiri.landmark[0].x:
            lm_kanan, lm_kiri = lm_kiri, lm_kanan

    if lm_kanan:
        landmarks['right_hand'] = [
            [float(lm.x), float(lm.y)] for lm in lm_kanan.landmark
        ]
    if lm_kiri:
        landmarks['left_hand'] = [
            [float(lm.x), float(lm.y)] for lm in lm_kiri.landmark
        ]

    # Pose — bahu, siku, pergelangan
    if hasil.pose_landmarks:
        landmarks['pose'] = [
            [float(hasil.pose_landmarks.landmark[i].x),
             float(hasil.pose_landmarks.landmark[i].y)]
            for i in [11, 12, 13, 14, 15, 16]
        ]

    return landmarks


# ─────────────────────────────────────────────────────────────────────────────
# Blueprint
# ─────────────────────────────────────────────────────────────────────────────
ai_bp = Blueprint('ai_bp', __name__)


# ── /predict/huruf ────────────────────────────────────────────────────────────
@ai_bp.route('/predict/huruf', methods=['POST'])
def predict_huruf():
    """
    Prediksi huruf dari 1 frame — sama persis dengan prediksi_huruf() di uji_kamera.py.
    Menggunakan extractor persisten per session agar optical flow & decay berfungsi.
    """
    if not MODEL_HURUF_READY:
        return jsonify({'error': 'Model huruf belum siap'}), 500
    if not FE_AVAILABLE:
        return jsonify({'error': 'Feature extractor tidak tersedia'}), 500

    frame = _read_frame()
    if frame is None:
        return jsonify({'error': 'Tidak ada gambar yang dikirim'}), 400

    session_id = request.headers.get('X-Session-ID', 'default')
    sess       = _get_session(session_id)
    extractor: FeatureExtractor = sess['extractor']

    try:
        # CATATAN: frame TIDAK perlu di-flip karena react-webcam dengan
        # mirrored={true} sudah mengirim gambar yang sudah di-mirror.
        # Jika di-flip lagi, orientasi jadi salah (tidak sesuai training data).

        # Ekstrak fitur 156 menggunakan FeatureExtractor persisten
        fitur, info = extractor.extract(frame)
        landmarks   = _extract_landmarks(info)

        ada_kanan = info['ada_kanan']
        ada_kiri  = info['ada_kiri']
        tumpuk    = info['tumpuk']
        ada_pose  = info['hasil_mediapipe'].pose_landmarks is not None

        detection_status = {
            'right_hand':   bool(ada_kanan),
            'left_hand':    bool(ada_kiri),
            'overlapping':  bool(tumpuk),
            'pose':         bool(ada_pose),
        }

        # Sama dengan uji_kamera.py: prediksi_huruf() hanya jalan kalau ada tangan
        ada_tangan = ada_kanan or ada_kiri or tumpuk
        if not ada_tangan:
            return jsonify({
                'text':             '',
                'confidence':       0.0,
                'found_in_db':      False,
                'db_detail':        None,
                'detection_status': detection_status,
                'landmarks':        landmarks,
            }), 200

        # Prediksi — fitur langsung ke model (sama dengan uji_kamera.py)
        pred       = _model_huruf.predict(fitur[np.newaxis, ...], verbose=0)
        idx        = int(np.argmax(pred))
        confidence = float(pred[0][idx])

        if confidence < CONFIDENCE_HURUF:
            return jsonify({
                'text':             '',
                'confidence':       round(confidence, 4),
                'found_in_db':      False,
                'db_detail':        None,
                'detection_status': detection_status,
                'landmarks':        landmarks,
            }), 200

        huruf = _encoder_huruf.inverse_transform([idx])[0]

        db_item = KosaKata.query.filter(KosaKata.text.ilike(huruf)).first()
        return jsonify({
            'text':             huruf,
            'confidence':       round(confidence, 4),
            'found_in_db':      bool(db_item),
            'db_detail':        db_item.to_detail_dict() if db_item else None,
            'detection_status': detection_status,
            'landmarks':        landmarks,
        }), 200

    except Exception as e:
        print(f"[predict_huruf] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'error_type': type(e).__name__}), 500


# ── /predict/kata ─────────────────────────────────────────────────────────────
@ai_bp.route('/predict/kata', methods=['POST'])
def predict_kata():
    """
    Prediksi kata — sama dengan mode 'kata' di uji_kamera.py.
    Frame dikumpulkan ke buffer, saat penuh (30 frame) baru diprediksi.
    """
    if not MODEL_KATA_READY:
        return jsonify({'error': 'Model kata belum siap'}), 500

    frame = _read_frame()
    if frame is None:
        return jsonify({'error': 'Tidak ada gambar yang dikirim'}), 400

    session_id = request.headers.get('X-Session-ID', 'default')
    sess       = _get_session(session_id)
    buffer: deque               = sess['buffer']
    extractor: FeatureExtractor = sess['extractor']

    try:
        # Tidak perlu flip — sudah di-mirror oleh react-webcam
        fitur, info = extractor.extract(frame)
        landmarks   = _extract_landmarks(info)

        ada_kanan = info['ada_kanan']
        ada_kiri  = info['ada_kiri']
        tumpuk    = info['tumpuk']
        ada_pose  = info['hasil_mediapipe'].pose_landmarks is not None

        detection_status = {
            'right_hand':   bool(ada_kanan),
            'left_hand':    bool(ada_kiri),
            'overlapping':  bool(tumpuk),
            'pose':         bool(ada_pose),
        }

        # Sama dengan uji_kamera.py: tambah ke buffer hanya jika ada gerakan
        ada_sesuatu = ada_kanan or ada_kiri or tumpuk or ada_pose
        if ada_sesuatu:
            buffer.append(fitur)

        if len(buffer) < FRAME_PER_VIDEO:
            return jsonify({
                'text':             '',
                'buffer_count':     len(buffer),
                'buffer_max':       FRAME_PER_VIDEO,
                'ready':            False,
                'detection_status': detection_status,
                'landmarks':        landmarks,
            }), 200

        # Buffer penuh → prediksi (sama dengan uji_kamera.py)
        seq       = np.array(list(buffer))
        seq       = normalisasi_sekuens(seq)
        seq_input = seq[np.newaxis, ...]

        pred       = _model_kata.predict(seq_input, verbose=0)
        idx        = int(np.argmax(pred))
        confidence = float(pred[0][idx])

        if confidence > CONFIDENCE_KATA:
            kata = str(_encoder_kata.inverse_transform([idx])[0]).upper()
        else:
            kata = '?'

        # Reset buffer & extractor setelah prediksi — sama dengan uji_kamera.py
        buffer.clear()
        extractor.reset()

        db_item = None
        if kata and kata != '?':
            db_item = KosaKata.query.filter(KosaKata.text.ilike(kata)).first()

        return jsonify({
            'text':             kata,
            'confidence':       round(confidence, 4),
            'buffer_count':     0,
            'buffer_max':       FRAME_PER_VIDEO,
            'ready':            True,
            'found_in_db':      bool(db_item),
            'db_detail':        db_item.to_detail_dict() if db_item else None,
            'detection_status': detection_status,
            'landmarks':        landmarks,
        }), 200

    except Exception as e:
        print(f"[predict_kata] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


# ── /predict/kata/reset ───────────────────────────────────────────────────────
@ai_bp.route('/predict/kata/reset', methods=['POST'])
def reset_kata():
    session_id = request.headers.get('X-Session-ID', 'default')
    with _sessions_lock:
        if session_id in _sessions:
            _sessions[session_id]['buffer'].clear()
            if _sessions[session_id]['extractor']:
                _sessions[session_id]['extractor'].reset()
    return jsonify({'message': 'Buffer direset'}), 200


# ── /predict/reset ────────────────────────────────────────────────────────────
@ai_bp.route('/predict/reset', methods=['POST'])
def reset_session():
    """Reset session — dipanggil saat ganti mode atau reset manual."""
    session_id = request.headers.get('X-Session-ID', 'default')
    with _sessions_lock:
        if session_id in _sessions:
            _sessions[session_id]['buffer'].clear()
            if _sessions[session_id]['extractor']:
                _sessions[session_id]['extractor'].reset()
    return jsonify({'message': 'Session direset'}), 200


# ── /predict (backward-compatible) ───────────────────────────────────────────
@ai_bp.route('/predict', methods=['POST'])
def predict_sign():
    return predict_huruf()


# ── /predict/kata/batch ───────────────────────────────────────────────────────
@ai_bp.route('/predict/kata/batch', methods=['POST'])
def predict_kata_batch():
    """
    Prediksi kata dari batch frame — semua diproses sekuensial melalui
    FeatureExtractor baru, persis seperti uji_kamera.py memproses
    frame berurutan dari kamera.

    Frontend mengumpulkan ~30 frame di browser, lalu kirim sekaligus.
    Ini menghindari masalah frame hilang/tidak berurutan saat kirim
    satu-satu via HTTP.
    """
    if not MODEL_KATA_READY:
        return jsonify({'error': 'Model kata belum siap'}), 500
    if not FE_AVAILABLE:
        return jsonify({'error': 'Feature extractor tidak tersedia'}), 500

    frames_files = request.files.getlist('frames')
    if not frames_files:
        return jsonify({'error': 'Tidak ada frame yang dikirim'}), 400

    print(f"[predict_kata_batch] Menerima {len(frames_files)} frame")

    try:
        # Buat extractor baru — state bersih, sama seperti awal uji_kamera.py
        extractor = FeatureExtractor()
        buffer = []
        last_detection = {
            'right_hand': False,
            'left_hand': False,
            'overlapping': False,
            'pose': False,
        }

        for f in frames_files:
            raw   = f.read()
            nparr = np.frombuffer(raw, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                continue

            # Tidak perlu flip — sudah di-mirror oleh react-webcam
            fitur, info = extractor.extract(frame)

            ada_kanan = info['ada_kanan']
            ada_kiri  = info['ada_kiri']
            tumpuk    = info['tumpuk']
            ada_pose  = info['hasil_mediapipe'].pose_landmarks is not None
            ada_sesuatu = ada_kanan or ada_kiri or tumpuk or ada_pose

            if ada_sesuatu:
                buffer.append(fitur)

            last_detection = {
                'right_hand':  bool(ada_kanan),
                'left_hand':   bool(ada_kiri),
                'overlapping': bool(tumpuk),
                'pose':        bool(ada_pose),
            }

        extractor.tutup()

        print(f"[predict_kata_batch] {len(buffer)} frame valid dari {len(frames_files)} dikirim")

        if len(buffer) < 5:
            return jsonify({
                'text':             '?',
                'confidence':       0.0,
                'ready':            True,
                'found_in_db':      False,
                'db_detail':        None,
                'detection_status': last_detection,
                'message':          f'Hanya {len(buffer)} frame valid dari {len(frames_files)}',
            }), 200

        # Sesuaikan panjang ke FRAME_PER_VIDEO (padding/sampling)
        seq       = sesuaikan_panjang(buffer, FRAME_PER_VIDEO)
        seq       = normalisasi_sekuens(seq)
        seq_input = seq[np.newaxis, ...]

        pred       = _model_kata.predict(seq_input, verbose=0)
        idx        = int(np.argmax(pred))
        confidence = float(pred[0][idx])

        if confidence > CONFIDENCE_KATA:
            kata = str(_encoder_kata.inverse_transform([idx])[0]).upper()
        else:
            kata = '?'

        db_item = None
        if kata and kata != '?':
            db_item = KosaKata.query.filter(KosaKata.text.ilike(kata)).first()

        print(f"[predict_kata_batch] Hasil: '{kata}' (confidence: {confidence:.2%})")

        return jsonify({
            'text':             kata,
            'confidence':       round(confidence, 4),
            'ready':            True,
            'found_in_db':      bool(db_item),
            'db_detail':        db_item.to_detail_dict() if db_item else None,
            'detection_status': last_detection,
        }), 200

    except Exception as e:
        print(f"[predict_kata_batch] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


# ── /debug/hand-detection ─────────────────────────────────────────────────────
# Endpoint khusus untuk debug: cek apakah MediaPipe bisa mendeteksi tangan
@ai_bp.route('/debug/hand-detection', methods=['POST'])
def debug_hand_detection():
    """
    Endpoint untuk diagnosa: apakah MediaPipe bisa mendeteksi tangan dan fitur?
    Kirim gambar, dapatkan detail deteksi lengkap.
    """
    if not MODEL_HURUF_READY or not FE_AVAILABLE:
        return jsonify({'error': 'Model atau feature extractor belum siap'}), 500

    frame = _read_frame()
    if frame is None:
        return jsonify({'error': 'Tidak ada gambar yang dikirim'}), 400

    try:
        # Tidak perlu flip — sudah di-mirror oleh react-webcam

        # Ekstrak fitur menggunakan FeatureExtractor
        extractor_temp = FeatureExtractor()
        fitur, info = extractor_temp.extract(frame)
        extractor_temp.tutup()

        h, w = frame.shape[:2]

        diagnostics = {
            'frame_shape': [h, w],
            'feature_extraction': {
                'total_features': len(fitur),
                'features_valid': not np.any(np.isnan(fitur)),
            },
            'hand_detection': {
                'right_hand_detected': info['ada_kanan'],
                'left_hand_detected': info['ada_kiri'],
                'hands_overlapping': info['tumpuk'],
                'pose_detected': info['hasil_mediapipe'].pose_landmarks is not None,
            },
            'recommended_action': ''
        }

        ada_sesuatu = (
            info['ada_kanan'] or
            info['ada_kiri']  or
            info['tumpuk']    or
            (info['hasil_mediapipe'].pose_landmarks is not None)
        )

        if not ada_sesuatu:
            diagnostics['recommended_action'] = (
                "⚠️ Tidak ada gerakan tangan/pose terdeteksi. Coba:\n"
                "1. Pastikan tangan terlihat jelas di kamera\n"
                "2. Tingkatkan pencahayaan\n"
                "3. Posisikan tangan lebih dekat ke kamera\n"
                "4. Gunakan background yang lebih gelap/kontras"
            )
        else:
            diagnostics['recommended_action'] = (
                f"✅ Gerakan terdeteksi! "
                f"Kanan: {info['ada_kanan']}, Kiri: {info['ada_kiri']}, "
                f"Tumpuk: {info['tumpuk']}. Sistem siap untuk prediksi."
            )

        print(f"[debug_hand_detection] {diagnostics['recommended_action']}")
        return jsonify(diagnostics), 200

    except Exception as e:
        print(f"[debug_hand_detection] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'error_type': type(e).__name__,
        }), 500