"""
Configuration settings for RAG system.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./vantage.db"
    
    # Vector Store
    VECTOR_STORE_PATH: Path = Path("./data/vectors")
    FAISS_INDEX_PATH: Path = VECTOR_STORE_PATH / "faiss.index"
    VECTOR_METADATA_PATH: Path = VECTOR_STORE_PATH / "metadata.json"
    
    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    MAX_CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    
    # LLM
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    LLM_MODEL: str = "google/gemini-2.0-flash-001"
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 1024
    
    # RAG
    MAX_CONTEXT_CHUNKS: int = 5
    MIN_SIMILARITY_SCORE: float = 0.7
    
    # Security
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key")
    
    class Config:
        env_file = ".env"

settings = Settings()