import re

EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

def is_valid_email(email: str) -> bool:
    """Checks if the email string matches the RFC-compliant format."""
    if not email:
        return False
    return bool(re.match(EMAIL_REGEX, email))

def sanitize_input(text: str) -> str:
    """Sanitizes text inputs from leading/trailing whitespaces and tags."""
    if not text:
        return ""
    # Strip HTML tags
    clean = re.sub(r'<[^>]*>', '', text)
    return clean.strip()
