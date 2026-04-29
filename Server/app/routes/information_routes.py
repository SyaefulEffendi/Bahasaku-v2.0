from flask import Blueprint, request, jsonify, current_app, url_for
from app.models.information_model import Information
from app.extensions import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user_model import User
import os
import datetime
from werkzeug.utils import secure_filename

information_bp = Blueprint('information_bp', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_admin(user_id):
    user = User.query.get(user_id)
    return user and user.role == 'Admin'

# --- GET ALL (Bisa limit untuk Dashboard) ---
@information_bp.route('/', methods=['GET'])
def get_informations():
    # Ambil parameter limit dari URL. Contoh: /api/information?limit=2
    limit = request.args.get('limit', type=int)
    
    query = Information.query.order_by(Information.created_at.desc())
    
    if limit:
        items = query.limit(limit).all()
    else:
        items = query.all()
        
    return jsonify([item.to_dict() for item in items]), 200

# --- GET DETAIL (Saat diklik) ---
@information_bp.route('/<int:id>', methods=['GET'])
def get_information_detail(id):
    item = Information.query.get_or_404(id)
    return jsonify(item.to_dict()), 200

# --- CREATE (Admin Only) ---
@information_bp.route('/', methods=['POST'])
@jwt_required()
def create_information():
    try:
        user_id = int(get_jwt_identity())
        if not is_admin(user_id):
            return jsonify({"error": "Unauthorized"}), 403
            
        data = request.form
        title = data.get('title')
        content = data.get('content')
        
        if not title or not content:
            return jsonify({"error": "Judul dan Konten wajib diisi"}), 400
            
        # Handle Upload Gambar
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"info_{int(datetime.datetime.utcnow().timestamp())}_{file.filename}")
                save_dir = os.path.join(current_app.root_path, 'static', 'info_images')
                os.makedirs(save_dir, exist_ok=True)
                file.save(os.path.join(save_dir, filename))
                
                # Buat URL localhost
                image_url = url_for('static', filename=f'info_images/{filename}')
                # Jika ingin full URL: f"http://localhost:5000{url_for(...)}"
        
        new_info = Information(
            title=title,
            content=content,
            image_url=image_url,
            created_by_id=user_id
        )
        
        db.session.add(new_info)
        db.session.commit()
        
        return jsonify({"message": "Informasi berhasil dibuat", "data": new_info.to_dict()}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

#Update (Admin Only) ---
@information_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_information(id):
    try:
        user_id = int(get_jwt_identity())
        if not is_admin(user_id):
            return jsonify({"error": "Unauthorized"}), 403
            
        info = Information.query.get_or_404(id)
        
        # Ambil data form (Multipart)
        data = request.form
        title = data.get('title')
        content = data.get('content')
        
        # Update Text
        if title: info.title = title
        if content: info.content = content
        
        # Update Image (Jika ada file baru)
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                # 1. Hapus gambar lama
                if info.image_url:
                    try:
                        old_filename = info.image_url.split('/')[-1]
                        old_path = os.path.join(current_app.root_path, 'static', 'info_images', old_filename)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    except Exception:
                        pass # Lanjut saja jika gagal hapus

                # 2. Simpan gambar baru
                filename = secure_filename(f"info_{int(datetime.datetime.utcnow().timestamp())}_{file.filename}")
                save_dir = os.path.join(current_app.root_path, 'static', 'info_images')
                os.makedirs(save_dir, exist_ok=True)
                file.save(os.path.join(save_dir, filename))
                
                info.image_url = url_for('static', filename=f'info_images/{filename}')

        # Update Jejak Audit
        info.updated_by_id = user_id
        # updated_at otomatis terisi oleh database (onupdate=func.now())
        
        db.session.commit()
        return jsonify({"message": "Informasi berhasil diupdate", "data": info.to_dict()}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- DELETE (Admin Only) ---
@information_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_information(id):
    try:
        user_id = int(get_jwt_identity())
        if not is_admin(user_id):
            return jsonify({"error": "Unauthorized"}), 403
            
        info = Information.query.get_or_404(id)
        
        # Hapus file gambar fisik jika ada
        if info.image_url:
            try:
                # Ambil nama file dari URL
                filename = info.image_url.split('/')[-1]
                path = os.path.join(current_app.root_path, 'static', 'info_images', filename)
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass
                
        db.session.delete(info)
        db.session.commit()
        
        return jsonify({"message": "Informasi berhasil dihapus"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500