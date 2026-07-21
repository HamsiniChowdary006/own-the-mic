from datetime import datetime
from app.extensions import db

class ResumeMetadata(db.Model):
    __tablename__ = 'resume_metadata'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False) # Stores Supabase Storage URL or path
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
