"""
Knowledge Bridge Service
========================
Ingests documents from the database into ChromaDB using OpenRouter AI for
intelligent section extraction and Gemini embeddings for vectorization.

Pipeline:
  1. Fetch document binary (PDF) from DB
  2. Extract raw text via PyPDF2
  3. Use OpenRouter AI to discover logical sections dynamically
  4. Vectorize each section into ChromaDB with dynamic metadata from the Document model
"""

import io
import json
import os
import logging
import textwrap
from datetime import datetime
from typing import Any

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("knowledge_bridge")


# ---------------------------------------------------------------------------
# 1.  Dynamic Metadata Introspection
# ---------------------------------------------------------------------------

def _get_document_foreign_keys() -> list[str]:
    """
    Dynamically inspect the Document SQLAlchemy model and return all column
    names that are ForeignKey references or useful identifiers.
    This makes the service resilient to schema renames (e.g. policy_id -> policy_number).
    """
    from models import Document as DocumentModel
    from sqlalchemy import inspect as sa_inspect

    mapper = sa_inspect(DocumentModel)
    fk_columns: list[str] = []

    for col in mapper.columns:
        # Include every column that has a ForeignKey constraint
        if col.foreign_keys:
            fk_columns.append(col.key)
        # Also include common identifier patterns even if not FK
        elif col.key in ("user_email", "name", "category", "claim_id"):
            fk_columns.append(col.key)

    return list(set(fk_columns))  # deduplicate


def _build_metadata(document: Any) -> dict[str, str]:
    """
    Build a metadata dictionary from a Document ORM instance, dynamically
    reading every foreign key + identifier column found via introspection.
    ChromaDB metadata values must be str | int | float | bool.
    """
    meta: dict[str, str] = {}
    for col_name in _get_document_foreign_keys():
        value = getattr(document, col_name, None)
        if value is not None:
            meta[col_name] = str(value)

    # Always include the original filename as "source"
    meta["source"] = getattr(document, "name", "unknown")
    meta["document_id"] = str(document.id)
    meta["ingested_at"] = datetime.utcnow().isoformat()

    return meta


# ---------------------------------------------------------------------------
# 2.  PDF Text Extraction
# ---------------------------------------------------------------------------

def _extract_text_from_pdf(file_data: bytes) -> str:
    """Extract plain text from a PDF stored as binary bytes."""
    from PyPDF2 import PdfReader

    reader = PdfReader(io.BytesIO(file_data))
    pages: list[str] = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages.append(f"--- Page {i + 1} ---\n{text}")

    full_text = "\n\n".join(pages)
    if not full_text.strip():
        raise ValueError("PDF contains no extractable text (may be scanned/image-only).")

    return full_text


# ---------------------------------------------------------------------------
# 3.  OpenRouter AI - Dynamic Section Discovery
# ---------------------------------------------------------------------------

def _extract_sections(document_text: str) -> list[dict]:
    """
    Use OpenRouter AI to dynamically discover logical sections in the document.
    We do NOT hardcode a schema; instead we instruct the model to identify
    section boundaries and their semantic roles.

    Returns a list of dicts:
        [{ "extraction_class": "...", "text": "...", "attributes": {...} }, ...]
    """
    from openai import OpenAI

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not set - cannot extract sections.")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    # Truncate very long documents to avoid token limits
    max_chars = 30000
    truncated = document_text[:max_chars]
    if len(document_text) > max_chars:
        truncated += "\n\n[... document truncated for processing ...]"

    system_prompt = textwrap.dedent("""\
        You are a document analysis AI that identifies logical sections in
        insurance documents. You output ONLY valid JSON arrays, no markdown.

        For each section you find, output an object with:
        - "extraction_class": the semantic role (e.g. "header", "clause",
          "coverage_details", "exclusion", "table", "declaration",
          "terms_and_conditions", "contact_info", "summary", "paragraph",
          "signature", "definitions", "schedule", "endorsement", etc.)
        - "text": the verbatim text of the section
        - "attributes": meaningful key-value pairs (section_number, topic,
          monetary_values, dates, etc.)

        Example output:
        [
          {
            "extraction_class": "coverage_details",
            "text": "SECTION 1 - COVERAGE\\nThis policy covers...",
            "attributes": {"section_number": "1", "topic": "coverage"}
          }
        ]""")

    user_prompt = (
        "Identify all logical sections in this insurance document. "
        "Return a JSON array of section objects.\n\n"
        f"Document:\n{truncated}"
    )

    try:
        completion = client.chat.completions.create(
            model="google/gemini-2.0-flash-001",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=4096,
        )

        response_text = completion.choices[0].message.content.strip()

        # Clean markdown fences if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        sections_raw = json.loads(response_text)

        # Normalize into our expected format
        sections: list[dict] = []
        for item in sections_raw:
            sections.append({
                "extraction_class": item.get("extraction_class", "paragraph"),
                "text": item.get("text", ""),
                "attributes": item.get("attributes", {}),
            })

        if sections:
            return sections

    except Exception as e:
        logger.warning("OpenRouter section extraction failed: %s", e)

    # Fallback: treat entire document as one chunk
    logger.warning("Section extraction returned 0 sections - using full text as single chunk.")
    return [{
        "extraction_class": "full_document",
        "text": document_text,
        "attributes": {},
    }]


