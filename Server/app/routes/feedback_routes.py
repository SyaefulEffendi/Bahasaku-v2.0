from flask import Blueprint, request, jsonify, abort
from marshmallow import ValidationError
from app.models.feedback_model import Feedback
from app.extensions import db
from app.schemas import feedback_schema
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user_model import User

feedback_bp = Blueprint('feedback_bp', __name__)

def is_admin(user_id):
    user = User.query.get(user_id)
    return user and user.role == 'Admin'


@feedback_bp.route('/', methods=['POST'])
@jwt_required() # 1. Wajibkan Login
def create_feedback():
    try:
        # 2. Ambil User ID dari Token (User yang sedang login)
        current_user_id = int(get_jwt_identity())
        
        raw_data = request.get_json() or {}
        
        # 3. Masukkan user_id ke dalam data sebelum validasi
        # Kita memaksa user_id sesuai token, mengabaikan input user_id dari client jika ada
        raw_data['user_id'] = current_user_id
        
        # Validasi input menggunakan schema
        # Pastikan schema Anda memperbolehkan user_id (atau exclude user_id dari load jika user_id diisi manual)
        # Disini kita asumsikan feedback_schema bisa memvalidasi data lengkap
        data = feedback_schema.load(raw_data)
        
        # Buat feedback baru
        fb = Feedback(**data)
        db.session.add(fb)
        db.session.commit()
        
        return jsonify({
            'message': 'Feedback created successfully',
            'feedback': feedback_schema.dump(fb)
        }), 201
    except ValidationError as err:
        return jsonify({'error': 'Validation error', 'messages': err.messages}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@feedback_bp.route('/', methods=['GET'])
def list_feedback():
    feedback = Feedback.query.order_by(Feedback.created_at.desc()).all()
    return jsonify([f.to_profile_dict() for f in feedback])


@feedback_bp.route('/<int:feedback_id>', methods=['GET'])
def get_feedback(feedback_id):
    fb = Feedback.query.get_or_404(feedback_id)
    return jsonify(fb.to_profile_dict())


@feedback_bp.route('/<int:feedback_id>', methods=['DELETE'])
@jwt_required()
def delete_feedback(feedback_id):
    try:
        current_user_id = int(get_jwt_identity())
    except Exception:
        return jsonify({"error": "Invalid token identity."}), 401

    if not is_admin(current_user_id):
        return jsonify({"error": "Akses ditolak. Diperlukan hak Admin."}), 403

    fb = Feedback.query.get_or_404(feedback_id)
    db.session.delete(fb)
    db.session.commit()
    return jsonify({'message': f'Feedback with ID {feedback_id} deleted'}), 200

@feedback_bp.route('/<int:feedback_id>', methods=['PUT'])
@jwt_required()
def update_feedback_status(feedback_id):
    try:
        current_user_id = int(get_jwt_identity())
    except Exception:
        return jsonify({"error": "Invalid token identity."}), 401

    # Pastikan hanya Admin yang bisa update status
    if not is_admin(current_user_id):
        return jsonify({"error": "Akses ditolak. Diperlukan hak Admin."}), 403

    fb = Feedback.query.get_or_404(feedback_id)
    data = request.get_json()
    new_status = data.get('status')

    # Validasi status harus sesuai dengan yang ada di model
    ALLOWED_STATUS = ['Baru', 'Ditinjau', 'Selesai']
    if new_status not in ALLOWED_STATUS:
        return jsonify({'error': 'Status tidak valid.'}), 400

    fb.status = new_status
    db.session.commit()

    return jsonify({
        'message': f'Status feedback updated to {new_status}',
        'feedback': fb.to_profile_dict()
    }), 200