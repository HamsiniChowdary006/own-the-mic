from flask import Blueprint, render_template, current_app

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    google_client_id = current_app.config.get('GOOGLE_CLIENT_ID', '')
    return render_template('index.html', google_client_id=google_client_id)

@main_bp.route('/feedback')
def feedback():
    google_client_id = current_app.config.get('GOOGLE_CLIENT_ID', '')
    return render_template('index.html', google_client_id=google_client_id)

