from datetime import datetime
from app.extensions import db
from app.models.session import InterviewSession, Question, Answer
from app.models.score import Score
from app.models.resume import ResumeMetadata

class InterviewService:
    """Service to manage interview session history, question structures, and scores."""

    def save_interview_session(self, user_id: int, data: dict) -> InterviewSession:
        """
        Saves a completed interview session, its QA history, and multi-dimensional scores.
        """
        # Resolve any associated resume metadata ID
        resume = ResumeMetadata.query.filter_by(user_id=user_id).first()
        resume_id = resume.id if resume else None

        # 1. Create the session
        session = InterviewSession(
            user_id=user_id,
            role=data.get('role'),
            qtype=data.get('qtype'),
            overall_score=data.get('overallScore'),
            score_label=data.get('scoreLabel'),
            strengths=data.get('strengths'),
            improvements=data.get('improvements'),
            recommendation=data.get('recommendation'),
            resume_id=resume_id,
            ai_provider=data.get('aiProvider') or 'gemini',
            created_at=datetime.utcnow()
        )
        
        db.session.add(session)
        db.session.flush() # Yield session ID for relationships

        # 2. Add 6-dimension scores if present
        dims = data.get('dimensions', {})
        score_details = Score(
            session_id=session.id,
            content_relevance=dims.get('contentRelevance', {}).get('score', 0),
            answer_structure=dims.get('answerStructure', {}).get('score', 0),
            voice_clarity=dims.get('voiceClarity', {}).get('score', 0),
            voice_modulation=dims.get('voiceModulation', {}).get('score', 0),
            filler_control=dims.get('fillerControl', {}).get('score', 0),
            answer_depth=dims.get('answerDepth', {}).get('score', 0)
        )
        db.session.add(score_details)

        # 3. Add Questions and Answers
        qas = data.get('qas', [])
        q_feedbacks = data.get('questionFeedback', [])
        
        for i, qa in enumerate(qas):
            # Parse if the question is follow up based on structure
            is_followup = qa.get('is_followup', False)
            
            q = Question(
                session_id=session.id,
                question_text=qa.get('question'),
                is_followup=is_followup,
                order_index=i,
                created_at=datetime.utcnow()
            )
            db.session.add(q)
            db.session.flush()
            
            # Match feedback from list
            fb = next((f for f in q_feedbacks if f.get('index') == i), {})
            
            # Count words
            ans_text = qa.get('answer', '')
            word_count = len(ans_text.split()) if ans_text else 0
            
            # Simple local filler word count estimate if not already supplied
            filler_count = qa.get('fillerCount', 0)
            
            a = Answer(
                question_id=q.id,
                answer_text=ans_text,
                filler_count=filler_count,
                word_count=word_count,
                score=fb.get('score'),
                feedback_brief=fb.get('brief'),
                model_answer=fb.get('modelAnswer'),
                created_at=datetime.utcnow()
            )
            db.session.add(a)
            
        db.session.commit()
        return session

    def get_user_session_history(self, user_id: int) -> list:
        """
        Retrieves all interview sessions completed by a user, ordered by creation date descending.
        """
        sessions = InterviewSession.query.filter_by(user_id=user_id)\
                                        .order_by(InterviewSession.created_at.desc())\
                                        .all()
        return [
            {
                "id": s.id,
                "role": s.role,
                "qtype": s.qtype,
                "overallScore": s.overall_score,
                "scoreLabel": s.score_label,
                "date": s.created_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "aiProvider": s.ai_provider
            }
            for s in sessions
        ]
