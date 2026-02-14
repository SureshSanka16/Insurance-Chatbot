"""
LLM service for generating responses.
Interfaces with OpenRouter/OpenAI for text generation.
"""
import logging
from typing import Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """Service for LLM interactions."""
    
    def __init__(self):
        self.client: Optional[OpenAI] = None
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client."""
        if not settings.OPENROUTER_API_KEY:
            logger.warning("OPENROUTER_API_KEY not set. LLM features will be limited.")
            return
        
        if not OpenAI:
            logger.error("OpenAI library not installed. Run: pip install openai")
            return
        
        try:
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=settings.OPENROUTER_API_KEY,
            )
            logger.info(f"LLM service initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
    
    async def generate_answer(self, query: str, context: Optional[str] = None) -> str:
        """Generate an answer given query and optional context."""
        if not self.client:
            return "I apologize, but the AI service is currently unavailable. Please ensure the API key is configured."
        
        try:
            # Build prompt
            if context and context.strip():
                system_prompt = (
                    "You are a helpful AI assistant for an insurance company. "
                    "Answer questions based on the provided context from insurance documents. "
                    "Be accurate, helpful, and cite the source when possible. "
                    "If the context doesn't contain relevant information, say so clearly."
                )
                
                user_prompt = f"""Context from insurance documents:
{context}

Question: {query}

Please provide a helpful answer based on the context above."""
            else:
                system_prompt = (
                    "You are a helpful AI assistant for an insurance company. "
                    "Provide general guidance about insurance topics, but recommend "
                    "users check their specific policy documents for exact details."
                )
                user_prompt = query
            
            # Generate response
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            answer = completion.choices[0].message.content.strip()
            logger.info(f"Generated answer ({len(answer)} chars) for query")
            return answer
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return f"I apologize, but I encountered an error while processing your question. Please try again later."
    
    def get_model_info(self) -> dict:
        """Get LLM model information."""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "client_initialized": self.client is not None
        }

# Singleton instance
llm_service = LLMService()