from app.extensions import db
from sqlalchemy.sql import func
import datetime

# --- Konstanta untuk Status Feedback ---
FEEDBACK_STATUS = ('Baru', 'Ditinjau', 'Selesai')
# ------------------------------------


class Feedback(db.Model):
    """Model untuk menyimpan feedback dari user.

    Kolom:
    - id: primary key
    - user_id: foreign key ke users.id
    - message: isi feedback
    - status: ENUM('Baru','Ditinjau','Selesai')
    - created_at: timestamp default CURRENT_TIMESTAMP
    """

    __tablename__ = "feedback"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Menggunakan konstanta FEEDBACK_STATUS
    status = db.Column(db.Enum(*FEEDBACK_STATUS, name='feedback_status_enum'), nullable=False, default='Baru')
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    # Relasi ke model User (opsional, berguna untuk query join)
    user = db.relationship('User', backref=db.backref('feedbacks', lazy='dynamic'))

    def to_dict(self):
        """Konversi ke dict untuk dikembalikan lewat API."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'message': self.message,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def to_profile_dict(self):
        """Versi lebih lengkap termasuk info singkat user (jika relasi tersedia)."""
        data = self.to_dict()
        
        # NOTE: Agar relasi ini berfungsi, Anda perlu memastikan model 'User' 
        # (yang dirujuk oleh db.relationship('User', ...)) sudah diimpor 
        # di suatu tempat yang dapat diakses oleh SQLAlchemy.
        # Dalam struktur Flask yang baik, ini biasanya otomatis.
        if self.user:
            data['user'] = {
                'id': self.user.id,
                'full_name': self.user.full_name,
                'email': self.user.email,
            }
        return data

    def __repr__(self):
        return f'<Feedback id={self.id} user_id={self.user_id} status={self.status}>'