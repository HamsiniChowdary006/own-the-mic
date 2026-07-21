import requests
from flask import current_app
from app.extensions import db
from app.models.user import User, UserSettings

def verify_google_token(id_token: str) -> dict:
    """
    Verify a Google ID token with Google's tokeninfo endpoint.
    Returns user details dictionary if valid, or None if invalid.
    """
    if not id_token:
        return None

    try:
        # Call Google's verification endpoint
        url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
        response = requests.get(url, timeout=5)
        if not response.ok:
            current_app.logger.error(f"Google token verification failed: {response.text}")
            return None

        payload = response.json()
        
        # Verify audience matches our Client ID
        client_id = current_app.config.get('GOOGLE_CLIENT_ID')
        if client_id and payload.get('aud') != client_id:
            current_app.logger.error(
                f"Google token audience mismatch. Expected: {client_id}, Got: {payload.get('aud')}"
            )
            return None

        # Return relevant profile fields
        return {
            'google_id': payload.get('sub'),
            'name': payload.get('name'),
            'email': payload.get('email'),
            'picture': payload.get('picture')
        }
    except Exception as e:
        current_app.logger.exception(f"Exception during Google token verification: {str(e)}")
        return None

def get_or_create_google_user(profile: dict) -> User:
    """
    Get an existing user by Google ID or Email, or create a new user.
    Handles linking Google OAuth to an existing email-based user account.
    """
    google_id = profile['google_id']
    email = profile['email']
    name = profile['name']
    picture = profile['picture']

    # 1. Search for existing user with this google_id
    user = User.query.filter_by(google_id=google_id).first()
    if user:
        # Update profile picture and name if they changed
        user.name = name
        user.profile_pic = picture
        db.session.commit()
        return user

    # 2. Search for existing user with this email
    user = User.query.filter_by(email=email).first()
    if user:
        # Link Google ID to existing user account
        user.google_id = google_id
        user.profile_pic = picture
        db.session.commit()
        return user

    # 3. Create a new user if no match found
    new_user = User(
        name=name,
        email=email,
        google_id=google_id,
        profile_pic=picture,
        is_pro=False # default to false
    )
    db.session.add(new_user)
    db.session.commit()

    # Create empty user settings
    settings = UserSettings(user_id=new_user.id)
    db.session.add(settings)
    db.session.commit()

    return new_user
