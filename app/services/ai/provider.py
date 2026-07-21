class AIProviderError(Exception):
    """Exception raised when an AI provider call fails."""
    pass

class BaseAIProvider:
    """Base interface for all AI model providers."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key

    def call_ai(self, prompt: str, system_prompt: str = "") -> str:
        """
        Execute a prompt against the AI model provider.
        
        Args:
            prompt: The user query or task prompt.
            system_prompt: Optional instructions directing the model's behavior.
            
        Returns:
            The generated response string.
            
        Raises:
            AIProviderError: If the call encounters an error.
        """
        raise NotImplementedError
