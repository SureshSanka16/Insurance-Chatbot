"""
Document processing service for RAG pipeline.
Handles PDF extraction, text cleaning, and chunking.
"""
import logging
from typing import List, Dict, Any
from pathlib import Path
import hashlib
from datetime import datetime

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

from core.config import settings

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Handles document extraction and chunking for RAG."""
    
    def __init__(self):
        self.max_chunk_size = settings.MAX_CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
    
    async def extract_text_from_pdf(self, file_path: Path) -> str:
        """Extract text content from PDF file."""
        if not PyPDF2:
            raise ImportError("PyPDF2 not installed. Run: pip install PyPDF2")
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_parts = []
                
                for page in pdf_reader.pages:
                    text_parts.append(page.extract_text())
                
                return "\n".join(text_parts)
        except Exception as e:
            logger.error(f"Failed to extract text from {file_path}: {e}")
            raise
    
    def create_chunks(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split text into overlapping chunks with metadata."""
        # Simple chunking by sentences
        sentences = text.replace('.', '.\n').split('\n')
        chunks = []
        current_chunk = ""
        chunk_index = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Check if adding sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > self.max_chunk_size:
                if current_chunk:  # Save current chunk
                    chunk_id = self._generate_chunk_id(metadata, chunk_index)
                    chunks.append({
                        "id": chunk_id,
                        "text": current_chunk.strip(),
                        "metadata": {
                            **metadata,
                            "chunk_index": chunk_index,
                            "processed_at": datetime.utcnow().isoformat()
                        }
                    })
                    
                    # Start new chunk with overlap
                    overlap_text = self._get_overlap_text(current_chunk)
                    current_chunk = overlap_text + " " + sentence
                    chunk_index += 1
                else:
                    current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add final chunk
        if current_chunk.strip():
            chunk_id = self._generate_chunk_id(metadata, chunk_index)
            chunks.append({
                "id": chunk_id,
                "text": current_chunk.strip(),
                "metadata": {
                    **metadata,
                    "chunk_index": chunk_index,
                    "processed_at": datetime.utcnow().isoformat()
                }
            })
        
        logger.info(f"Created {len(chunks)} chunks from document")
        return chunks
    
    def _generate_chunk_id(self, metadata: Dict[str, Any], chunk_index: int) -> str:
        """Generate unique chunk ID."""
        doc_id = metadata.get("document_id", "unknown")
        return f"{doc_id}_chunk_{chunk_index:03d}"
    
    def _get_overlap_text(self, text: str) -> str:
        """Get overlap text for next chunk."""
        words = text.split()
        if len(words) <= self.chunk_overlap:
            return text
        return " ".join(words[-self.chunk_overlap:])
    
    async def process_document(self, 
                             file_path: Path,
                             document_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Main processing pipeline: extract + chunk."""
        logger.info(f"Processing document: {file_path}")
        
        # Extract text
        text = await self.extract_text_from_pdf(file_path)
        
        # Create chunks
        chunks = self.create_chunks(text, document_metadata)
        
        logger.info(f"Document processing complete: {len(chunks)} chunks")
        return chunks

# Singleton instance
document_processor = DocumentProcessor()