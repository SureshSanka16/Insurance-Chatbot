"""
Secure RAG Retrieval Service
=============================
Provides privacy-enforced retrieval over the ChromaDB knowledge base.

Security model:
  - Every query MUST include a `user_id` scope.  Searching without a user
    scope is treated as a security violation and raises immediately.
  - Admin callers may optionally bypass the user scope by passing
    `admin_override=True`, but `user_id` must still be provided as an
    audit trail (it is logged, not filtered on).
  - All other filter keys are matched dynamically against the metadata
    fields that the Knowledge Bridge wrote at ingestion time, so the
    service adapts automatically if the Document model schema changes.

Relationship chain in the data model (server/models.py):
  User.id  ──FK──▶  Policy.user_id
  Policy.policy_number  ──FK──▶  Claim.policy_number
  Claim.id  ──FK──▶  Document.claim_id
  Document also carries direct copies:  user_id, policy_number, claim_id

ChromaDB metadata written per chunk by knowledge_bridge._build_metadata:
  user_id, claim_id, policy_number, user_email, category, name (filename),
  source, document_id, ingested_at  +  section_type, chunk_index, attr_*
"""

import logging
import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("rag_service")

# ── Metadata keys that the Knowledge Bridge stores and that callers may ──
# ── filter on.  Built dynamically from the Document model at import time ──
# ── so this list stays in sync with schema changes automatically.        ──

_FILTERABLE_METADATA_KEYS: set[str] | None = None


def _get_filterable_keys() -> set[str]:
    """
    Lazily compute the set of metadata keys that callers are allowed to
    filter on.  Derived from the same introspection the Knowledge Bridge
    uses, plus the extra keys it writes explicitly.
    """
    global _FILTERABLE_METADATA_KEYS
    if _FILTERABLE_METADATA_KEYS is not None:
        return _FILTERABLE_METADATA_KEYS

    from services.knowledge_bridge import _get_document_foreign_keys

    # Keys from FK / identifier introspection
    dynamic_keys = set(_get_document_foreign_keys())

    # Keys the bridge always writes explicitly
    explicit_keys = {"source", "document_id", "section_type", "user_id",
                     "claim_id", "policy_number", "user_email", "category"}

    _FILTERABLE_METADATA_KEYS = dynamic_keys | explicit_keys
    return _FILTERABLE_METADATA_KEYS


# ---------------------------------------------------------------------------
#  Core errors
# ---------------------------------------------------------------------------

class ScopeViolationError(Exception):
    """Raised when a retrieval is attempted without mandatory user scope."""
    pass


class EmptyQueryError(ValueError):
    """Raised when the query string is empty or whitespace-only."""
    pass


# ---------------------------------------------------------------------------
#  retrieve_context()
# ---------------------------------------------------------------------------

