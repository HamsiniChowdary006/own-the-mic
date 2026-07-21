import requests
import json
from flask import current_app

def call_ai(prompt, provider='gemini', key=None, system_prompt=''):
    if not key:
        raise ValueError('No API key configured for provider.')
        
    if provider == 'gemini':
        return _call_gemini(prompt, key, system_prompt)
    elif provider == 'groq':
        return _call_openai_compat(prompt, 'https://api.groq.com/openai/v1/chat/completions', 'llama-3.3-70b-versatile', key, system_prompt)
    elif provider == 'openrouter':
        return _call_openai_compat(prompt, 'https://openrouter.ai/api/v1/chat/completions', 'meta-llama/llama-3.3-70b-instruct:free', key, system_prompt, ref='https://ownthemic.app')
    else:
        raise ValueError(f'Unknown provider: {provider}')

def _call_gemini(prompt, key, sys_prompt):
    models = ['gemini-1.5-flash', 'gemini-1.5-flash-latest', 'gemini-1.0-pro']
    last_err = ''
    
    for model in models:
        try:
            url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}'
            body = {
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.8, "maxOutputTokens": 1500}
            }
            if sys_prompt:
                body["systemInstruction"] = {"parts": [{"text": sys_prompt}]}
                
            resp = requests.post(url, json=body, headers={'Content-Type': 'application/json'})
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
            
    raise Exception(f'All Gemini models failed. Last error: {last_err}')

def _call_openai_compat(prompt, url, model, key, sys_prompt, ref=''):
    msgs = []
    if sys_prompt:
        msgs.append({"role": "system", "content": sys_prompt})
    msgs.append({"role": "user", "content": prompt})
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {key}'
    }
    if ref:
        headers['HTTP-Referer'] = ref
        
    resp = requests.post(url, json={
        "model": model,
        "messages": msgs,
        "max_tokens": 1500,
        "temperature": 0.8
    }, headers=headers)
    
    if not resp.ok:
        raise Exception(f'API error: {resp.text}')
        
    data = resp.json()
    text = data.get('choices', [{}])[0].get('message', {}).get('content')
    if not text:
        raise Exception('Empty API response')
        
    return text.strip()

def generate_question(role, qtype, difficulty='Beginner', prev_qs=None, resume_text='', provider='gemini', key=None):
    prev_qs = prev_qs or []
    
    if role == 'Electrical Engineering':
        try:
            import os
            import random
            bank_path = os.path.join(current_app.root_path, 'ee_questions.json')
            if os.path.exists(bank_path):
                with open(bank_path, 'r') as f:
                    ee_bank = json.load(f)
                
                bank_qs = {q['question'] for q in ee_bank}
                asked_bank_count = sum(1 for q in prev_qs if q in bank_qs)
                
                # Prioritize picking from the bank if we haven't hit our quota of 2
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
                        return random.choice(candidates)['question']
        except Exception:
            pass # fallback to AI
            
    prev_str = f'\nDo NOT repeat: {", ".join(prev_qs)}' if prev_qs else ''
    resume_ctx = f'\nCandidate resume context:\n{resume_text[:800]}' if resume_text else ''
    
    qt_map = {
        'Behavioural (STAR)': 'behavioural STAR-format (Tell me about a time...)',
        'Situational': 'situational (What would you do if...)',
        'Technical': f'technical role-specific ({difficulty} difficulty)',
        'Self Introduction': 'self-introduction (Tell me about yourself)'
    }
    qtype_mapped = qt_map.get(qtype, qtype)
    
    prompt = f'You are an expert {role} interviewer. Generate ONE realistic {qtype_mapped} interview question for a {role} candidate.{resume_ctx}{prev_str}\nRespond ONLY with the question text. No preamble, no numbering.'
    
    return call_ai(prompt, provider=provider, key=key)

def should_followup(question, answer, provider='gemini', key=None):
    if len(answer.split()) < 25:
        return True
    
    prompt = f'Interview question: "{question}"\nAnswer: "{answer}"\nIs this answer too short or vague for a real interview?\nReply ONLY "YES" or "NO".'
    
    try:
        res = call_ai(prompt, provider=provider, key=key)
        return res.strip().upper().startswith('Y')
    except:
        return False

def generate_followup(question, answer, role, provider='gemini', key=None):
    prompt = f'You are interviewing a {role} candidate.\nOriginal Q: "{question}"\nAnswer: "{answer}"\nAsk ONE short probing follow-up. Just the question, no preamble.'
    return call_ai(prompt, provider=provider, key=key)

def score_session(role, qtype, qas, provider='gemini', key=None):
    qa_str = '\n\n'.join([f"Q{i+1}: {x['question']}\nA{i+1}: {x.get('answer', '(skipped)')}" for i, x in enumerate(qas)])
    sys_prompt = 'You are an expert interview coach. Respond ONLY with valid JSON.'
    
    prompt = f"""Score this {role} ({qtype}) interview session.

{qa_str}

Return ONLY this JSON structure:
{{"overallScore":<0-100>,"scoreLabel":"<Excellent|Good|Fair|Needs Work>","dimensions":{{"contentRelevance":{{"score":<0-100>}},"answerStructure":{{"score":<0-100>}},"voiceClarity":{{"score":<0-100>}},"voiceModulation":{{"score":<0-100>}},"fillerControl":{{"score":<0-100>}},"answerDepth":{{"score":<0-100>}}}},"strengths":"<2 sentences>","improvements":"<2 sentences>","fillerWords":["word"],"recommendation":"<1 specific tip>","questionFeedback":[{{"index":0,"score":<0-100>,"brief":"<1 sentence>","modelAnswer":"<ideal STAR answer 3-4 sentences>"}}]}}

Weights: contentRelevance=25%, answerStructure=20%, voiceClarity=15%, voiceModulation=15%, fillerControl=15%, answerDepth=10%. overallScore = weighted average."""
    
    raw = call_ai(prompt, provider=provider, key=key, system_prompt=sys_prompt)
    import re
    match = re.search(r'\{[\s\S]*\}', raw)
    if not match:
        raise ValueError('Invalid JSON from AI')
        
    return json.loads(match.group(0))
