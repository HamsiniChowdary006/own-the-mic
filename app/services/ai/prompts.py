def get_question_prompt(role: str, qtype: str, difficulty: str, prev_qs: list, resume_text: str) -> str:
    prev_str = f'\nDo NOT repeat: {", ".join(prev_qs)}' if prev_qs else ''
    resume_ctx = f'\nCandidate resume context:\n{resume_text[:800]}' if resume_text else ''
    
    qt_map = {
        'Behavioural (STAR)': 'behavioural STAR-format (Tell me about a time...)',
        'Situational': 'situational (What would you do if...)',
        'Technical': f'technical role-specific ({difficulty} difficulty)',
        'Self Introduction': 'self-introduction (Tell me about yourself)'
    }
    qtype_mapped = qt_map.get(qtype, qtype)
    
    return (
        f"You are an expert {role} interviewer. Generate ONE realistic {qtype_mapped} interview question for a {role} candidate."
        f"{resume_ctx}{prev_str}\nRespond ONLY with the question text. No preamble, no numbering."
    )

def get_should_followup_prompt(question: str, answer: str) -> str:
    return f'Interview question: "{question}"\nAnswer: "{answer}"\nIs this answer too short or vague for a real interview?\nReply ONLY "YES" or "NO".'

def get_followup_prompt(question: str, answer: str, role: str) -> str:
    return f'You are interviewing a {role} candidate.\nOriginal Q: "{question}"\nAnswer: "{answer}"\nAsk ONE short probing follow-up. Just the question, no preamble.'

def get_score_system_prompt() -> str:
    return 'You are an expert interview coach. Respond ONLY with valid JSON.'

def get_score_user_prompt(role: str, qtype: str, qas: list) -> str:
    qa_str = '\n\n'.join([
        f"Q{i+1}: {x['question']}\nA{i+1}: {x.get('answer', '(skipped)')}" 
        for i, x in enumerate(qas)
    ])
    
    return f"""Score this {role} ({qtype}) interview session.

{qa_str}

Return ONLY this JSON structure:
{{"overallScore":<0-100>,"scoreLabel":"<Excellent|Good|Fair|Needs Work>","dimensions":{{"contentRelevance":{{"score":<0-100>}},"answerStructure":{{"score":<0-100>}},"voiceClarity":{{"score":<0-100>}},"voiceModulation":{{"score":<0-100>}},"fillerControl":{{"score":<0-100>}},"answerDepth":{{"score":<0-100>}}}},"strengths":"<2 sentences>","improvements":"<2 sentences>","fillerWords":["word"],"recommendation":"<1 specific tip>","questionFeedback":[{{"index":0,"score":<0-100>,"brief":"<1 sentence>","modelAnswer":"<ideal STAR answer 3-4 sentences>"}}]}}

Weights: contentRelevance=25%, answerStructure=20%, voiceClarity=15%, voiceModulation=15%, fillerControl=15%, answerDepth=10%. overallScore = weighted average."""