def retrieve_context(
    query: str,
    filters: dict,
    *,
    n_results: int = 5,
    admin_override: bool = False,
    allowed_base_sources: Optional[list[str]] = None,
    claim_id_scope: Optional[str] = None,
) -> dict:
    """
    Privacy-enforced semantic retrieval from the document knowledge base.

    Parameters
    ----------
    query : str
        Natural-language search query.
    filters : dict
        Key-value pairs to scope the search.  **Must** contain ``user_id``
        unless ``admin_override`` is True (in which case ``user_id`` is still
        required but used only for audit logging, not filtering).
        Any key that matches a stored metadata field (e.g. ``policy_number``,
        ``claim_id``) will be added to the ChromaDB ``where`` clause.
    n_results : int
        Maximum chunks to return (default 5, capped at 20).
    admin_override : bool
        If True, the ``user_id`` filter is logged but NOT enforced,
        allowing cross-user search.  Should only be set when the caller
        has verified the requesting user holds the Admin role.
    allowed_base_sources : list[str], optional
        If provided, base-policy chunks (no user_id in metadata) are
        included only if their ``source`` is in this list. Used to
        restrict RAG to the current tab (e.g. Vehicle tab → only
        Drive_Secure_V-15.pdf).
    claim_id_scope : str, optional
        When set, the vector query is NOT filtered by claim_id (so base
        policies can be returned). After retrieval, chunks are kept only
        if they belong to this claim (metadata.claim_id == claim_id_scope)
        OR are an allowed base policy (no user_id and source in
        allowed_base_sources). Use this to get both claim PDFs and base
        policy in one call.

    Returns
    -------
    dict with keys:
        context_text : str   – concatenated chunk texts (ready for LLM prompt)
        chunks       : list  – individual results with text + metadata
        total        : int   – number of chunks returned
        applied_filters : dict – the filters that were actually sent to ChromaDB

    Raises
    ------
    ScopeViolationError
        If ``user_id`` is missing from *filters*.
    EmptyQueryError
        If *query* is blank.
    """

    # ── Input validation ──────────────────────────────────────────────────

    if not query or not query.strip():
        raise EmptyQueryError("Search query must not be empty.")

    if "user_id" not in filters or not filters["user_id"]:
        raise ScopeViolationError(
            "Retrieval rejected: `user_id` is mandatory in filters. "
            "Searching without a user scope is a security violation."
        )

    n_results = max(1, min(n_results, 20))

    # ── Build vector-store where clause dynamically ────────────────────────
    #
    # IMPORTANT: We intentionally do NOT filter by user_id in the vector
    # query.  Base policy documents have no user_id in their metadata, so
    # any user_id filter would exclude them.  Instead we fetch broadly and
    # rely on the post-retrieval security check below (defence-in-depth)
    # which strips chunks belonging to *other* users while allowing base
    # policy chunks (no user_id) through.

    filterable = _get_filterable_keys()
    chroma_conditions: list[dict[str, str]] = []

    for key, value in filters.items():
        if value is None:
            continue

        # Skip user_id – handled by post-retrieval security check
        if key == "user_id":
            continue
        # When claim_id_scope is set, we don't filter by claim_id in the vector
        # query so we can get both claim docs and base policy; we post-filter instead.
        if key == "claim_id" and claim_id_scope is not None:
            continue

        if key in filterable:
            chroma_conditions.append({key: str(value)})
        else:
            logger.debug(
                "Filter key '%s' is not a recognised metadata field – ignoring.",
                key,
            )

    # Assemble the final `where` dict (without user_id)
    where_clause: dict | None = None
    if len(chroma_conditions) == 1:
        where_clause = chroma_conditions[0]
    elif len(chroma_conditions) > 1:
        where_clause = {"$and": chroma_conditions}

    # ── Audit log ─────────────────────────────────────────────────────────

    logger.info(
        "RAG retrieve | user=%s | admin_override=%s | query=%.80s | filters=%s",
        filters["user_id"],
        admin_override,
        query,
        where_clause,
    )

    # ── Query ChromaDB via Knowledge Bridge ───────────────────────────────

    from services.knowledge_bridge import query_knowledge_base

    raw_results = query_knowledge_base(
        query_text=query.strip(),
        n_results=n_results,
        where_filter=where_clause,
    )

    # ── Post-retrieval assembly ───────────────────────────────────────────

    chunks = []
    context_parts: list[str] = []

    for i, result in enumerate(raw_results):
        text = result.get("text", "")
        meta = result.get("metadata", {})

        # Defense-in-depth: if admin_override is False, verify every
        # returned chunk belongs to the requesting user OR is a base
        # policy (no user_id in metadata).  Chunks from *other* users
        # are silently stripped.
        if not admin_override:
            chunk_user = meta.get("user_id")
            # Allow: chunk has no user_id (base policy) OR matches requester
            if chunk_user and chunk_user != str(filters["user_id"]):
                logger.warning(
                    "SECURITY: Chunk %s has user_id=%s but requester is %s – "
                    "stripping from results.",
                    result.get("id"),
                    chunk_user,
                    filters["user_id"],
                )
                continue

        # Tab filter: when allowed_base_sources is set, base-policy chunks
        # (no user_id) are included only if source is in the list.
        if allowed_base_sources is not None:
            chunk_source = meta.get("source") or ""
            if not meta.get("user_id") and chunk_source not in allowed_base_sources:
                logger.debug(
                    "Filtering out base policy chunk (source=%s) – not in allowed list for this tab.",
                    chunk_source,
                )
                continue

        # When claim_id_scope is set, keep only chunks for this claim or allowed base policy.
        if claim_id_scope is not None:
            chunk_claim = meta.get("claim_id")
            is_base = not meta.get("user_id")
            if is_base:
                if allowed_base_sources is None or (meta.get("source") or "") not in allowed_base_sources:
                    continue
            else:
                if str(chunk_claim) != str(claim_id_scope):
                    logger.debug(
                        "Filtering out chunk (claim_id=%s) – not in scope %s.",
                        chunk_claim,
                        claim_id_scope,
                    )
                    continue

        chunks.append({
            "id": result.get("id"),
            "text": text,
            "metadata": meta,
            "distance": result.get("distance"),
            "rank": i + 1,
        })

        # Build the context block with provenance
        source_label = meta.get("source", "unknown")
        section_label = meta.get("section_type", "section")
        context_parts.append(
            f"[Source: {source_label} | Section: {section_label}]\n{text}"
        )

    context_text = "\n\n---\n\n".join(context_parts)

    return {
        "context_text": context_text,
        "chunks": chunks,
        "total": len(chunks),
        "applied_filters": where_clause or {},
    }


# ---------------------------------------------------------------------------
#  Convenience wrappers
# ---------------------------------------------------------------------------

def retrieve_for_user(
    query: str,
    user_id: str,
    *,
    policy_number: str | None = None,
    claim_id: str | None = None,
    n_results: int = 5,
) -> dict:
    """
    Shorthand for regular (non-admin) user retrieval.

    Automatically constructs the filters dict from the provided arguments
    and enforces user scope.
    """
    filters: dict = {"user_id": user_id}
    if policy_number:
        filters["policy_number"] = policy_number
    if claim_id:
        filters["claim_id"] = claim_id

    return retrieve_context(
        query=query,
        filters=filters,
        n_results=n_results,
        admin_override=False,
    )


def retrieve_for_admin(
    query: str,
    admin_user_id: str,
    *,
    target_user_id: str | None = None,
    policy_number: str | None = None,
    claim_id: str | None = None,
    n_results: int = 10,
) -> dict:
    """
    Admin retrieval – can optionally scope to a target user, or search
    across all users.

    ``admin_user_id`` is always logged for audit purposes.
    """
    filters: dict = {"user_id": admin_user_id}
    admin_override = True

    # If the admin wants to scope to a specific user, filter on that user
    if target_user_id:
        filters["user_id"] = target_user_id
        admin_override = False  # actually enforce the scope

    if policy_number:
        filters["policy_number"] = policy_number
    if claim_id:
        filters["claim_id"] = claim_id

    return retrieve_context(
        query=query,
        filters=filters,
        n_results=n_results,
        admin_override=admin_override,
    )
