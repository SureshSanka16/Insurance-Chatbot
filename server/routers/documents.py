"""
Document processing routes – Knowledge Bridge & Secure RAG endpoints.

Provides endpoints to:
  - Trigger document ingestion into ChromaDB   (POST /documents/{id}/process)
  - Batch-process all unprocessed documents     (POST /documents/process-all)
  - Search the knowledge base (legacy, simple)  (POST /documents/search)
  - **Secure RAG retrieval with privacy scope** (POST /documents/retrieve)
"""

import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database import get_db
from models import User, Document, UserRole, Claim, Policy
from dependencies import get_current_user
from schemas import DocumentListResponse

logger = logging.getLogger("knowledge_bridge.router")

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class ProcessDocumentResponse(BaseModel):
    document_id: str
    document_name: str
    text_length: int
    sections_extracted: int
    section_types: list[str]
    chunks_stored: int
    collection_total: int
    metadata_keys: list[str]


class BatchProcessResponse(BaseModel):
    total_documents: int
    processed: int
    failed: int
    results: list[dict]


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural language search query")
    n_results: int = Field(5, ge=1, le=20, description="Number of results")
    user_id: Optional[str] = Field(None, description="Filter by user_id")
    policy_number: Optional[str] = Field(None, description="Filter by policy_number")
    claim_id: Optional[str] = Field(None, description="Filter by claim_id")


class KnowledgeSearchResult(BaseModel):
    id: str
    text: str
    metadata: dict
    distance: Optional[float] = None


class KnowledgeSearchResponse(BaseModel):
    query: str
    results: list[KnowledgeSearchResult]
    total: int


# -- Secure RAG retrieval schemas --

class RAGRetrieveRequest(BaseModel):
    """Request body for the secure RAG retrieval endpoint."""
    query: str = Field(
        ..., min_length=1,
        description="Natural-language question to search for in the knowledge base.",
    )
    n_results: int = Field(5, ge=1, le=20, description="Max chunks to return.")
    policy_number: Optional[str] = Field(
        None, description="Scope retrieval to a specific policy.",
    )
    claim_id: Optional[str] = Field(
        None, description="Scope retrieval to a specific claim.",
    )
    target_user_id: Optional[str] = Field(
        None,
        description=(
            "Admin-only: scope retrieval to a different user's documents. "
            "Ignored for non-admin callers."
        ),
    )


class RAGChunk(BaseModel):
    id: str
    text: str
    metadata: dict
    distance: Optional[float] = None
    rank: int


class RAGRetrieveResponse(BaseModel):
    """Response from the secure RAG retrieval endpoint."""
    context_text: str = Field(
        ..., description="Concatenated chunk texts ready for LLM context injection.",
    )
    chunks: list[RAGChunk]
    total: int
    applied_filters: dict
    user_id: str = Field(
        ..., description="The user_id that was used to scope the query.",
    )


# ---------------------------------------------------------------------------
# List all documents (Documents Hub)
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=List[DocumentListResponse],
    summary="List all documents (admin: all; user: own and claim-linked)",
)
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns all documents the current user is allowed to see.
    Admin: every document (including base policies with no claim).
    User: documents they uploaded (user_id) or that belong to their claims (claim → policy → user_id).
    """
    q = (
        select(Document)
        .options(selectinload(Document.claim).selectinload(Claim.policy))
        .order_by(Document.created_at.desc())
    )
    result = await db.execute(q)
    rows = result.scalars().all()

    out: List[DocumentListResponse] = []
    for doc in rows:
        if current_user.role != UserRole.ADMIN:
            if doc.user_id != current_user.id:
                if not doc.claim or doc.claim.policy.user_id != current_user.id:
                    continue
        claim = doc.claim
        claimant = claim.claimant_name if claim else None
        claim_id = str(claim.id) if claim else None
        claim_type = claim.type if claim else None
        out.append(
            DocumentListResponse(
                id=doc.id,
                claim_id=doc.claim_id,
                name=doc.name,
                type=doc.type.value if hasattr(doc.type, "value") else str(doc.type),
                url=doc.url or None,
                size=doc.size,
                file_size_bytes=doc.file_size_bytes,
                content_type=doc.content_type,
                date=doc.date,
                summary=doc.summary,
                category=doc.category.value if doc.category and hasattr(doc.category, "value") else (doc.category or None),
                extracted_entities=doc.extracted_entities,
                user_email=doc.user_email,
                user_id=doc.user_id,
                policy_number=doc.policy_number,
                claimant=claimant,
                claimId=claim_id,
                claimType=claim_type,
            )
        )
    return out


# ---------------------------------------------------------------------------
# Endpoints – Ingestion
# ---------------------------------------------------------------------------

@router.post(
    "/{document_id}/process",
    response_model=ProcessDocumentResponse,
    summary="Process a document into the knowledge base",
)
async def process_single_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger the Knowledge Bridge pipeline for a single document.

    1. Extracts text from the stored PDF
    2. Uses OpenRouter AI to discover logical sections
    3. Vectorizes sections into ChromaDB with Gemini embeddings

    Users can process their own documents. Admins can process any document.
    """
    # Verify the document belongs to the user (unless admin)
    if current_user.role != UserRole.ADMIN:
        result = await db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.user_id == current_user.id,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only process your own documents.",
            )

    try:
        from services.knowledge_bridge import process_document

        result = await process_document(document_id)
        return ProcessDocumentResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Knowledge Bridge processing failed for document %s", document_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}",
        )


