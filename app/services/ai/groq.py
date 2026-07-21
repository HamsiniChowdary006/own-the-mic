import requests
from app.services.ai.provider import BaseAIProvider, AIProviderError

class GroqProvider(BaseAIProvider):
    """Groq AI provider implementation using OpenAI-compatible API."""

    def call_ai(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key:
            raise AIProviderError("Groq API key is not configured.")

        url = 'https://api.groq.com/openai/v1/chat/completions'
        # Default model matching original implementation
        model = 'llama-3.3-70b-versatile'
        
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.append({"role": "user", "content": prompt})
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        try:
            resp = requests.post(
                url, 
                json={
                    "model": model,
                    "messages": msgs,
                    "max_tokens": 1500,
                    "temperature": 0.8
                }, 
                headers=headers,
                timeout=15
            )
            
            if not resp.ok:
                raise AIProviderError(f"Groq API error: {resp.text}")
                
            data = resp.json()
            text = data.get('choices', [{}])[0].get('message', {}).get('content')
            if not text:
                raise AIProviderError("Empty response from Groq API.")
                
            return text.strip()
        except Exception as e:
            if isinstance(e, AIProviderError):
                raise
            raise AIProviderError(f"Exception during Groq API call: {str(e)}")
stream_with_context = False
