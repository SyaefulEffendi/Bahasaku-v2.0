from app.extensions import db
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

USER_TYPES = ('Tuli', 'Dengar', 'Umum')
ROLES = ('User', 'Admin')

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    
    password_hash = db.Column(db.String(255), nullable=False)
    
    user_type = db.Column(db.Enum(*USER_TYPES, name='user_type_enum'), nullable=False)
    
    location = db.Column(db.String(255), nullable=True)

    phone_number = db.Column(db.String(20), nullable=True)
    
    birth_date = db.Column(db.Date, nullable=True)
    
    profile_pic_url = db.Column(db.String(255), default='default.png')
    
    role = db.Column(db.Enum(*ROLES, name='role_enum'), nullable=False, default='User')
    
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    # ========= Fungsi Keamanan =========

    def set_password(self, password_mentah):
        """Membuat hash password yang aman."""
        self.password_hash = generate_password_hash(password_mentah, method='pbkdf2:sha256')

    def check_password(self, password_mentah):
        """Memeriksa apakah password mentah cocok dengan hash."""
        return check_password_hash(self.password_hash, password_mentah)

    # ========= Fungsi Utilitas =========

    def to_profile_dict(self):
        """Mengonversi objek User menjadi dictionary untuk profil lengkap."""
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "user_type": self.user_type,
            "location": self.location,
            "phone_number": self.phone_number,
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "profile_pic_url": self.profile_pic_url,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        """Representasi string untuk debugging."""
        return f'<User id={self.id} email={self.email}>'