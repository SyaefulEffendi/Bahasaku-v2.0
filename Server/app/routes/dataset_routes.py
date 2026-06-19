import os
import sys
import numpy as np
import pandas as pd
import cv2
import subprocess
from flask import Blueprint, request, jsonify, current_app
from threading import Lock

csv_lock = Lock()

# ── Import feature_extractor dari scripts/kata/ ───────────────────────────────
_FE_DIR = os.path.join(os.getcwd(), 'scripts', 'kata')
if not os.path.isdir(_FE_DIR):
    _FE_DIR = os.path.join(os.getcwd(), '..', 'scripts', 'kata')
sys.path.insert(0, os.path.abspath(_FE_DIR))

try:
    from feature_extractor import FeatureExtractor, normalisasi_sekuens, sesuaikan_panjang, N_FITUR
    FE_AVAILABLE = True
except ImportError as e:
    FE_AVAILABLE = False
    print(f"[dataset_routes] PERINGATAN: Tidak bisa import feature_extractor → {e}")

dataset_bp = Blueprint('dataset_bp', __name__)

DATASET_KATA_CSV = os.path.join(os.getcwd(), 'dataset', 'kata', 'dataset_kata.csv')
DATASET_HURUF_CSV = os.path.join(os.getcwd(), 'dataset', 'huruf', 'dataset_huruf.csv')
FRAME_PER_VIDEO = 30
KOLOM_CSV = [f'f{i}' for i in range(156)] + ['label'] # N_FITUR is 156