@router.post(
    "/process-all",
    response_model=BatchProcessResponse,
    summary="Batch-process all unprocessed documents",
)
async def process_all_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Find all unprocessed documents and run the ingestion pipeline on each.

    - Regular users: processes only their own unprocessed documents.
    - Admins: processes ALL unprocessed documents across all users.
    """

    # Find documents that haven't been processed yet
    query = select(Document).where(
        (Document.file_data.isnot(None))
        & (
            (Document.summary.is_(None))
            | (~Document.summary.startswith("Processed by Knowledge Bridge"))
        )
    )
    # Non-admin users can only process their own documents
    if current_user.role != UserRole.ADMIN:
        query = query.where(Document.user_id == current_user.id)

    result = await db.execute(query)
    documents = result.scalars().all()

    from services.knowledge_bridge import process_document

    results: list[dict] = []
    processed = 0
    failed = 0

    for doc in documents:
        try:
            res = await process_document(doc.id)
            results.append({"document_id": doc.id, "status": "success", **res})
            processed += 1
        except Exception as e:
            logger.exception("Failed to process document %s", doc.id)
            results.append({
                "document_id": doc.id,
                "document_name": doc.name,
                "status": "error",
                "error": str(e),
            })
            failed += 1

    return BatchProcessResponse(
        total_documents=len(documents),
        processed=processed,
        failed=failed,
        results=results,
    )


# ---------------------------------------------------------------------------
# Endpoints – Retrieval
# ---------------------------------------------------------------------------

@router.post(
    "/search",
    response_model=KnowledgeSearchResponse,
    summary="Search the knowledge base (simple)",
    deprecated=True,
)
async def search_knowledge_base(
    request: KnowledgeSearchRequest,
    current_user: User = Depends(get_current_user),
):
    """
    **Deprecated** – use ``POST /documents/retrieve`` instead.

    Simple semantic search.  Non-admin users are automatically scoped to
    their own documents.
    """
    from services.knowledge_bridge import query_knowledge_base

    # Build optional metadata filter
    where_filter: dict | None = None
    conditions = {}
    if request.user_id:
        conditions["user_id"] = request.user_id
    if request.policy_number:
        conditions["policy_number"] = request.policy_number
    if request.claim_id:
        conditions["claim_id"] = request.claim_id

    # Non-admin users can only search their own documents
    if current_user.role != UserRole.ADMIN:
        conditions["user_id"] = current_user.id

    if len(conditions) == 1:
        where_filter = conditions
    elif len(conditions) > 1:
        where_filter = {"$and": [{k: v} for k, v in conditions.items()]}

    try:
        results = query_knowledge_base(
            query_text=request.query,
            n_results=request.n_results,
            where_filter=where_filter,
        )

        return KnowledgeSearchResponse(
            query=request.query,
            results=[KnowledgeSearchResult(**r) for r in results],
            total=len(results),
        )

    except Exception as e:
        logger.exception("Knowledge base search failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.post(
    "/retrieve",
    response_model=RAGRetrieveResponse,
    summary="Secure RAG retrieval with mandatory user-scoped privacy",
)
async def retrieve_documents(
    request: RAGRetrieveRequest,
    current_user: User = Depends(get_current_user),
):
    """
    **Privacy-enforced** semantic retrieval for RAG pipelines.

    Security guarantees:
      - Every query is scoped to the authenticated user's `user_id`.
      - Non-admin users **cannot** access another user's documents, even
        if they supply a `target_user_id`.
      - Admin users may set `target_user_id` to scope to a specific user,
        or leave it blank for a cross-user search (audit-logged).
      - A post-retrieval defense-in-depth check strips any chunk whose
        `user_id` metadata does not match the scoped user.

    Returns concatenated `context_text` suitable for direct injection into
    an LLM prompt, plus the individual ranked `chunks` with full metadata.
    """
    from services.rag_service import (
        retrieve_context,
        ScopeViolationError,
        EmptyQueryError,
    )

    # ── Determine the effective user scope ────────────────────────────────
    is_admin = current_user.role == UserRole.ADMIN
    admin_override = False

    # Build filters dict – user_id is ALWAYS present
    filters: dict = {"user_id": current_user.id}

    if is_admin and request.target_user_id:
        # Admin scoping to a specific other user
        filters["user_id"] = request.target_user_id
    elif is_admin and not request.target_user_id:
        # Admin cross-user search – override scope but log audit trail
        admin_override = True

    # Non-admin callers: target_user_id is silently ignored (their own
    # user_id is always enforced).

    if request.policy_number:
        filters["policy_number"] = request.policy_number
    if request.claim_id:
        filters["claim_id"] = request.claim_id

    # ── Call the RAG service ──────────────────────────────────────────────
    try:
        result = retrieve_context(
            query=request.query,
            filters=filters,
            n_results=request.n_results,
            admin_override=admin_override,
        )
    except ScopeViolationError as e:
        # This should never happen because we always inject user_id above,
        # but we handle it defensively.
        logger.error("Scope violation despite server-side injection: %s", e)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except EmptyQueryError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception("RAG retrieval failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retrieval failed: {str(e)}",
        )

    return RAGRetrieveResponse(
        context_text=result["context_text"],
        chunks=[RAGChunk(**c) for c in result["chunks"]],
        total=result["total"],
        applied_filters=result["applied_filters"],
        user_id=filters["user_id"],
    )
