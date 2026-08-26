from datetime import datetime
from app.extensions import db

class PilotFeedback(db.Model):
    __tablename__ = 'pilot_feedback'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    
    # Question 1: What challenge were you hoping OwnTheMic would help you with?
    challenge = db.Column(db.Text, nullable=False)
    
    # Question 2: Did the AI feedback help you improve your response?
    ai_feedback_helpful = db.Column(db.String(50), nullable=False)
    
    # Question 3: Which part of the feedback was most valuable?
    most_valuable_feedback = db.Column(db.Text, nullable=False)
    
    # Question 4: Was anything confusing, inaccurate, or unnecessary?
    confusing_inaccurate_unnecessary = db.Column(db.Text, nullable=True)
    
    # Question 5: Would you use OwnTheMic again before your next interview?
    would_use_again = db.Column(db.String(50), nullable=False)
    
    # Question 6: What's the one feature or improvement that would make OwnTheMic even more valuable to you?
    desired_improvement = db.Column(db.Text, nullable=True)
    
    # Question 7: If OwnTheMic offered a Pro version with advanced interview practice and personalised feedback, would you consider paying for it?
    pro_interest = db.Column(db.String(50), nullable=False)
    
    # Question 7 Followup: Would you consider a fair monthly price of ₹99–129?
    pro_price_interest = db.Column(db.String(50), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('pilot_feedbacks', lazy='dynamic'))
