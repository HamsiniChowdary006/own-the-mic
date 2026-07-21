# OwnTheMic — AI Interview Coach

OwnTheMic is a web application that uses artificial intelligence to coach you on your interview skills. It transcribes your voice, scores your answers across multiple dimensions (Content, Structure, Clarity, Pace, Fillers, and Depth), and generates tailored feedback and model answers to help you improve.

## Features
- **Voice-powered practice**: Speak your answers out loud and get transcribed in real time.
- **6-dimension scoring**: Get detailed feedback on content, structure, clarity, modulation, filler words, and depth.
- **Adaptive AI questions**: The AI interviewer acts like a real person, asking follow-up questions when necessary.
- **Model answers**: Compare your answers with ideal STAR-format answers tailored to the role.
- **Progress tracking**: Save your past interview sessions and track your improvement over time.
- **Resume-aware questions**: Upload your resume to get highly relevant, personalized interview questions.

## Technology Stack
- **Frontend**: HTML, Vanilla JS, CSS (Jinja Templates)
- **Backend**: Python, Flask, Flask-SQLAlchemy, Flask-JWT-Extended
- **Database**: PostgreSQL (with local SQLite fallback for dev)
- **AI Providers**: Gemini, Groq (Llama 3), OpenRouter

## Local Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/kumudasrip/own-the-mic.git
   cd own-the-mic
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Rename `.env.example` to `.env` and fill in your secrets.
   ```env
   SECRET_KEY=your-secret-key
   JWT_SECRET_KEY=your-jwt-secret-key
   # DATABASE_URL=postgresql://postgres:password@localhost:5432/ownthemic
   ```
   *(If you leave `DATABASE_URL` commented out, the app will automatically use a local SQLite database `app.db` for easy development).*

5. **Initialize the Database**
   Run the database migrations to create the required tables:
   ```bash
   python -m flask db upgrade
   ```

6. **Run the Application**
   ```bash
   python run.py
   ```
   The application will be accessible at [http://127.0.0.1:5000](http://127.0.0.1:5000).

## AI Configuration
To unlock the core coaching features, you will need an API key from one of the supported AI providers (Gemini, Groq, or OpenRouter). You can add this API key through the application settings menu in the UI.

## Deployment
This app includes a `Procfile` and `wsgi.py` and is fully ready to be deployed to platforms like Heroku, Render, or any standard Linux VPS running Gunicorn. Ensure you set your `.env` variables (including `DATABASE_URL` for PostgreSQL) securely in your hosting provider's dashboard.
