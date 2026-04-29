from flask import Blueprint, request, jsonify
from app.models.kosa_kata_model import KosaKata
import cv2
import numpy as np
import os

ai_bp = Blueprint('ai_bp', __name__)

# Mengatur path model
MODEL_PATH = os.path.join(os.getcwd(), 'app', 'models_ml', 'best.pt') 

try:
    # Load model sekali saat aplikasi start
    model = YOLO(MODEL_PATH)
    print("YOLOv8 Model Loaded Successfully!")
except Exception as e:
    print(f"Error loading YOLO model: {e}")
    model = None

@ai_bp.route('/predict', methods=['POST'])
def predict_sign():
    if not model:
        return jsonify({'error': 'Model ML belum siap'}), 500
        
    if 'image' not in request.files:
        return jsonify({'error': 'No image sent'}), 400
        
    try:
        file = request.files['image']
        
        # 1. Baca gambar dari request
        img_bytes = file.read()
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # 2. Prediksi menggunakan YOLO
        # conf=0.60   -> Hanya ambil jika yakin > 60% (Filter gerakan ragu-ragu)
        # verbose=False -> Matikan log di terminal agar lebih cepat
        # max_det DIHAPUS -> Agar gerakan 2 tangan (seperti huruf A di SIBI) tetap terdeteksi utuh
        results = model(img, conf=0.60, verbose=False) 
        
        detected_text = None
        confidence = 0
        
        # Ambil hasil prediksi
        # Kita ambil deteksi dengan confidence tertinggi
        for result in results:
            if result.boxes:
                # result.boxes[0] otomatis adalah box dengan confidence tertinggi di YOLO
                box = result.boxes[0] 
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                detected_text = model.names[class_id]
                break # Ambil yang paling akurat saja
                
        if not detected_text:
            return jsonify({'text': '', 'found_in_db': False}), 200
            
        # 3. Cek Database
        db_item = KosaKata.query.filter(KosaKata.text.ilike(detected_text)).first()
        
        return jsonify({
            'text': detected_text,
            'confidence': confidence,
            'found_in_db': bool(db_item),
            'db_detail': db_item.to_detail_dict() if db_item else None
        })

    except Exception as e:
        print(f"Error during prediction: {e}")
        return jsonify({'error': 'Internal server error processing image'}), 500