# ---------------------------------------------------------------------------
# 4.  Vectorization (lightweight vector store)
# ---------------------------------------------------------------------------

def _vectorize_sections(
    sections: list[dict],
    metadata_base: dict[str, str],
) -> dict:
    """
    Upsert extracted sections into the FAISS vector store.

    Each chunk gets:
      - id:        <document_id>_chunk_<index>
      - document:  the section text
      - metadata:  base metadata (FKs) + section-specific attributes
    """
    from services.faiss_vector_store import upsert_chunks, count

    doc_id = metadata_base.get("document_id", "unknown")

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []

    for idx, section in enumerate(sections):
        chunk_id = f"{doc_id}_chunk_{idx:03d}"

        # Merge base metadata with section-level attributes
        chunk_meta = {**metadata_base}
        chunk_meta["section_type"] = section.get("extraction_class", "unknown")
        chunk_meta["chunk_index"] = str(idx)

        # Flatten section attributes into metadata
        for k, v in (section.get("attributes") or {}).items():
            if isinstance(v, (str, int, float, bool)):
                chunk_meta[f"attr_{k}"] = str(v)
            else:
                chunk_meta[f"attr_{k}"] = str(v)

        ids.append(chunk_id)
        documents.append(section["text"])
        metadatas.append(chunk_meta)

    total = upsert_chunks(ids, documents, metadatas)

    return {
        "chunks_stored": len(ids),
        "collection_name": "vantage_vectors",
        "collection_total": total,
    }


# ---------------------------------------------------------------------------
# 5.  Public API - process_document()
# ---------------------------------------------------------------------------

async def process_document(document_id: str) -> dict:
    """
    Full Knowledge Bridge pipeline for a single document.

    1. Fetch from DB  ->  2. Extract PDF text  ->  3. AI section extraction
    ->  4. Vectorize into ChromaDB

    Returns a summary dict with processing results.
    """
    from sqlalchemy import select
    from database import async_session_maker
    from models import Document as DocumentModel

    # --- Step 1: Fetch document from DB ---
    async with async_session_maker() as session:
        result = await session.execute(
            select(DocumentModel).where(DocumentModel.id == document_id)
        )
        document = result.scalar_one_or_none()

        if not document:
            raise ValueError(f"Document {document_id} not found in database.")

        if not document.file_data:
            raise ValueError(
                f"Document {document_id} ('{document.name}') has no binary file data stored."
            )

        # Build metadata while we still have the ORM instance in session
        metadata_base = _build_metadata(document)
        file_data = bytes(document.file_data)
        doc_name = document.name

    logger.info("Processing document '%s' (id=%s)", doc_name, document_id)

    # --- Step 2: Extract text from PDF ---
    raw_text = _extract_text_from_pdf(file_data)
    logger.info("Extracted %d characters from PDF", len(raw_text))

    # --- Step 3: Dynamic section extraction via OpenRouter AI ---
    sections = _extract_sections(raw_text)
    logger.info("AI found %d sections", len(sections))

    # --- Step 4: Vectorize into ChromaDB ---
    vector_result = _vectorize_sections(sections, metadata_base)
    logger.info(
        "Stored %d chunks in vector store (total: %d)",
        vector_result["chunks_stored"],
        vector_result["collection_total"],
    )

    # --- Step 5: Update document record with summary ---
    async with async_session_maker() as session:
        result = await session.execute(
            select(DocumentModel).where(DocumentModel.id == document_id)
        )
        doc = result.scalar_one_or_none()
        if doc:
            section_types = [s.get("extraction_class", "unknown") for s in sections]
            doc.summary = (
                f"Processed by Knowledge Bridge: {len(sections)} sections extracted "
                f"({', '.join(set(section_types))}). "
                f"{vector_result['chunks_stored']} chunks vectorized into ChromaDB."
            )
            await session.commit()

    return {
        "document_id": document_id,
        "document_name": doc_name,
        "text_length": len(raw_text),
        "sections_extracted": len(sections),
        "section_types": list({s.get("extraction_class", "unknown") for s in sections}),
        "chunks_stored": vector_result["chunks_stored"],
        "collection_total": vector_result["collection_total"],
        "metadata_keys": list(metadata_base.keys()),
    }


# ---------------------------------------------------------------------------
# 6.  Utility - Query the knowledge base
# ---------------------------------------------------------------------------

def query_knowledge_base(
    query_text: str,
    n_results: int = 5,
    where_filter: dict | None = None,
) -> list[dict]:
    """
    Query the FAISS vector store for relevant document chunks.

    Args:
        query_text: The search query.
        n_results: Number of results to return.
        where_filter: Optional metadata filter dict
                      (e.g. {"user_id": "abc-123"}).

    Returns:
        List of dicts with keys: id, text, metadata, distance.
    """
    from services.faiss_vector_store import query

    return query(
        query_text=query_text,
        n_results=n_results,
        where_filter=where_filter,
    )
