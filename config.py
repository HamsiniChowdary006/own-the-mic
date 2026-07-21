import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Essential Flask Configurations
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')

    # Database Configuration (Supabase PostgreSQL)
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Google OAuth Credentials
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')

    # AI Provider API Keys
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

    # Supabase Client & Storage Configurations
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_PUBLISHABLE_KEY = os.environ.get('SUPABASE_PUBLISHABLE_KEY')
    SUPABASE_SECRET_KEY = os.environ.get('SUPABASE_SECRET_KEY')

    # Local storage uploads folder (used temporarily or as cache if needed)
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB maximum upload limit

    @classmethod
    def validate(cls):
        """Validate presence of key environment variables."""
        # Critical security and database credentials required in all environments
        critical_vars = {
            'SECRET_KEY': cls.SECRET_KEY,
            'JWT_SECRET_KEY': cls.JWT_SECRET_KEY,
            'DATABASE_URL': cls.DATABASE_URL
        }
        missing_critical = [name for name, val in critical_vars.items() if not val]
        if missing_critical:
            raise RuntimeError(
                f"Missing critical environment variables: {', '.join(missing_critical)}. "
                "Ensure these are defined in your environment or .env file."
            )

        # Integration service credentials (warning/informational)
        integration_vars = {
            'GOOGLE_CLIENT_ID': cls.GOOGLE_CLIENT_ID,
            'GOOGLE_CLIENT_SECRET': cls.GOOGLE_CLIENT_SECRET,
            'GEMINI_API_KEY': cls.GEMINI_API_KEY,
            'GROQ_API_KEY': cls.GROQ_API_KEY,
            'SUPABASE_URL': cls.SUPABASE_URL,
            'SUPABASE_PUBLISHABLE_KEY': cls.SUPABASE_PUBLISHABLE_KEY,
            'SUPABASE_SECRET_KEY': cls.SUPABASE_SECRET_KEY
        }
        missing_integrations = [name for name, val in integration_vars.items() if not val]
        if missing_integrations:
            print(f"[*] WARNING: Missing integration credentials: {', '.join(missing_integrations)}")

class DevelopmentConfig(Config):
    DEBUG = True
    ENV = 'development'

class TestingConfig(Config):
    TESTING = True
    ENV = 'testing'
    # Use SQLite in-memory for testing to ensure isolation and speed
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_SECRET_KEY = 'test-jwt-secret-key-123'
    SECRET_KEY = 'test-secret-key-123'

    @classmethod
    def validate(cls):
        # Skip critical checks for testing environment
        pass

class ProductionConfig(Config):
    DEBUG = False
    ENV = 'production'

    @classmethod
    def validate(cls):
        # Run standard validation first
        super().validate()
        # In production, all integration services are strictly required
        required_production_vars = {
            'GOOGLE_CLIENT_ID': cls.GOOGLE_CLIENT_ID,
            'GOOGLE_CLIENT_SECRET': cls.GOOGLE_CLIENT_SECRET,
            'GEMINI_API_KEY': cls.GEMINI_API_KEY,
            'GROQ_API_KEY': cls.GROQ_API_KEY,
            'SUPABASE_URL': cls.SUPABASE_URL,
            'SUPABASE_PUBLISHABLE_KEY': cls.SUPABASE_PUBLISHABLE_KEY,
            'SUPABASE_SECRET_KEY': cls.SUPABASE_SECRET_KEY
        }
        missing_prod = [name for name, val in required_production_vars.items() if not val]
        if missing_prod:
            raise RuntimeError(
                f"Missing required production integrations: {', '.join(missing_prod)}. "
                "These are mandatory when running in Production Config mode."
            )

config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Auto-detect config class
def get_config():
    env = os.environ.get('FLASK_ENV', 'development').lower()
    return config_by_name.get(env, DevelopmentConfig)