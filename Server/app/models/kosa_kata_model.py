from app.extensions import db
from sqlalchemy.sql import func

# --- Konstanta untuk Kategori Kosa Kata (Opsional) ---
# Anda bisa menambahkan kategori spesifik di sini, misalnya:
# KOSA_KATA_CATEGORIES = ('Umum', 'Salam', 'Makanan', 'Emosi', 'Tempat')
# Jika Anda tidak menentukan kategori, defaultnya adalah 'Lainnya'.
KOSA_KATA_CATEGORIES = ('Lainnya',) # Biarkan satu tuple jika hanya ada default
# --------------------------------------------------


class KosaKata(db.Model):
    """Model untuk tabel kosa_kata.

    Kolom:
    - id: primary key
    - text: kata/frasa, harus unik
    - video_file_path: lokasi file video isyarat
    - category: kategori kosa kata
    - added_by_admin_id: foreign key ke user (Admin) yang menambahkan
    - created_at: timestamp
    """

    __tablename__ = 'kosa_kata'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    text = db.Column(db.String(50), unique=True, nullable=False)
    video_file_path = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50), nullable=False, default='Lainnya') # String lebih fleksibel daripada Enum di sini
    added_by_admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    # Relasi ke User yang menambahkan (opsional)
    added_by_admin = db.relationship('User', backref=db.backref('kosa_kata_added', lazy='dynamic'))

    def to_dict(self):
        """Konversi dasar ke dict."""
        return {
            'id': self.id,
            'text': self.text,
            'video_file_path': self.video_file_path,
            'category': self.category,
            'added_by_admin_id': self.added_by_admin_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def to_detail_dict(self):
        """Konversi detail, termasuk info admin."""
        data = self.to_dict()
        if self.added_by_admin:
            data['added_by_admin'] = {
                'id': self.added_by_admin.id,
                'full_name': self.added_by_admin.full_name,
                'email': self.added_by_admin.email,
            }
        return data

    def __repr__(self):
        return f"<KosaKata id={self.id} text={self.text} category={self.category}>"