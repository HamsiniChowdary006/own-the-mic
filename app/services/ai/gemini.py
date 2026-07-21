import requests
from app.services.ai.provider import BaseAIProvider, AIProviderError

class GeminiProvider(BaseAIProvider):
    """Google Gemini AI provider implementation."""

    def call_ai(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key:
            raise AIProviderError("Gemini API key is not configured.")

        # Try models in order of capability/preference
        models = ['gemini-1.5-flash', 'gemini-1.5-flash-latest', 'gemini-1.0-pro']
        last_err = ''
        
        for model in models:
            try:
                url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}'
                body = {
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.8, "maxOutputTokens": 1500}
                }
                if system_prompt:
                    body["systemInstruction"] = {"parts": [{"text": system_prompt}]}
                    
                resp = requests.post(
                    url, 
                    json=body, 
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                if not resp.ok:
                    last_err = resp.text
                    continue
                    
                data = resp.json()
                text = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text')
                if not text:
                    last_err = 'Empty response'
                    continue
                    
                return text.strip()
            except Exception as e:
                last_err = str(e)
                continue
                
        raise AIProviderError(f"All Gemini models failed. Last error: {last_err}")
