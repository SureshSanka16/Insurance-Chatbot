"""
FAISS Vector Store
==================
High-performance vector store using FAISS and sentence-transformers.
Provides accurate semantic search for insurance policy documents.
"""

import json
import os
import logging
import pickle
from typing import Optional

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("faiss_vector_store")

# Storage paths
_STORE_DIR = os.path.join(os.path.dirname(__file__), "..", "faiss_data")
_INDEX_FILE = os.path.join(os.path.abspath(_STORE_DIR), "faiss.index")
_METADATA_FILE = os.path.join(os.path.abspath(_STORE_DIR), "metadata.json")
_MODEL_CACHE = os.path.join(os.path.abspath(_STORE_DIR), "model_cache")

# Global state
_index: faiss.Index | None = None
_metadata: list[dict] = []
_model: SentenceTransformer | None = None
_embedding_dim = 384  # all-MiniLM-L6-v2 dimension


def _ensure_dir():
    """Create storage directory if it doesn't exist."""
    os.makedirs(os.path.abspath(_STORE_DIR), exist_ok=True)
    os.makedirs(os.path.abspath(_MODEL_CACHE), exist_ok=True)


def _get_model() -> SentenceTransformer:
    """
    Load or initialize the sentence transformer model.
    Uses all-MiniLM-L6-v2: fast, lightweight, and accurate.
    """
    global _model
    if _model is not None:
        return _model

    logger.info("Loading sentence transformer model (all-MiniLM-L6-v2)...")
    _model = SentenceTransformer(
        'sentence-transformers/all-MiniLM-L6-v2',
        cache_folder=_MODEL_CACHE
    )
    logger.info("Model loaded successfully")
    return _model


def _load_index(force: bool = False):
    """Load FAISS index and metadata from disk (only once unless forced)."""
    global _index, _metadata

    # Skip if already loaded (unless forced)
    if not force and _index is not None and len(_metadata) > 0:
        return

    _ensure_dir()

    if os.path.exists(_INDEX_FILE) and os.path.exists(_METADATA_FILE):
        try:
            _index = faiss.read_index(_INDEX_FILE)
            with open(_METADATA_FILE, 'r', encoding='utf-8') as f:
                _metadata = json.load(f)
            logger.info(
                "Loaded FAISS index with %d vectors (dim=%d)",
                _index.ntotal, _embedding_dim
            )
            return
        except Exception as e:
            logger.warning("Failed to load FAISS index: %s. Creating new index.", e)
            _index = None
            _metadata = []

    if _index is None:
        # Create new index (Inner Product for cosine similarity with normalized vectors)
        _index = faiss.IndexFlatIP(_embedding_dim)
        _metadata = []
        logger.info("Created new FAISS index (dim=%d)", _embedding_dim)


