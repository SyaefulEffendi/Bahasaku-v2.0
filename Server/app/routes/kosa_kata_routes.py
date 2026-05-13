from flask import Blueprint, request, jsonify
from app.models.kosa_kata_model import KosaKata
from app.extensions import db
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user_model import User
import os
from werkzeug.utils import secure_filename
from flask import current_app, url_for
import datetime

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}  # Format video yang diizinkan

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_admin(user_id):
    user = User.query.get(user_id)
    return user and user.role == 'Admin'

kosa_kata_bp = Blueprint('kosa_kata_bp', __name__)


@kosa_kata_bp.route('/', methods=['POST'])
@jwt_required()
def create_kosa_kata():
    try:
        current_user_id = int(get_jwt_identity())
    except Exception:
        return jsonify({"error": "Invalid token identity."}), 401

    if not is_admin(current_user_id):
        return jsonify({"error": "Akses ditolak. Diperlukan hak Admin."}), 403

    data = request.form or {}
    text = data.get('text')
    category = data.get('category', 'Lainnya')

    if not text:
        return jsonify({'error': 'text is required'}), 400

    if 'video' not in request.files:
        return jsonify({'error': 'Video file is required'}), 400

    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Format file tidak didukung. Gunakan mp4/avi/mov/mkv.'}), 400

    filename = secure_filename(f"{text}_{int(datetime.datetime.utcnow().timestamp())}_{file.filename}")
    save_dir = os.path.join(current_app.root_path, 'static', 'videos')
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, filename)

    try:
        file.save(save_path)
    except Exception as e:
        return jsonify({'error': f'Gagal menyimpan file: {str(e)}'}), 500

    video_url = url_for('static', filename=f'videos/{filename}')

    kk = KosaKata(text=text, video_file_path=video_url, category=category, added_by_admin_id=current_user_id)
    db.session.add(kk)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        try:
            if os.path.exists(save_path):
                os.remove(save_path)
        except Exception:
            pass
        return jsonify({'error': 'text must be unique'}), 400

    return jsonify({'message': 'KosaKata created', 'kosa_kata': kk.to_detail_dict()}), 201


@kosa_kata_bp.route('/', methods=['GET'])
def list_kosa_kata():
    items = KosaKata.query.order_by(KosaKata.created_at.desc()).all()
    return jsonify([i.to_detail_dict() for i in items])


@kosa_kata_bp.route('/<int:item_id>', methods=['GET'])
def get_kosa_kata(item_id):
    item = KosaKata.query.get_or_404(item_id)
    return jsonify(item.to_detail_dict())


@kosa_kata_bp.route('/<int:item_id>', methods=['PUT', 'PATCH'])
@jwt_required()
def update_kosa_kata(item_id):
    try:
        current_user_id = int(get_jwt_identity())
    except Exception:
        return jsonify({"error": "Invalid token identity."}), 401

    if not is_admin(current_user_id):
        return jsonify({"error": "Akses ditolak. Diperlukan hak Admin."}), 403

    item = KosaKata.query.get_or_404(item_id)
    data = request.form or {}
    text = data.get('text')
    category = data.get('category')

    old_video_path = None
    if 'video' in request.files:
        file = request.files['video']
        if file.filename != '':
            if not allowed_file(file.filename):
                return jsonify({'error': 'Format file tidak didukung. Gunakan mp4/avi/mov/mkv.'}), 400

            filename = secure_filename(f"{text or item.text}_{int(datetime.datetime.utcnow().timestamp())}_{file.filename}")
            save_dir = os.path.join(current_app.root_path, 'static', 'videos')
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, filename)

            try:
                file.save(save_path)
                old_video_path = item.video_file_path
                item.video_file_path = url_for('static', filename=f'videos/{filename}')
            except Exception as e:
                return jsonify({'error': f'Gagal menyimpan file: {str(e)}'}), 500

    if text:
        item.text = text
    if category:
        item.category = category

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'text must be unique'}), 400

    # Hapus video lama jika ada
    if old_video_path:
        try:
            old_filename = old_video_path.split('/videos/')[-1]
            old_path = os.path.join(current_app.root_path, 'static', 'videos', old_filename)
            if os.path.exists(old_path):
                os.remove(old_path)
        except Exception:
            pass

    return jsonify({'message': 'KosaKata updated', 'kosa_kata': item.to_detail_dict()})


@kosa_kata_bp.route('/<int:item_id>', methods=['DELETE'])
@jwt_required()
def delete_kosa_kata(item_id):
    try:
        current_user_id = int(get_jwt_identity())
    except Exception:
        return jsonify({"error": "Invalid token identity."}), 401

    if not is_admin(current_user_id):
        return jsonify({"error": "Akses ditolak. Diperlukan hak Admin."}), 403

    item = KosaKata.query.get_or_404(item_id)

    # Hapus file video
    try:
        video_filename = item.video_file_path.split('/videos/')[-1]
        video_path = os.path.join(current_app.root_path, 'static', 'videos', video_filename)
        if os.path.exists(video_path):
            os.remove(video_path)
    except Exception:
        pass

    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': f'KosaKata with ID {item_id} deleted'}), 200
