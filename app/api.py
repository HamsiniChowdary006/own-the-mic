from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import bcrypt
import os
from werkzeug.utils import secure_filename
from app.models import db, User, UserSettings, Resume, InterviewSession, Question, Answer
from app.ai_service import generate_question, should_followup, generate_followup, score_session
from flask import current_app
from datetime import datetime

api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if User.query.filter_by(email=data.get('email')).first():
        return jsonify({"error": "Email already exists"}), 400
        
    password = data.get('password').encode('utf-8')
    hashed = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')
    
    new_user = User(
        name=data.get('name'),
        email=data.get('email'),
        password_hash=hashed,
        age=data.get('age'),
        gender=data.get('gender'),
        college=data.get('college')
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    # Initialize empty settings
    settings = UserSettings(user_id=new_user.id)
    db.session.add(settings)
    db.session.commit()
    
    access_token = create_access_token(identity=str(new_user.id))
    
    return jsonify({
        "message": "User created successfully",
        "access_token": access_token,
        "user": {
            "uid": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "isPro": new_user.is_pro
        }
    }), 201

@api.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()
    
    if not user or not bcrypt.checkpw(data.get('password').encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({"error": "Invalid email or password"}), 401
        
    access_token = create_access_token(identity=str(user.id))
    
    return jsonify({
        "access_token": access_token,
        "user": {
            "uid": user.id,
            "name": user.name,
            "email": user.email,
            "isPro": user.is_pro,
            "college": user.college,
            "age": user.age
        }
    }), 200

@api.route('/auth/me', methods=['GET'])
@jwt_required()
def get_me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    return jsonify({
        "user": {
            "uid": user.id,
            "name": user.name,
            "email": user.email,
            "isPro": user.is_pro,
            "college": user.college,
            "age": user.age
        }
    }), 200

@api.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json()
    
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

@api.route('/ai/question', methods=['POST'])
@jwt_required(optional=True)
def api_generate_question():
    data = request.get_json()
    role = data.get('role')
    qtype = data.get('qtype')
    difficulty = data.get('difficulty', 'Beginner')
    prev_qs = data.get('prevQs', [])
    resume_text = data.get('resumeText', '')
    
    # In a real app, you would fetch user settings for provider and key
    # For now, we expect them in the request body (as currently passed from JS)
    provider = data.get('provider', 'gemini')
    key = data.get('key')
    
    try:
        q = generate_question(role, qtype, difficulty, prev_qs, resume_text, provider, key)
        return jsonify({"question": q})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/ai/followup', methods=['POST'])
@jwt_required(optional=True)
def api_followup():
    data = request.get_json()
    q = data.get('question')
    a = data.get('answer')
    role = data.get('role')
    provider = data.get('provider', 'gemini')
    key = data.get('key')
    
    try:
        needed = should_followup(q, a, provider, key)
        if needed:
            fq = generate_followup(q, a, role, provider, key)
            return jsonify({"followup": fq})
        return jsonify({"followup": None})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/ai/score', methods=['POST'])
@jwt_required(optional=True)
def api_score():
    data = request.get_json()
    role = data.get('role')
    qtype = data.get('qtype')
    qas = data.get('qas', [])
    provider = data.get('provider', 'gemini')
    key = data.get('key')
    
    try:
        result = score_session(role, qtype, qas, provider, key)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/resume/upload', methods=['POST'])
@jwt_required()
def upload_resume():
    user_id = get_jwt_identity()
    
    if 'resume' not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files['resume']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if file:
        filename = secure_filename(file.filename)
        # Create a user-specific folder or unique filename
        unique_filename = f"{user_id}_{filename}"
        
        upload_path = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        os.makedirs(upload_path, exist_ok=True)
        
        file_path = os.path.join(upload_path, unique_filename)
        file.save(file_path)
        
        # Delete old resume if any, or just add new
        resume = Resume.query.filter_by(user_id=user_id).first()
        if not resume:
            resume = Resume(user_id=user_id, filename=filename, file_path=file_path)
            db.session.add(resume)
        else:
            resume.filename = filename
            resume.file_path = file_path
            
        db.session.commit()
        return jsonify({"message": "Resume uploaded successfully", "filename": filename})

@api.route('/session/save', methods=['POST'])
@jwt_required()
def save_session():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    session = InterviewSession(
        user_id=user_id,
        role=data.get('role'),
        qtype=data.get('qtype'),
        overall_score=data.get('overallScore'),
        score_label=data.get('scoreLabel'),
        strengths=data.get('strengths'),
        improvements=data.get('improvements'),
        recommendation=data.get('recommendation'),
        created_at=datetime.utcnow()
    )
    db.session.add(session)
    db.session.flush() # get session ID
    
    qas = data.get('qas', [])
    q_feedbacks = data.get('questionFeedback', [])
    
    for i, qa in enumerate(qas):
        q = Question(
            session_id=session.id,
            question_text=qa.get('question'),
            is_followup=False,
            order_index=i
        )
        db.session.add(q)
        db.session.flush()
        
        # Match feedback by index
        fb = next((f for f in q_feedbacks if f.get('index') == i), {})
        
        a = Answer(
            question_id=q.id,
            answer_text=qa.get('answer'),
            word_count=len(qa.get('answer', '').split()),
            score=fb.get('score'),
            feedback_brief=fb.get('brief'),
            model_answer=fb.get('modelAnswer')
        )
        db.session.add(a)
        
    db.session.commit()
    return jsonify({"message": "Session saved successfully", "session_id": session.id})

@api.route('/session/history', methods=['GET'])
@jwt_required()
def get_history():
    user_id = get_jwt_identity()
    sessions = InterviewSession.query.filter_by(user_id=user_id).order_by(InterviewSession.created_at.desc()).all()
    
    res = []
    for s in sessions:
        res.append({
            "id": s.id,
            "role": s.role,
            "qtype": s.qtype,
            "overallScore": s.overall_score,
            "scoreLabel": s.score_label,
            "date": s.created_at.strftime('%Y-%m-%dT%H:%M:%SZ')
        })
        
    return jsonify({"sessions": res})