def _save_index():
    """Persist FAISS index and metadata to disk."""
    _ensure_dir()
    faiss.write_index(_index, _INDEX_FILE)
    with open(_METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(_metadata, f)
    logger.info("Saved FAISS index with %d vectors", _index.ntotal)


def _normalize_vector(vec: np.ndarray) -> np.ndarray:
    """Normalize vector for cosine similarity."""
    norm = np.linalg.norm(vec)
    if norm > 0:
        return vec / norm
    return vec


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def upsert_chunks(
    ids: list[str],
    documents: list[str],
    metadatas: list[dict],
) -> int:
    """
    Add or update chunks in the FAISS vector store.

    Args:
        ids: Unique IDs for each chunk.
        documents: Text content of each chunk.
        metadatas: Metadata dicts for each chunk.

    Returns:
        Total number of chunks in the store.
    """
    global _index, _metadata

    _load_index()
    model = _get_model()

    # Build lookup of existing IDs
    existing_ids = {meta["id"]: idx for idx, meta in enumerate(_metadata)}

    # Separate new and update chunks
    new_ids = []
    new_docs = []
    new_metas = []

    for chunk_id, doc_text, meta in zip(ids, documents, metadatas):
        if chunk_id in existing_ids:
            # Update existing: remove old and add new
            idx = existing_ids[chunk_id]
            _metadata[idx] = {"id": chunk_id, "text": doc_text, "metadata": meta}
            # Note: FAISS doesn't support in-place updates, so we mark for rebuild
        else:
            new_ids.append(chunk_id)
            new_docs.append(doc_text)
            new_metas.append(meta)

    # Add new chunks
    if new_docs:
        logger.info("Encoding %d new documents...", len(new_docs))
        embeddings = model.encode(new_docs, show_progress_bar=False, convert_to_numpy=True)
        
        # Normalize for cosine similarity
        embeddings = np.array([_normalize_vector(emb) for emb in embeddings], dtype=np.float32)

        # Add to index
        _index.add(embeddings)

        # Add metadata
        for chunk_id, doc_text, meta in zip(new_ids, new_docs, new_metas):
            _metadata.append({
                "id": chunk_id,
                "text": doc_text,
                "metadata": meta,
            })

        _save_index()

    return len(_metadata)


def query(
    query_text: str,
    n_results: int = 5,
    where_filter: dict | None = None,
) -> list[dict]:
    """
    Query the FAISS vector store for similar chunks.

    Args:
        query_text: The search query.
        n_results: Number of results to return.
        where_filter: Optional metadata filter dict.
            Simple: {"user_id": "abc"}
            Compound: {"$and": [{"user_id": "abc"}, {"policy_number": "POL-1"}]}

    Returns:
        List of dicts with keys: id, text, metadata, distance.
    """
    global _index, _metadata

    _load_index()

    if _index.ntotal == 0:
        return []

    model = _get_model()

    # Encode query
    query_emb = model.encode([query_text], show_progress_bar=False, convert_to_numpy=True)[0]
    query_emb = _normalize_vector(query_emb).reshape(1, -1).astype(np.float32)

    # Search FAISS index
    # Get more results than needed for filtering
    k = min(_index.ntotal, n_results * 10)
    distances, indices = _index.search(query_emb, k)

    # Apply metadata filters
    filtered_results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:  # FAISS returns -1 for missing results
            continue

        chunk_data = _metadata[idx]
        
        # Apply filter
        if where_filter and not _matches_filter(chunk_data["metadata"], where_filter):
            continue

        # Convert distance (cosine similarity) to distance metric
        # FAISS IndexFlatIP returns dot product (cosine similarity for normalized vectors)
        # Convert to distance: distance = 1 - similarity
        similarity = float(dist)
        distance = 1.0 - similarity

        filtered_results.append({
            "id": chunk_data["id"],
            "text": chunk_data["text"],
            "metadata": chunk_data["metadata"],
            "distance": round(max(0.0, distance), 4),  # Ensure non-negative
        })

        if len(filtered_results) >= n_results:
            break

    return filtered_results


def count() -> int:
    """Return total number of chunks in the store."""
    _load_index()
    return len(_metadata)


def clear():
    """Clear all data from the vector store."""
    global _index, _metadata
    _index = faiss.IndexFlatIP(_embedding_dim)
    _metadata = []
    _save_index()
    logger.info("Cleared FAISS vector store")


def _matches_filter(metadata: dict, where_filter: dict) -> bool:
    """Check if metadata matches the filter criteria."""
    if not where_filter:
        return True

    # Handle $and compound filter
    if "$and" in where_filter:
        conditions = where_filter["$and"]
        return all(_matches_filter(metadata, cond) for cond in conditions)

    # Handle $or compound filter
    if "$or" in where_filter:
        conditions = where_filter["$or"]
        return any(_matches_filter(metadata, cond) for cond in conditions)

    # Simple key-value filter
    for key, value in where_filter.items():
        if str(metadata.get(key, "")) != str(value):
            return False

    return True
