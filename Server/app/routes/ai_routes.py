"""
ai_routes.py
Mendukung DUA mode prediksi:
  1. POST /ai/predict/huruf  → model MediaPipe (1 frame, model_1tangan / model_2tangan)
  2. POST /ai/predict/kata   → model LSTM      (buffer 30 frame, model_kata)
  3. POST /ai/predict        → backward-compatible, diteruskan ke /huruf

Struktur folder yang diharapkan (sesuai proyek Anda):
  Server/
  ├── app/
  │   ├── models_ml/
  │   │   ├── model_1tangan.h5
  │   │   ├── model_2tangan.h5
  │   │   ├── model_kata.keras  (atau model_kata.h5)
  │   │   ├── label_encoder_1tangan.pkl
  │   │   ├── label_encoder_2tangan.pkl
  │   │   └── label_encoder_kata.pkl
  │   └── routes/
  │       └── ai_routes.py   ← file ini
  └── scripts/
      └── kata/
          └── feature_extractor.py   ← diimport di sini
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
# os.getcwd() saat Flask jalan = folder Server/ (tempat run flask / python app.py)
# Jadi path-nya: Server/scripts/kata/feature_extractor.py
_FE_DIR = os.path.join(os.getcwd(), 'scripts', 'kata')
if not os.path.isdir(_FE_DIR):
    # Fallback jika dijalankan dari dalam folder app/
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
# Konstanta
# ─────────────────────────────────────────────────────────────────────────────
CONFIDENCE_HURUF  = 0.5
CONFIDENCE_KATA   = 0.5
FRAME_PER_VIDEO   = 30

# ─────────────────────────────────────────────────────────────────────────────
# Load semua model (sekali saat startup)
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 55)
print("[ai_routes] Memuat model ML...")

# --- Model huruf ---
try:
    _model_1t = tf.keras.models.load_model(os.path.join(MODEL_DIR, 'model_1tangan.h5'))
    _model_2t = tf.keras.models.load_model(os.path.join(MODEL_DIR, 'model_2tangan.h5'))
    with open(os.path.join(MODEL_DIR, 'label_encoder_1tangan.pkl'), 'rb') as f:
        _encoder_1t = pickle.load(f)
    with open(os.path.join(MODEL_DIR, 'label_encoder_2tangan.pkl'), 'rb') as f:
        _encoder_2t = pickle.load(f)
    import mediapipe as mp
    _mp_hands = mp.solutions.hands
    _hands = _mp_hands.Hands(
        max_num_hands=2,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.3
    )
    MODEL_HURUF_READY = True
    print("[ai_routes] ✓ Model huruf (1tangan & 2tangan) berhasil dimuat.")
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
# Session buffer untuk mode kata (satu buffer per tab browser)
# ─────────────────────────────────────────────────────────────────────────────
_sessions: dict = {}
_sessions_lock  = threading.Lock()


def _get_session(session_id: str) -> dict:
    with _sessions_lock:
        if session_id not in _sessions:
            _sessions[session_id] = {
                'buffer':    deque(maxlen=FRAME_PER_VIDEO),
                'extractor': FeatureExtractor() if FE_AVAILABLE else None,
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


# ─────────────────────────────────────────────────────────────────────────────
# Blueprint
# ─────────────────────────────────────────────────────────────────────────────
ai_bp = Blueprint('ai_bp', __name__)


# ── /predict/huruf ────────────────────────────────────────────────────────────
@ai_bp.route('/predict/huruf', methods=['POST'])
def predict_huruf():
    if not MODEL_HURUF_READY:
        return jsonify({'error': 'Model huruf belum siap'}), 500

    frame = _read_frame()
    if frame is None:
        return jsonify({'error': 'Tidak ada gambar yang dikirim'}), 400

    try:
        frame   = cv2.flip(frame, 1)
        rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = _hands.process(rgb)

        if not results.multi_hand_landmarks:
            print(f"[predict_huruf] ⚠️ Tidak ada tangan terdeteksi di frame")
            return jsonify({'text': '', 'confidence': 0.0, 'found_in_db': False, 'db_detail': None}), 200

        jumlah = len(results.multi_hand_landmarks)
        print(f"[predict_huruf] ✓ Terdeteksi {jumlah} tangan")

        if jumlah == 1:
            coords = []
            for lm in results.multi_hand_landmarks[0].landmark:
                coords.extend([lm.x, lm.y, lm.z])
            pred       = _model_1t.predict(np.array([coords]), verbose=0)
            idx        = int(np.argmax(pred))
            confidence = float(pred[0][idx])
            huruf      = _encoder_1t.inverse_transform([idx])[0] if confidence >= CONFIDENCE_HURUF else ''
            print(f"[predict_huruf] 1 tangan: {huruf} (confidence: {confidence:.4f})")
        else:
            coords = []
            for hl in results.multi_hand_landmarks[:2]:
                for lm in hl.landmark:
                    coords.extend([lm.x, lm.y, lm.z])
            pred       = _model_2t.predict(np.array([coords]), verbose=0)
            idx        = int(np.argmax(pred))
            confidence = float(pred[0][idx])
            huruf      = _encoder_2t.inverse_transform([idx])[0] if confidence >= CONFIDENCE_HURUF else ''
            print(f"[predict_huruf] 2 tangan: {huruf} (confidence: {confidence:.4f})")

        if not huruf:
            return jsonify({'text': '', 'confidence': round(confidence, 4), 'found_in_db': False, 'db_detail': None}), 200

        db_item = KosaKata.query.filter(KosaKata.text.ilike(huruf)).first()
        return jsonify({
            'text':        huruf,
            'confidence':  round(confidence, 4),
            'found_in_db': bool(db_item),
            'db_detail':   db_item.to_detail_dict() if db_item else None,
        }), 200

    except Exception as e:
        print(f"[predict_huruf] Error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ── /predict/kata ─────────────────────────────────────────────────────────────
@ai_bp.route('/predict/kata', methods=['POST'])
def predict_kata():
    if not MODEL_KATA_READY:
        return jsonify({'error': 'Model kata belum siap'}), 500

    frame = _read_frame()
    if frame is None:
        return jsonify({'error': 'Tidak ada gambar yang dikirim'}), 400

    session_id = request.headers.get('X-Session-ID', 'default')
    sess       = _get_session(session_id)
    buffer: deque              = sess['buffer']
    extractor: FeatureExtractor = sess['extractor']

    try:
        frame = cv2.flip(frame, 1)
        fitur, info = extractor.extract(frame)

        ada_sesuatu = (
            info['ada_kanan'] or
            info['ada_kiri']  or
            info['tumpuk']    or
            (info['hasil_mediapipe'].pose_landmarks is not None)
        )
        if ada_sesuatu:
            buffer.append(fitur)
            if len(buffer) % 5 == 0:  # Log setiap 5 frame
                tangan_status = f"kanan: {info['ada_kanan']}, kiri: {info['ada_kiri']}"
                print(f"[predict_kata] Buffer: {len(buffer)}/{FRAME_PER_VIDEO} ({tangan_status})")
        else:
            if len(buffer) > 0:  # Hanya log jika ada yang sebelumnya tertambah
                print(f"[predict_kata] ⚠️ Gerakan tangan tidak terdeteksi, buffer hold di {len(buffer)}")

        if len(buffer) < FRAME_PER_VIDEO:
            return jsonify({
                'text':         '',
                'buffer_count': len(buffer),
                'buffer_max':   FRAME_PER_VIDEO,
                'ready':        False,
            }), 200

        # Buffer penuh → prediksi
        seq       = sesuaikan_panjang(list(buffer), FRAME_PER_VIDEO)
        seq       = normalisasi_sekuens(seq)
        seq_input = seq[np.newaxis, ...]

        pred       = _model_kata.predict(seq_input, verbose=0)
        idx        = int(np.argmax(pred))
        confidence = float(pred[0][idx])
        kata       = str(_encoder_kata.inverse_transform([idx])[0]).upper() if confidence >= CONFIDENCE_KATA else ''

        buffer.clear()
        extractor.reset()

        if not kata:
            return jsonify({
                'text':         '',
                'confidence':   round(confidence, 4),
                'buffer_count': 0,
                'buffer_max':   FRAME_PER_VIDEO,
                'ready':        True,
                'found_in_db':  False,
                'db_detail':    None,
            }), 200

        db_item = KosaKata.query.filter(KosaKata.text.ilike(kata)).first()
        return jsonify({
            'text':         kata,
            'confidence':   round(confidence, 4),
            'buffer_count': 0,
            'buffer_max':   FRAME_PER_VIDEO,
            'ready':        True,
            'found_in_db':  bool(db_item),
            'db_detail':    db_item.to_detail_dict() if db_item else None,
        }), 200

    except Exception as e:
        print(f"[predict_kata] Error: {e}")
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


# ── /predict (backward-compatible) ───────────────────────────────────────────
@ai_bp.route('/predict', methods=['POST'])
def predict_sign():
    return predict_huruf()


# ── /debug/hand-detection ─────────────────────────────────────────────────────
# Endpoint khusus untuk debug: cek apakah MediaPipe bisa mendeteksi tangan
@ai_bp.route('/debug/hand-detection', methods=['POST'])
def debug_hand_detection():
    """
    Endpoint untuk diagnosa: apakah MediaPipe bisa mendeteksi tangan?
    Kirim gambar, dapatkan detail deteksi lengkap.
    """
    if not MODEL_HURUF_READY:
        return jsonify({'error': 'Model huruf belum siap'}), 500

    frame = _read_frame()
    if frame is None:
        return jsonify({'error': 'Tidak ada gambar yang dikirim'}), 400

    try:
        frame = cv2.flip(frame, 1)
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Proses dengan berbagai confidence level
        results = _hands.process(rgb)
        
        h, w = frame.shape[:2]
        
        diagnostics = {
            'frame_shape': [h, w],
            'hands_detected': False,
            'num_hands': 0,
            'hand_details': [],
            'mediapipe_settings': {
                'min_detection_confidence': 0.5,
                'min_tracking_confidence': 0.3,
                'max_num_hands': 2,
            },
            'recommended_action': ''
        }
        
        if not results.multi_hand_landmarks:
            diagnostics['recommended_action'] = (
                "❌ Tangan tidak terdeteksi. Coba:\n"
                "1. Pastikan tangan terlihat jelas di kamera\n"
                "2. Tingkatkan pencahayaan\n"
                "3. Posisikan tangan lebih dekat ke kamera\n"
                "4. Gunakan background yang lebih gelap/kontras"
            )
        else:
            diagnostics['hands_detected'] = True
            diagnostics['num_hands'] = len(results.multi_hand_landmarks)
            
            for i, hand_lm in enumerate(results.multi_hand_landmarks):
                hand_info = {
                    'index': i,
                    'num_landmarks': len(hand_lm.landmark),
                    'wrist_position': {
                        'x': round(hand_lm.landmark[0].x, 3),
                        'y': round(hand_lm.landmark[0].y, 3),
                        'z': round(hand_lm.landmark[0].z, 3),
                    },
                    'all_landmarks': [
                        {
                            'index': j,
                            'x': round(lm.x, 3),
                            'y': round(lm.y, 3),
                            'z': round(lm.z, 3),
                        }
                        for j, lm in enumerate(hand_lm.landmark)
                    ]
                }
                diagnostics['hand_details'].append(hand_info)
            
            diagnostics['recommended_action'] = (
                f"✅ Terdeteksi {diagnostics['num_hands']} tangan! "
                "Sistem siap untuk prediksi."
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