def ensure_dataset_dir(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        df = pd.DataFrame(columns=KOLOM_CSV)
        df.to_csv(path, index=False)

@dataset_bp.route('/record/kata', methods=['POST'])
def record_kata():
    if not FE_AVAILABLE:
        return jsonify({'error': 'Feature extractor tidak tersedia'}), 500

    target_kata = request.form.get('label')
    if not target_kata:
        return jsonify({'error': 'Label (kata) tidak diberikan'}), 400
    
    target_kata = target_kata.lower() # Biasanya kata di dataset huruf kecil

    frames_files = request.files.getlist('frames')
    if not frames_files:
        return jsonify({'error': 'Tidak ada frame yang dikirim'}), 400

    ensure_dataset_dir(DATASET_KATA_CSV)

    try:
        extractor = FeatureExtractor()
        buffer = []

        for f in frames_files:
            raw = f.read()
            nparr = np.frombuffer(raw, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                continue

            fitur, info = extractor.extract(frame)
            
            # Terima frame selama pose terdeteksi atau tangan (sama seperti script asli)
            pose_ok = info['hasil_mediapipe'].pose_landmarks is not None
            if pose_ok or info['ada_kanan'] or info['ada_kiri']:
                buffer.append(fitur)

        extractor.tutup()

        if len(buffer) >= int(FRAME_PER_VIDEO * 0.8): # minimal 24 frame
            seq = sesuaikan_panjang(buffer, FRAME_PER_VIDEO)
            seq = normalisasi_sekuens(seq)
            
            data_baru = []
            for baris in seq:
                data_baru.append(list(baris) + [target_kata])
                
            df_baru = pd.DataFrame(data_baru, columns=KOLOM_CSV)
            
            with csv_lock:
                is_new_file = not os.path.exists(DATASET_KATA_CSV)
                df_baru.to_csv(DATASET_KATA_CSV, mode='a', header=is_new_file, index=False)
                
                # Baca total video secara efisien (tanpa memuat seluruh isi jika tidak perlu, tapi di sini kita baca lagi untuk amannya)
                df_gabung = pd.read_csv(DATASET_KATA_CSV)
                total_video = len(df_gabung[df_gabung['label'] == target_kata]) // FRAME_PER_VIDEO
            
            return jsonify({
                'message': 'Berhasil menyimpan video kata',
                'label': target_kata,
                'total_video_tersimpan': total_video
            }), 200
        else:
            return jsonify({
                'error': f'Gagal menyimpan, frame valid hanya {len(buffer)} dari {FRAME_PER_VIDEO}',
                'frames_valid': len(buffer)
            }), 400

    except Exception as e:
        print(f"[record_kata] Error: {e}")
        return jsonify({'error': str(e)}), 500


@dataset_bp.route('/record/huruf', methods=['POST'])
def record_huruf():
    if not FE_AVAILABLE:
        return jsonify({'error': 'Feature extractor tidak tersedia'}), 500

    target_huruf = request.form.get('label')
    if not target_huruf:
        return jsonify({'error': 'Label (huruf) tidak diberikan'}), 400
        
    target_huruf = target_huruf.upper() # Huruf biasanya kapital

    if 'image' not in request.files:
        return jsonify({'error': 'Tidak ada gambar yang dikirim'}), 400

    ensure_dataset_dir(DATASET_HURUF_CSV)

    try:
        raw = request.files['image'].read()
        nparr = np.frombuffer(raw, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
             return jsonify({'error': 'Gambar tidak valid'}), 400

        extractor = FeatureExtractor()
        fitur, info = extractor.extract(frame)
        extractor.tutup()

        ada_tangan = info['ada_kanan'] or info['ada_kiri'] or info['tumpuk']
        
        if not ada_tangan:
             return jsonify({'error': 'Tidak ada tangan terdeteksi'}), 400

        data_baru = [list(fitur) + [target_huruf]]
        df_baru = pd.DataFrame(data_baru, columns=KOLOM_CSV)
        
        with csv_lock:
            is_new_file = not os.path.exists(DATASET_HURUF_CSV)
            df_baru.to_csv(DATASET_HURUF_CSV, mode='a', header=is_new_file, index=False)
            
            # Hitung total
            df_gabung = pd.read_csv(DATASET_HURUF_CSV)
            total_sample = len(df_gabung[df_gabung['label'] == target_huruf])

        return jsonify({
            'message': 'Berhasil menyimpan frame huruf',
            'label': target_huruf,
            'total_sample_tersimpan': total_sample
        }), 200

    except Exception as e:
        print(f"[record_huruf] Error: {e}")
        return jsonify({'error': str(e)}), 500

@dataset_bp.route('/stats', methods=['GET'])
def dataset_stats():
    stats = {'kata': {}, 'huruf': {}}
    
    if os.path.exists(DATASET_KATA_CSV):
        df_kata = pd.read_csv(DATASET_KATA_CSV)
        counts = df_kata['label'].value_counts()
        for label, count in counts.items():
            stats['kata'][label] = count // FRAME_PER_VIDEO

    if os.path.exists(DATASET_HURUF_CSV):
        df_huruf = pd.read_csv(DATASET_HURUF_CSV)
        counts = df_huruf['label'].value_counts()
        for label, count in counts.items():
            stats['huruf'][label] = int(count)
            
    return jsonify(stats), 200

@dataset_bp.route('/train/<tipe>', methods=['POST'])
def train_model(tipe):
    if tipe not in ['kata', 'huruf']:
        return jsonify({'error': 'Tipe tidak valid. Gunakan kata atau huruf.'}), 400
        
    script_path = os.path.join(os.getcwd(), 'scripts', tipe, f'train_{tipe}.py')
    
    if not os.path.exists(script_path):
         # Cek fallback jika os.getcwd() di server
         script_path = os.path.join(os.getcwd(), '..', 'scripts', tipe, f'train_{tipe}.py')
         if not os.path.exists(script_path):
             return jsonify({'error': f'Skrip training {script_path} tidak ditemukan'}), 404

    try:
        # Menjalankan script menggunakan subprocess
        # script train_.py butuh current working directory-nya di folder script tersebut karena ada sys.path.insert(0, os.path.dirname...)
        # Kita set cwd ke folder dari scriptnya
        script_dir = os.path.dirname(script_path)
        
        # Eksekusi secara sinkronus dan kumpulkan output
        # Gunakan environment utf-8 agar karakter spesial (seperti tanda panah / checklist) tidak menyebabkan UnicodeEncodeError
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        result = subprocess.run(
            [sys.executable, os.path.basename(script_path)],
            cwd=script_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            env=env
        )

        if result.returncode == 0:
            return jsonify({
                'message': f'Training {tipe} selesai',
                'log': result.stdout
            }), 200
        else:
            return jsonify({
                'error': f'Training {tipe} gagal',
                'log': result.stderr + "\n" + result.stdout
            }), 500

    except Exception as e:
        print(f"[train_model] Error: {e}")
        return jsonify({'error': str(e)}), 500
