from app.extensions import db
from sqlalchemy.sql import func
from app.models.user_model import User

class Information(db.Model):
    __tablename__ = 'information'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    # --- Relasi Pembuat ---
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='infos_created')
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_by = db.relationship('User', foreign_keys=[updated_by_id], backref='infos_updated')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'image_url': self.image_url,
            'created_at': self.created_at.strftime('%d-%m-%Y %H:%M') if self.created_at else '-',
            'created_by': self.created_by.full_name if self.created_by else 'Admin',
            
            # Data Edit Baru
            'updated_at': self.updated_at.strftime('%d-%m-%Y %H:%M') if self.updated_at else '-',
            'updated_by': self.updated_by.full_name if self.updated_by else '-'
        }