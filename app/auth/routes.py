from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import bcrypt
from app.extensions import db
from app.models.user import User, UserSettings
from app.auth.services import verify_google_token, get_or_create_google_user

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    
    email = data.get('email')
    if not email:
        return jsonify({"error": "Email is required"}), 400
        
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 400
        
    password = data.get('password')
    if not password or len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
        
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    new_user = User(
        name=data.get('name'),
        email=email,
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

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
        
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.password_hash or not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
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
            "age": user.age,
            "profilePic": user.profile_pic
        }
    }), 200

@auth_bp.route('/me', methods=['GET'])
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
            "age": user.age,
            "profilePic": user.profile_pic
        }
    }), 200

@auth_bp.route('/google', methods=['POST'])
def google_auth():
    """
    Endpoint called by the client after receiving Google Credential (JWT token).
    Verifies the token and registers/logs in the user.
    """
    data = request.get_json() or {}
    id_token = data.get('id_token')
    
    if not id_token:
        return jsonify({"error": "id_token is required"}), 400
        
    # Verify the Google Token
    profile = verify_google_token(id_token)
    if not profile:
        return jsonify({"error": "Invalid Google token"}), 401
        
    # Retrieve or create user matching Google profile
    user = get_or_create_google_user(profile)
    
    # Issue app-specific JWT
    access_token = create_access_token(identity=str(user.id))
    
    return jsonify({
        "access_token": access_token,
        "user": {
            "uid": user.id,
            "name": user.name,
            "email": user.email,
            "isPro": user.is_pro,
            "college": user.college,
            "age": user.age,
            "profilePic": user.profile_pic
        }
    }), 200
