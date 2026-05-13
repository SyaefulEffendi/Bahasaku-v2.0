from flask import Blueprint, jsonify, request
from app.models.user_model import User
from app.extensions import db
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_ 
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, verify_jwt_in_request
from flask import current_app, url_for
import os
from werkzeug.utils import secure_filename
from app.models.user_model import ROLES
import datetime

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

user_bp = Blueprint('user_bp', __name__)

def is_admin(user_id):
    """Mengecek apakah user dengan user_id yang diberikan memiliki role 'Admin'."""
    user = User.query.get(user_id)
    return user and user.role == 'Admin'

# ==================== Register ================ ====
@user_bp.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()

    current_user_id = None
    is_registering_admin = False
    
    # Cek ada token Authorization di header kaga
    if request.headers.get('Authorization'):
        try:
            verify_jwt_in_request() 
            current_user_id = int(get_jwt_identity())
            is_registering_admin = is_admin(current_user_id)
        except Exception as e:
            print(f"Token check failed: {e}") 
            pass

    try:
        birth_date_str = data.get('birth_date')
        birth_date_obj = None

        if birth_date_str:
            try:
                birth_date_obj = datetime.datetime.strptime(birth_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        new_user = User(
            full_name=data.get('full_name'),
            email=data.get('email'),
            user_type=data.get('user_type'),
            location=data.get('location'),
            phone_number=data.get('phone_number'), 
            birth_date=birth_date_obj
        )

        if is_registering_admin and 'role' in data and data.get('role') in ROLES:
            new_user.role = data.get('role') 
        else:
            new_user.role = 'User' 

        if not all([new_user.full_name, new_user.email, data.get('password'), new_user.user_type]):
            return jsonify({"error": "Data tidak lengkap (nama, email, password, user_type wajib diisi)"}), 400

        if User.query.filter_by(email=new_user.email).first():
            return jsonify({"error": "Email sudah terdaftar"}), 409
            
        if new_user.phone_number and User.query.filter_by(phone_number=new_user.phone_number).first():
            return jsonify({"error": "Nomor telepon sudah terdaftar"}), 409

        new_user.set_password(data.get('password'))
        db.session.add(new_user)
        db.session.commit()

        access_token = create_access_token(identity=str(new_user.id))
        return jsonify({
            "message": "Registrasi berhasil",
            "access_token": access_token,
            "user": new_user.to_profile_dict()
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Email atau Nomor Telepon sudah terdaftar"}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Error Register: {str(e)}")
        return jsonify({"error": "Terjadi kesalahan server saat registrasi."}), 500

# ==================== Login ====================
@user_bp.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    # Variabel 'email' di ini bisa berisi Email ATAU No Telp (sesuai inputan user)
    identifier = data.get('email') 
    password = data.get('password')
    remember_me = data.get('remember_me', False)

    if not identifier or not password:
        return jsonify({"error": "Email/No.HP dan password wajib diisi"}), 400

    # Cari Email ATAU Nomor Telepon User
    user = User.query.filter(
        or_(User.email == identifier, User.phone_number == identifier)
    ).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Email/No.HP atau password salah"}), 401

    expires_delta = None
    if remember_me: 
        expires_delta = datetime.timedelta(days=1)

    access_token = create_access_token(
        identity=str(user.id),
        expires_delta=expires_delta
    )
    
    return jsonify({
        "message": "Login berhasil",
        "access_token": access_token,
        "user": user.to_profile_dict()
    }), 200

# ==================== Ambil semua data user ====================
@user_bp.route('/', methods=['GET'])
@jwt_required()
def get_users():
    try:
        current_user_id = int(get_jwt_identity())
    except Exception:
        return jsonify({"error": "Invalid token identity."}), 401
    if not is_admin(current_user_id):
        return jsonify({"error": "Akses ditolak. Diperlukan hak Admin."}), 403
    
    users = User.query.all()
    return jsonify([user.to_profile_dict() for user in users])

# ==================== Up foto profile user ====================
@user_bp.route('/<int:user_id>/photo', methods=['POST'])
@jwt_required()
def upload_profile_photo(user_id):
    try:
        current_user_id = int(get_jwt_identity())
    except Exception:
        return jsonify({"error": "Invalid token identity."}), 401

    if user_id != current_user_id:
        return jsonify({"error": "Akses ditolak. Anda hanya dapat mengupload foto untuk akun Anda sendiri."}), 403

    if 'photo' not in request.files: 
        return jsonify({"error": "File foto tidak ditemukan pada request."}), 400

    file = request.files['photo']

    if file.filename == '':
        return jsonify({"error": "Nama file kosong."}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Format file tidak didukung. Gunakan png/jpg/jpeg/gif."}), 400

    filename = secure_filename(f"{user_id}_{int(datetime.datetime.utcnow().timestamp())}_{file.filename}")
    save_dir = os.path.join(current_app.root_path, 'static', 'foto_profile')
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, filename)

    try:
        file.save(save_path)
    except Exception as e:
        return jsonify({"error": f"Gagal menyimpan file sementara: {str(e)}"}), 500

    relative_url = url_for('static', filename=f'foto_profile/{filename}')
    absolute_url = f"http://localhost:5000{relative_url}"

    user = User.query.get_or_404(user_id)
    old_url = user.profile_pic_url or ''
    old_filename = None
    if old_url and ('/foto_profile/' in old_url):
        old_filename = old_url.split('/foto_profile/')[-1]

    try:
        user.profile_pic_url = absolute_url
        db.session.commit()

        if old_filename:
            try:
                old_path = os.path.join(current_app.root_path, 'static', 'foto_profile', old_filename)
                save_dir_norm = os.path.normpath(os.path.join(current_app.root_path, 'static', 'foto_profile'))
                old_path_norm = os.path.normpath(old_path)
                if old_path_norm.startswith(save_dir_norm) and os.path.exists(old_path_norm) and old_path_norm != save_path:
                    os.remove(old_path_norm)
            except Exception:
                pass

        return jsonify({"message": "Foto profil berhasil diupload", "user": user.to_profile_dict()}), 200

    except Exception as e:
        try:
            if os.path.exists(save_path):
                os.remove(save_path)
        except Exception:
            pass
        db.session.rollback()
        return jsonify({"error": f"Gagal memperbarui database: {str(e)}"}), 500

# ==================== Ambil 1 user sesuai ID ====================
@user_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    try:
        current_user_id = int(get_jwt_identity())
    except Exception:
        return jsonify({"error": "Invalid token identity."}), 401

    user = User.query.get_or_404(user_id)
    print(f"[GET] User {user_id}, Current: {current_user_id}")

    if user.id != current_user_id and not is_admin(current_user_id):
        return jsonify({"error": "Akses ditolak. Anda tidak berhak melihat profil ini."}), 403

    profile = user.to_profile_dict()
    print(f"[GET] Returning profile: {profile}")
    return jsonify(profile)

# ==================== Update User ====================
@user_bp.route('/<int:user_id>', methods=['PUT', 'PATCH'])
@jwt_required()
def update_user(user_id):
    try:
        current_user_id = int(get_jwt_identity())
    except Exception:
        return jsonify({"error": "Invalid token identity."}), 401
    
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    try:
        current_user = User.query.get(int(current_user_id))
    except Exception:
        current_user = None

    is_current_admin = current_user and current_user.role == 'Admin'

    if user.id != current_user_id and not is_current_admin:
        return jsonify({"error": "Akses ditolak."}), 403

    try:
        user.full_name = data.get('full_name', user.full_name)
        user.location = data.get('location', user.location)

        if 'phone_number' in data:
            user.phone_number = data.get('phone_number')

        if 'birth_date' in data:
            birth_date_str = data.get('birth_date')
            if birth_date_str == "" or birth_date_str is None:
                user.birth_date = None
            else:
                user.birth_date = datetime.datetime.strptime(birth_date_str, '%Y-%m-%d').date()

        if 'user_type' in data and data.get('user_type'):
            user.user_type = data.get('user_type')

        if is_current_admin:
            if 'role' in data and data.get('role') in ROLES:
                user.role = data.get('role')

            if 'email' in data and data.get('email') and data.get('email') != user.email:
                if User.query.filter_by(email=data.get('email')).first(): 
                    return jsonify({"error": "Email sudah terdaftar"}), 409
                user.email = data.get('email')

            if 'password' in data and data.get('password'):
                user.set_password(data.get('password'))

        if (user.id == current_user_id) and ('password' in data) and data.get('password'):
            user.set_password(data.get('password'))

        db.session.commit()
        return jsonify({
            "message": "Profil berhasil diperbarui",
            "user": user.to_profile_dict()
        })
    
    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": f"Format tanggal salah: {str(e)}"}), 422

    except Exception as e:
        import traceback
        traceback.print_exc() 
        db.session.rollback()
        return jsonify({"error": f"Error: {str(e)}"}), 500

# ==================== Delete User ====================
@user_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    try:
        current_user_id = int(get_jwt_identity())
    except Exception:
        return jsonify({"error": "Invalid token identity."}), 401

    if not is_admin(current_user_id):
        return jsonify({"error": "Akses ditolak. Diperlukan hak Admin."}), 403
    
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user_id: 
        return jsonify({"error": "Admin tidak dapat menghapus akunnya sendiri melalui rute ini."}), 400

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"User dengan ID {user_id} berhasil dihapus."}), 200

# ==================== Ganti Password ====================
@user_bp.route('/<int:user_id>/change-password', methods=['PUT'])
@jwt_required()
def change_password(user_id):
    try:
        current_user_id = int(get_jwt_identity())
    except Exception:
        return jsonify({"error": "Invalid token identity."}), 401

    if user_id != current_user_id:
        return jsonify({"error": "Akses ditolak."}), 403

    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    if not old_password or not new_password:
        return jsonify({"error": "Password lama dan password baru wajib diisi."}), 400

    user = User.query.get_or_404(user_id)

    if not user.check_password(old_password):
        return jsonify({"error": "Password lama salah."}), 401

    user.set_password(new_password)
    db.session.commit()

    return jsonify({"message": "Password berhasil diubah."}), 200