from datetime import datetime
from app.extensions import db

class Score(db.Model):
    __tablename__ = 'scores'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('interview_sessions.id'), nullable=False)
    
    # 6 dimensions of scoring
    content_relevance = db.Column(db.Integer, nullable=False, default=0)
    answer_structure = db.Column(db.Integer, nullable=False, default=0)
    voice_clarity = db.Column(db.Integer, nullable=False, default=0)
    voice_modulation = db.Column(db.Integer, nullable=False, default=0)
    filler_control = db.Column(db.Integer, nullable=False, default=0)
    answer_depth = db.Column(db.Integer, nullable=False, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    session = db.relationship('InterviewSession', backref=db.backref('score_details', uselist=False, cascade='all, delete-orphan'))
