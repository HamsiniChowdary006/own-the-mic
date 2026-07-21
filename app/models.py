from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    college = db.Column(db.String(200))
    is_pro = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    settings = db.relationship('UserSettings', backref='user', uselist=False, cascade='all, delete-orphan')
    sessions = db.relationship('InterviewSession', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    resumes = db.relationship('Resume', backref='user', lazy='dynamic', cascade='all, delete-orphan')

class UserSettings(db.Model):
    __tablename__ = 'user_settings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    gemini_key = db.Column(db.String(256))
    groq_key = db.Column(db.String(256))
    openrouter_key = db.Column(db.String(256))
    preferred_provider = db.Column(db.String(50), default='gemini')

class Resume(db.Model):
    __tablename__ = 'resumes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class InterviewSession(db.Model):
    __tablename__ = 'interview_sessions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    qtype = db.Column(db.String(100), nullable=False)
    num_questions = db.Column(db.Integer, default=3)
    timer_enabled = db.Column(db.Boolean, default=True)
    resume_id = db.Column(db.Integer, db.ForeignKey('resumes.id'), nullable=True)
    
    overall_score = db.Column(db.Integer)
    score_label = db.Column(db.String(50))
    strengths = db.Column(db.Text)
    improvements = db.Column(db.Text)
    recommendation = db.Column(db.Text)
    filler_words = db.Column(db.Text) # Stored as JSON string or comma separated
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    questions = db.relationship('Question', backref='session', lazy='dynamic', cascade='all, delete-orphan')
    feedbacks = db.relationship('Feedback', backref='session', lazy='dynamic', cascade='all, delete-orphan')

class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('interview_sessions.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    is_followup = db.Column(db.Boolean, default=False)
    order_index = db.Column(db.Integer, nullable=False)
    
    answer = db.relationship('Answer', backref='question', uselist=False, cascade='all, delete-orphan')

class Answer(db.Model):
    __tablename__ = 'answers'
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    answer_text = db.Column(db.Text)
    filler_count = db.Column(db.Integer, default=0)
    word_count = db.Column(db.Integer, default=0)
    
    score = db.Column(db.Integer)
    feedback_brief = db.Column(db.Text)
    model_answer = db.Column(db.Text)

class Feedback(db.Model):
    # Overall session feedback from the user to the app
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('interview_sessions.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    rating = db.Column(db.Integer)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
