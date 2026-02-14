"""
Lightweight Vector Store
========================
A simple in-process vector store using numpy for cosine similarity search.
Replaces ChromaDB which is incompatible with Python 3.14.

Stores embeddings in a JSON file alongside the SQLite DB for persistence.
Uses OpenRouter-compatible embedding via a local sentence chunking approach,
or falls back to simple TF-IDF style matching.
"""

import json
import os
import logging
import hashlib
from typing import Optional

import numpy as np
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("vector_store")

# Persistent storage path
_STORE_DIR = os.path.join(os.path.dirname(__file__), "..", "vector_data")
_STORE_FILE = os.path.join(os.path.abspath(_STORE_DIR), "vectors.json")

# In-memory store
_store: dict | None = None


def _ensure_dir():
    os.makedirs(os.path.abspath(_STORE_DIR), exist_ok=True)


def _load_store() -> dict:
    """Load the vector store from disk, or create a new one."""
    global _store
    if _store is not None:
        return _store

    _ensure_dir()
    if os.path.exists(_STORE_FILE):
        try:
            with open(_STORE_FILE, "r", encoding="utf-8") as f:
                _store = json.load(f)
                logger.info("Loaded vector store with %d chunks", len(_store.get("chunks", [])))
        except Exception as e:
            logger.warning("Failed to load vector store: %s", e)
            _store = {"chunks": []}
    else:
        _store = {"chunks": []}

    return _store


def _save_store():
    """Persist the vector store to disk."""
    global _store
    if _store is None:
        return
    _ensure_dir()
    with open(_STORE_FILE, "w", encoding="utf-8") as f:
        json.dump(_store, f)
    logger.info("Saved vector store with %d chunks", len(_store.get("chunks", [])))


def _get_embedding(text: str) -> list[float]:
    """
    Get embedding for text using a local word-level hashing approach.
    Deterministic, fast, and works offline with no API dependencies.
    Uses word unigrams, bigrams, and character trigrams for robust matching.
    """
    return _local_embedding(text)


def _local_embedding(text: str, dim: int = 512) -> list[float]:
    """
    Local deterministic embedding using multi-level hashing:
    - Word unigrams (weighted 3x)
    - Word bigrams (weighted 2x)
    - Character trigrams (weighted 1x)

    This provides reasonable semantic matching for document retrieval.
    """
    import re
    text_lower = text.lower().strip()

    # Tokenize into words
    words = re.findall(r'[a-z0-9]+', text_lower)

    vec = np.zeros(dim, dtype=np.float32)

    # Word unigrams (strongest signal)
    for word in words:
        h = int(hashlib.md5(word.encode()).hexdigest(), 16)
        idx = h % dim
        vec[idx] += 3.0

    # Word bigrams
    for i in range(len(words) - 1):
        bigram = f"{words[i]}_{words[i+1]}"
        h = int(hashlib.md5(bigram.encode()).hexdigest(), 16)
        idx = h % dim
        vec[idx] += 2.0

    # Character trigrams (catches partial matches)
    for i in range(len(text_lower) - 2):
        trigram = text_lower[i:i+3]
        if trigram.strip():  # skip whitespace-only trigrams
            h = int(hashlib.md5(trigram.encode()).hexdigest(), 16)
            idx = h % dim
            vec[idx] += 1.0

    # Normalize to unit vector
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm

    return vec.tolist()


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a_np = np.array(a, dtype=np.float32)
    b_np = np.array(b, dtype=np.float32)
    dot = np.dot(a_np, b_np)
    norm_a = np.linalg.norm(a_np)
    norm_b = np.linalg.norm(b_np)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def upsert_chunks(
    ids: list[str],
    documents: list[str],
    metadatas: list[dict],
) -> int:
    """
    Add or update chunks in the vector store.

    Args:
        ids: Unique IDs for each chunk.
        documents: Text content of each chunk.
        metadatas: Metadata dicts for each chunk.

    Returns:
        Total number of chunks in the store.
    """
    store = _load_store()

    # Build lookup of existing IDs
    existing = {c["id"]: i for i, c in enumerate(store["chunks"])}

    for chunk_id, doc_text, meta in zip(ids, documents, metadatas):
        embedding = _get_embedding(doc_text)

        chunk_data = {
            "id": chunk_id,
            "text": doc_text,
            "metadata": meta,
            "embedding": embedding,
        }

        if chunk_id in existing:
            store["chunks"][existing[chunk_id]] = chunk_data
        else:
            store["chunks"].append(chunk_data)

    _save_store()
    return len(store["chunks"])


def query(
    query_text: str,
    n_results: int = 5,
    where_filter: dict | None = None,
) -> list[dict]:
    """
    Query the vector store for similar chunks.

    Args:
        query_text: The search query.
        n_results: Number of results to return.
        where_filter: Optional metadata filter dict.
            Simple: {"user_id": "abc"}
            Compound: {"$and": [{"user_id": "abc"}, {"policy_number": "POL-1"}]}

    Returns:
        List of dicts with keys: id, text, metadata, distance.
    """
    store = _load_store()
    chunks = store.get("chunks", [])

    if not chunks:
        return []

    # Apply metadata filters
    filtered = _apply_filter(chunks, where_filter)

    if not filtered:
        return []

    # Get query embedding
    query_emb = _get_embedding(query_text)

    # Compute similarities
    scored = []
    for chunk in filtered:
        sim = _cosine_similarity(query_emb, chunk["embedding"])
        scored.append((sim, chunk))

    # Sort by similarity (highest first)
    scored.sort(key=lambda x: x[0], reverse=True)

    # Return top n results
    results = []
    for sim, chunk in scored[:n_results]:
        results.append({
            "id": chunk["id"],
            "text": chunk["text"],
            "metadata": chunk["metadata"],
            "distance": round(1.0 - sim, 4),  # convert similarity to distance
        })

    return results


def count() -> int:
    """Return total number of chunks in the store."""
    store = _load_store()
    return len(store.get("chunks", []))


def _apply_filter(chunks: list[dict], where_filter: dict | None) -> list[dict]:
    """Apply metadata filters to chunks."""
    if not where_filter:
        return chunks

    # Handle $and compound filter
    if "$and" in where_filter:
        conditions = where_filter["$and"]
        result = chunks
        for cond in conditions:
            result = _apply_filter(result, cond)
        return result

    # Handle $or compound filter
    if "$or" in where_filter:
        conditions = where_filter["$or"]
        seen_ids = set()
        result = []
        for cond in conditions:
            for chunk in _apply_filter(chunks, cond):
                if chunk["id"] not in seen_ids:
                    seen_ids.add(chunk["id"])
                    result.append(chunk)
        return result

    # Simple key-value filter
    filtered = []
    for chunk in chunks:
        meta = chunk.get("metadata", {})
        match = True
        for key, value in where_filter.items():
            if str(meta.get(key, "")) != str(value):
                match = False
                break
        if match:
            filtered.append(chunk)

    return filtered
