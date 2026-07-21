from datetime import datetime
from app.extensions import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=True) # Nullable for OAuth users
    google_id = db.Column(db.String(256), unique=True, nullable=True)
    profile_pic = db.Column(db.String(500), nullable=True)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    college = db.Column(db.String(200))
    is_pro = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    settings = db.relationship('UserSettings', backref='user', uselist=False, cascade='all, delete-orphan')
    sessions = db.relationship('InterviewSession', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    resumes = db.relationship('ResumeMetadata', backref='user', lazy='dynamic', cascade='all, delete-orphan')

class UserSettings(db.Model):
    __tablename__ = 'user_settings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    gemini_key = db.Column(db.String(256))
    groq_key = db.Column(db.String(256))
    openrouter_key = db.Column(db.String(256))
    preferred_provider = db.Column(db.String(50), default='gemini')
