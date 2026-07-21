import os
import json
import random
import re
from flask import current_app
from app.services.ai.prompts import (
    get_question_prompt,
    get_should_followup_prompt,
    get_followup_prompt,
    get_score_system_prompt,
    get_score_user_prompt
)
from app.services.ai.gemini import GeminiProvider
from app.services.ai.groq import GroqProvider
from app.services.ai.provider import AIProviderError

def get_provider_client(provider_name: str, key: str = None):
    """
    Get the instance of the requested AI provider.
    If no key is provided, attempts to load it from the current app config.
    """
    provider_name = provider_name.lower()
    if provider_name == 'gemini':
        api_key = key or current_app.config.get('GEMINI_API_KEY')
        return GeminiProvider(api_key=api_key)
    elif provider_name == 'groq':
        api_key = key or current_app.config.get('GROQ_API_KEY')
        return GroqProvider(api_key=api_key)
    else:
        raise ValueError(f"Unknown AI provider: {provider_name}")

def execute_with_fallback(prompt: str, system_prompt: str = "", preferred_provider: str = 'gemini', key: str = None) -> tuple:
    """
    Executes an AI prompt with a primary provider and falls back to the alternative if it fails.
    Returns a tuple of (result_text, provider_used).
    """
    providers_queue = ['gemini', 'groq']
    
    # Reorder queue if the preferred provider is different and has a key
    if preferred_provider in providers_queue:
        providers_queue.remove(preferred_provider)
        providers_queue.insert(0, preferred_provider)
        
    last_error = None
    
    for provider_name in providers_queue:
        # Use the explicitly passed key only for the first try of the preferred provider
        current_key = key if provider_name == preferred_provider else None
        
        try:
            client = get_provider_client(provider_name, key=current_key)
            # Only proceed if we have a key configured (either passed in or in env)
            if not client.api_key:
                current_app.logger.warning(f"Skipping provider {provider_name} due to missing API key.")
                continue
                
            current_app.logger.info(f"Attempting call to {provider_name}...")
            result = client.call_ai(prompt, system_prompt)
            current_app.logger.info(f"Successfully called {provider_name}.")
            return result, provider_name
        except Exception as e:
            last_error = str(e)
            current_app.logger.warning(f"Provider {provider_name} failed: {last_error}")
            continue
            
    raise Exception(f"All AI Providers failed. Last error: {last_error}")

def generate_question(role: str, qtype: str, difficulty: str = 'Beginner', prev_qs: list = None, resume_text: str = '', provider: str = 'gemini', key: str = None) -> str:
    """
    Generates a new interview question based on the role, type, and resume.
    Includes fallback to local EE question bank for Electrical Engineering role.
    """
    prev_qs = prev_qs or []
    
    # 1. Local Question Bank Fallback for Electrical Engineering
    if role == 'Electrical Engineering':
        try:
            # Look up ee_questions.json in the app package directory
            bank_path = os.path.join(current_app.root_path, 'ee_questions.json')
            if os.path.exists(bank_path):
                with open(bank_path, 'r') as f:
                    ee_bank = json.load(f)
                
                bank_qs = {q['question'] for q in ee_bank}
                asked_bank_count = sum(1 for q in prev_qs if q in bank_qs)
                
                # Pick from bank if quota (2 questions) not met or 30% chance
                if asked_bank_count < 2 or random.random() < 0.3:
                    if qtype == 'Mixed':
                        candidates = ee_bank
                    elif qtype.startswith('Behavioural'):
                        candidates = [q for q in ee_bank if q.get('type', '').startswith('Behavioural')]
                    else:
                        candidates = [q for q in ee_bank if q.get('type') == qtype]
                    
                    candidates = [q for q in candidates if q.get('difficulty') in [difficulty, 'Any']]
                    candidates = [q for q in candidates if q['question'] not in prev_qs]
                    
                    if candidates:
                        picked_q = random.choice(candidates)['question']
                        current_app.logger.info(f"Picked question from local EE bank: {picked_q}")
                        return picked_q
        except Exception as e:
            current_app.logger.warning(f"Error loading EE local question bank: {str(e)}. Falling back to AI.")
            
    # 2. AI Question Generation
    prompt = get_question_prompt(role, qtype, difficulty, prev_qs, resume_text)
    response, _ = execute_with_fallback(prompt, preferred_provider=provider, key=key)
    return response

def should_followup(question: str, answer: str, provider: str = 'gemini', key: str = None) -> bool:
    """
    Decides whether a followup question is needed based on the answer length and depth.
    """
    if len(answer.split()) < 25:
        return True
        
    prompt = get_should_followup_prompt(question, answer)
    try:
        response, _ = execute_with_fallback(prompt, preferred_provider=provider, key=key)
        return response.strip().upper().startswith('Y')
    except Exception as e:
        current_app.logger.warning(f"should_followup check failed: {str(e)}. Defaulting to False.")
        return False

def generate_followup(question: str, answer: str, role: str, provider: str = 'gemini', key: str = None) -> str:
    """
    Generates a probing followup question.
    """
    prompt = get_followup_prompt(question, answer, role)
    response, _ = execute_with_fallback(prompt, preferred_provider=provider, key=key)
    return response

def score_session(role: str, qtype: str, qas: list, provider: str = 'gemini', key: str = None) -> dict:
    """
    Evaluates the entire interview session, returns structured scores and feedback in JSON.
    """
    system_prompt = get_score_system_prompt()
    prompt = get_score_user_prompt(role, qtype, qas)
    
    response, provider_used = execute_with_fallback(
        prompt, 
        system_prompt=system_prompt, 
        preferred_provider=provider, 
        key=key
    )
    
    match = re.search(r'\{[\s\S]*\}', response)
    if not match:
        raise ValueError("Invalid JSON output received from AI provider")
        
    result = json.loads(match.group(0))
    # Tag response with which provider ended up being used
    result['aiProvider'] = provider_used
    return result
