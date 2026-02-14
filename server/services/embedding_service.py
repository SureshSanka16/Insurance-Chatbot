"""
Embedding service using sentence-transformers.
Generates vector embeddings for text chunks.
"""
import logging
from typing import List, Union
import numpy as np
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

from core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Handles text embeddings using sentence-transformers."""
    
    def __init__(self):
        self.model = None
        self.model_name = settings.EMBEDDING_MODEL
        self.embedding_dim = settings.EMBEDDING_DIMENSION
        self.cache_dir = Path("./models/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_model(self):
        """Lazy load the embedding model."""
        if self.model is None:
            if not SentenceTransformer:
                raise ImportError(
                    "sentence-transformers not installed. "
                    "Run: pip install sentence-transformers"
                )
            
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(
                self.model_name,
                cache_folder=str(self.cache_dir)
            )
            logger.info("Embedding model loaded successfully")
    
    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for single text."""
        self._load_model()
        
        # Generate embedding
        embedding = self.model.encode([text], show_progress_bar=False)[0]
        
        # Normalize for cosine similarity
        embedding = embedding / np.linalg.norm(embedding)
        
        return embedding.astype(np.float32)
    
    def embed_batch(self, texts: List[str], batch_size: int = 8) -> List[np.ndarray]:
        """Generate embeddings for multiple texts."""
        self._load_model()
        
        logger.info(f"Generating embeddings for {len(texts)} texts")
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        # Normalize embeddings
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / norms
        
        return [emb.astype(np.float32) for emb in embeddings]
    
    def embed_chunks(self, chunks: List[dict]) -> List[dict]:
        """Add embeddings to chunk objects."""
        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.embed_batch(texts)
        
        # Add embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk["embedding"] = embedding
        
        return chunks
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Compute cosine similarity between two embeddings."""
        return float(np.dot(embedding1, embedding2))
    
    def get_model_info(self) -> dict:
        """Get embedding model information."""
        return {
            "model_name": self.model_name,
            "embedding_dimension": self.embedding_dim,
            "cache_dir": str(self.cache_dir)
        }

# Singleton instance
embedding_service = EmbeddingService()