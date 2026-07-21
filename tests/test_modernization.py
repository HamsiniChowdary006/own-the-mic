import unittest
from unittest.mock import patch, MagicMock
from flask import current_app
from config import TestingConfig, get_config
from app import create_app
from app.extensions import db
from app.models.user import User, UserSettings
from app.services.ai.ai_service import get_provider_client, execute_with_fallback
from app.services.ai.provider import AIProviderError

class ConfigTestCase(unittest.TestCase):
    def test_testing_config(self):
        config = TestingConfig()
        self.assertTrue(config.TESTING)
        self.assertEqual(config.SQLALCHEMY_DATABASE_URI, 'sqlite:///:memory:')

class AppInitializationTestCase(unittest.TestCase):
    def setUp(self):
        # Disable config validation for testing or use TestingConfig directly
        self.app = create_app(TestingConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_app_exists(self):
        self.assertFalse(current_app is None)

    def test_blueprints_registered(self):
        blueprints = list(self.app.blueprints.keys())
        self.assertIn('main', blueprints)
        self.assertIn('api', blueprints)
        self.assertIn('auth', blueprints)

class AuthServicesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestingConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('requests.get')
    def test_verify_google_token_success(self, mock_get):
        from app.auth.services import verify_google_token
        
        # Configure testing credentials
        self.app.config['GOOGLE_CLIENT_ID'] = 'test-client-id'
        
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'sub': '123456789',
            'name': 'Test User',
            'email': 'test@example.com',
            'picture': 'https://example.com/avatar.jpg',
            'aud': 'test-client-id'
        }
        mock_get.return_value = mock_response

        profile = verify_google_token('valid-token')
        self.assertIsNotNone(profile)
        self.assertEqual(profile['google_id'], '123456789')
        self.assertEqual(profile['email'], 'test@example.com')

    def test_get_or_create_google_user(self):
        from app.auth.services import get_or_create_google_user
        profile = {
            'google_id': '123456789',
            'name': 'Test User',
            'email': 'test@example.com',
            'picture': 'https://example.com/avatar.jpg'
        }
        
        # Verify user is created
        user = get_or_create_google_user(profile)
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.google_id, '123456789')
        self.assertIsNotNone(user.settings)
        
        # Fetching again should return the same user
        user_repeat = get_or_create_google_user(profile)
        self.assertEqual(user.id, user_repeat.id)

class AIServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestingConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    @patch('app.services.ai.gemini.GeminiProvider.call_ai')
    def test_fallback_chain_success_first(self, mock_gemini_call):
        mock_gemini_call.return_value = "Gemini Response"
        self.app.config['GEMINI_API_KEY'] = 'gemini-key'
        self.app.config['GROQ_API_KEY'] = 'groq-key'
        
        result, provider = execute_with_fallback("Hello", preferred_provider='gemini')
        self.assertEqual(result, "Gemini Response")
        self.assertEqual(provider, "gemini")
        mock_gemini_call.assert_called_once()

    @patch('app.services.ai.groq.GroqProvider.call_ai')
    @patch('app.services.ai.gemini.GeminiProvider.call_ai')
    def test_fallback_chain_failure_fallback(self, mock_gemini_call, mock_groq_call):
        # Gemini fails, should fall back to Groq
        mock_gemini_call.side_effect = AIProviderError("Gemini Quota Exceeded")
        mock_groq_call.return_value = "Groq Response"
        
        self.app.config['GEMINI_API_KEY'] = 'gemini-key'
        self.app.config['GROQ_API_KEY'] = 'groq-key'
        
        result, provider = execute_with_fallback("Hello", preferred_provider='gemini')
        self.assertEqual(result, "Groq Response")
        self.assertEqual(provider, "groq")

if __name__ == '__main__':
    unittest.main()
