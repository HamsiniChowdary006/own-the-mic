from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.user import User
from app.models.pilot_feedback import PilotFeedback
from app.services.ai import (
    generate_question as ai_generate_question,
    should_followup as ai_should_followup,
    generate_followup as ai_generate_followup,
    score_session as ai_score_session
)
from app.services.resume import ResumeService
from app.services.interview import InterviewService

api_bp = Blueprint('api', __name__, url_prefix='/api')

resume_service = ResumeService()
interview_service = InterviewService()

@api_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    data = request.get_json() or {}
    
    if 'name' in data:
        user.name = data['name']
    if 'email' in data:
        user.email = data['email']
    if 'college' in data:
        user.college = data['college']
    if 'age' in data:
        user.age = data['age']
        
    db.session.commit()
    return jsonify({"message": "Profile updated successfully"})

@api_bp.route('/ai/question', methods=['POST'])
@jwt_required(optional=True)
def get_ai_question():
    data = request.get_json() or {}
    role = data.get('role')
    qtype = data.get('qtype')
    difficulty = data.get('difficulty', 'Beginner')
    prev_qs = data.get('prevQs', [])
    resume_text = data.get('resumeText', '')
    
    # 1. Resolve preferred provider from user settings (if authenticated)
    provider = 'gemini'
    user_id = get_jwt_identity()
    if user_id:
        user = User.query.get(user_id)
        if user and user.settings and user.settings.preferred_provider:
            provider = user.settings.preferred_provider
            
    # 2. Key is resolved inside execute_with_fallback, but check for manual pass-in override
    manual_key = data.get('key')
    manual_provider = data.get('provider')
    
    try:
        q = ai_generate_question(
            role=role,
            qtype=qtype,
            difficulty=difficulty,
            prev_qs=prev_qs,
            resume_text=resume_text,
            provider=manual_provider or provider,
            key=manual_key
        )
        return jsonify({"question": q})
    except Exception as e:
        current_app.logger.exception(f"Error generating question: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/ai/followup', methods=['POST'])
@jwt_required(optional=True)
def check_followup():
    data = request.get_json() or {}
    q = data.get('question')
    a = data.get('answer')
    role = data.get('role')
    
    provider = 'gemini'
    user_id = get_jwt_identity()
    if user_id:
        user = User.query.get(user_id)
        if user and user.settings and user.settings.preferred_provider:
            provider = user.settings.preferred_provider
            
    manual_key = data.get('key')
    manual_provider = data.get('provider')
    
    try:
        needed = ai_should_followup(
            question=q,
            answer=a,
            provider=manual_provider or provider,
            key=manual_key
        )
        if needed:
            fq = ai_generate_followup(
                question=q,
                answer=a,
                role=role,
                provider=manual_provider or provider,
                key=manual_key
            )
            return jsonify({"followup": fq})
        return jsonify({"followup": None})
    except Exception as e:
        current_app.logger.exception(f"Error checking and generating followup: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/ai/score', methods=['POST'])
@jwt_required(optional=True)
def get_ai_score():
    data = request.get_json() or {}
    role = data.get('role')
    qtype = data.get('qtype')
    qas = data.get('qas', [])
    
    provider = 'gemini'
    user_id = get_jwt_identity()
    if user_id:
        user = User.query.get(user_id)
        if user and user.settings and user.settings.preferred_provider:
            provider = user.settings.preferred_provider
            
    manual_key = data.get('key')
    manual_provider = data.get('provider')
    
    try:
        result = ai_score_session(
            role=role,
            qtype=qtype,
            qas=qas,
            provider=manual_provider or provider,
            key=manual_key
        )
        return jsonify(result)
    except Exception as e:
        current_app.logger.exception(f"Error scoring session: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/resume/upload', methods=['POST'])
@jwt_required()
def upload_resume_file():
    user_id = get_jwt_identity()
    
    if 'resume' not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files['resume']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Only PDF resumes are supported"}), 400
        
    try:
        # Load file stream in memory as raw bytes
        file_bytes = file.read()
        resume_record = resume_service.upload_resume(
            user_id=user_id,
            filename=file.filename,
            file_data=file_bytes,
            content_type=file.content_type
        )
        return jsonify({
            "message": "Resume uploaded successfully",
            "filename": resume_record.filename,
            "url": resume_record.file_path
        })
    except Exception as e:
        current_app.logger.exception(f"Error in upload_resume: {str(e)}")
        return jsonify({"error": f"Failed to upload resume: {str(e)}"}), 500

@api_bp.route('/session/save', methods=['POST'])
@jwt_required()
def save_session_details():
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    
    try:
        session = interview_service.save_interview_session(user_id, data)
        return jsonify({
            "message": "Session saved successfully",
            "session_id": session.id
        })
    except Exception as e:
        current_app.logger.exception(f"Error in save_session: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/session/history', methods=['GET'])
@jwt_required()
def get_session_history():
    user_id = get_jwt_identity()
    try:
        history = interview_service.get_user_session_history(user_id)
        return jsonify({"sessions": history})
    except Exception as e:
        current_app.logger.exception(f"Error fetching session history: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/feedback/pilot', methods=['POST'])
@jwt_required()
def submit_pilot_feedback():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Prevent duplicate submissions
    existing = PilotFeedback.query.filter_by(user_id=user.id).first()
    if existing:
        return jsonify({"error": "You have already submitted pilot feedback. Thank you!"}), 400

    data = request.get_json() or {}
    
    # Extract and validate parameters
    challenge = data.get('challenge')
    ai_feedback_helpful = data.get('ai_feedback_helpful')
    most_valuable_feedback = data.get('most_valuable_feedback')
    would_use_again = data.get('would_use_again')
    pro_interest = data.get('pro_interest')
    
    if not challenge or not ai_feedback_helpful or not most_valuable_feedback or not would_use_again or not pro_interest:
        return jsonify({"error": "Missing required feedback fields"}), 400
        
    confusing_inaccurate_unnecessary = data.get('confusing_inaccurate_unnecessary', '')
    desired_improvement = data.get('desired_improvement', '')
    pro_price_interest = data.get('pro_price_interest', '')
    
    # Create record
    feedback_record = PilotFeedback(
        user_id=user.id,
        email=user.email,
        challenge=challenge,
        ai_feedback_helpful=ai_feedback_helpful,
        most_valuable_feedback=most_valuable_feedback,
        confusing_inaccurate_unnecessary=confusing_inaccurate_unnecessary,
        would_use_again=would_use_again,
        desired_improvement=desired_improvement,
        pro_interest=pro_interest,
        pro_price_interest=pro_price_interest
    )
    
    db.session.add(feedback_record)
    db.session.commit()
    
    return jsonify({"message": "Feedback submitted successfully!", "id": feedback_record.id}), 201

@api_bp.route('/feedback/pilot/status', methods=['GET'])
@jwt_required()
def get_pilot_feedback_status():
    user_id = get_jwt_identity()
    existing = PilotFeedback.query.filter_by(user_id=user_id).first()
    return jsonify({"submitted": existing is not None})

