import requests
from app.services.ai.provider import BaseAIProvider, AIProviderError

class GroqProvider(BaseAIProvider):
    """Groq AI provider implementation using OpenAI-compatible API."""

    def call_ai(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key:
            raise AIProviderError("Groq API key is not configured.")

        url = 'https://api.groq.com/openai/v1/chat/completions'
        # Try models in order of capability/preference
        models = [
            'llama-3.3-70b-versatile',
            'groq/compound-mini',
            'groq/compound',
            'llama-3.1-70b-versatile',
            'llama3-70b-8192'
        ]
        
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.append({"role": "user", "content": prompt})
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        last_err = ''
        for model in models:
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
                    last_err = f"Model {model} failed: {resp.text}"
                    continue
                    
                data = resp.json()
                text = data.get('choices', [{}])[0].get('message', {}).get('content')
                if not text:
                    last_err = f"Model {model} returned empty response"
                    continue
                    
                return text.strip()
            except Exception as e:
                last_err = f"Model {model} exception: {str(e)}"
                continue
                
        raise AIProviderError(f"All Groq models failed. Last error: {last_err}")
stream_with_context = False
