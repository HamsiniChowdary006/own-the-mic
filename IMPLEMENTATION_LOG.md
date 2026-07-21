# Implementation Log: OwnTheMic Backend Modernization

This log documents the architecture, database migrations, setup instructions, and production checklist for the **OwnTheMic** modernized backend.

---

## 🏗️ Architectural Decisions

### 1. Separation of Concerns (Service-Based Refactor)
- **Routes / Controllers**: Blueprints in `app/routes/` and `app/auth/` are now lightweight wrapper handlers. They only parse inputs, perform basic verification, and forward parameters to business logic.
- **Services**: All business logic (AI interactions, PDF/storage uploads, interview flows, and profile management) lives inside `app/services/` and `app/auth/services.py`.
- **Database Models**: Reorganized from a single file to the `app/models/` package, exposing schemas via `app/models/__init__.py`.

### 2. Multi-Provider Fallback Strategy
- Gemini acts as the default provider.
- Groq works as the alternative.
- Calls to providers are wrapped in a fallback execution loop. If one service fails (network timeout, rate limit, quota issue), the app catches the exception and attempts execution with the next fallback provider.

### 3. Google OAuth Single-Sign-On (SSO)
- Integrated Google Identity Services HTML & JavaScript elements onto signin/signup layouts.
- Verified tokens securely on the backend via standard endpoints using the `requests` library.
- Enabled automatic user registration on first login, linking to existing email-based user entries when appropriate.

---

## 🗃️ Database Migration Notes

Existing migrations are fully preserved. A new migration version (`a3297a7e37e9_modernize_schema.py`) has been added to update the schema:
1. Replaces the local `resumes` table with `resume_metadata`.
2. Adds `google_id` (unique/nullable) and `profile_pic` to `users`.
3. Sets `password_hash` to nullable to accommodate OAuth entries.
4. Adds `ai_provider` to `interview_sessions`.
5. Creates the new `scores` table to persist dimension-specific scores.

To run migrations:
```bash
python -m flask db upgrade
```

---

## 📁 Project Tree

```
own-the-mic/
│
├── app/
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── services.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── feedback.py
│   │   ├── resume.py
│   │   ├── score.py
│   │   ├── session.py
│   │   └── user.py
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── api.py
│   │   └── main.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   ├── ai_service.py
│   │   │   ├── gemini.py
│   │   │   ├── groq.py
│   │   │   ├── prompts.py
│   │   │   └── provider.py
│   │   │
│   │   ├── interview/
│   │   │   ├── __init__.py
│   │   │   └── interview_service.py
│   │   │
│   │   ├── resume/
│   │   │   ├── __init__.py
│   │   │   └── resume_service.py
│   │   │
│   │   └── storage/
│   │       ├── __init__.py
│   │       └── supabase_storage.py
│   │
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── main.js
│   │
│   ├── templates/
│   │   ├── auth/
│   │   │   ├── signin.html
│   │   │   └── signup.html
│   │   ├── dashboard/
│   │   │   └── index.html
│   │   ├── base.html
│   │   └── index.html
│   │
│   ├── __init__.py
│   ├── ee_questions.json
│   └── extensions.py
│
├── migrations/
│   └── versions/
│       ├── 710958432794_initial_migration.py
│       └── a3297a7e37e9_modernize_schema.py
│
├── tests/
│   └── test_modernization.py
│
├── .env.example
├── config.py
├── run.py
└── requirements.txt
```

---

## 🛠️ Environment Setup Instructions

1. **Clone & Virtualenv Setup**:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```
2. **Install Packages**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Environment Setup**:
   Create a `.env` file in the root based on `.env.example`:
   ```env
   # Authentication Secrets
   SECRET_KEY=your-flask-secret-key
   JWT_SECRET_KEY=your-jwt-secret-key

   # Supabase Database
   DATABASE_URL=postgresql://<user>:<password>@<db-host>:5432/postgres

   # Google Client Credentials
   GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-google-client-secret

   # AI Provider Keys
   GEMINI_API_KEY=your-gemini-api-key
   GROQ_API_KEY=your-groq-api-key

   # Supabase Cloud Storage
   SUPABASE_URL=https://your-supabase-project.supabase.co
   SUPABASE_PUBLISHABLE_KEY=your-supabase-publishable-key
   SUPABASE_SECRET_KEY=your-supabase-secret-key
   ```
4. **Upgrade Database Schema**:
   ```bash
   python -m flask db upgrade
   ```
5. **Run Server**:
   ```bash
   python run.py
   ```

---

## 🚀 Production Readiness Checklist

- [x] **Database Connectivity**: Suppressed SQLite fallbacks in production. Database runs on Supabase PostgreSQL.
- [x] **Secure Credentials**: All integration credentials, database links, and secret signatures are loaded from the environment. No secrets are hardcoded.
- [x] **Environment Validation**: Critical keys are validated immediately on startup (fails fast with `RuntimeError` if missing in production).
- [x] **Strict Content Security Policy**: Configured `Talisman` to allow Google SSO endpoints, styling sheets, fonts, and user avatars securely.
- [x] **Graceful Fallbacks**: AI Question generator and Evaluator fallback safely to secondary models if default provider fails.
- [x] **Secured Assets**: User resumes are stored securely inside private directories on Supabase Storage (`user_<id>/*`).
- [x] **Unit Testing**: Automated test suite passed successfully.
