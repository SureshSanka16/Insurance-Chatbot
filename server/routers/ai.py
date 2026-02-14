"""
AI-powered routes for risk analysis and RAG-augmented copilot chat.

The /copilot/chat endpoint uses the secure RAG service to retrieve
document context scoped to the authenticated user before generating a
response via OpenRouter, so the chatbot automatically "knows" which policy
or claim the user is looking at.
"""

import logging
import os
import time
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from openai import OpenAI

from database import get_db
from models import Claim, Policy, User, UserRole, RiskLevel
from dependencies import get_current_user
from services.ai_service import analyze_risk
from services import simple_rag

load_dotenv()

logger = logging.getLogger("ai_router")

router = APIRouter()

# Tab (frontend category) <-> claim type. Used to filter claims and validate.
TAB_TO_CLAIM_TYPE = {
    "Vehicle": "Vehicle",
    "Health": "Health",
    "Life": "Life",
    "Home": "Property",
}
CLAIM_TYPE_TO_TAB = {v: k for k, v in TAB_TO_CLAIM_TYPE.items()}

# Base policy PDF source names per tab - RAG returns only these when tab is set.
TAB_TO_BASE_POLICY_SOURCES = {
    "Vehicle": ["Drive_Secure_V-15.pdf"],
    "Health": ["Health_Shield_H-500.pdf"],
    "Life": ["Platinum_Life_L-100.pdf"],
    "Home": ["Home_Protect_P-50.pdf"],
}

# ---------------------------------------------------------------------------
# OpenRouter client for copilot
# ---------------------------------------------------------------------------
_OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
_openrouter_client: OpenAI | None = None
_COPILOT_MODEL = "google/gemini-2.0-flash-001"  # fast, capable, cheap on OpenRouter

if _OPENROUTER_API_KEY:
    _openrouter_client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=_OPENROUTER_API_KEY,
    )
    print(f"[OK] OpenRouter configured for copilot (model: {_COPILOT_MODEL})")
else:
    print("[WARN] OPENROUTER_API_KEY not set. AI copilot will be disabled.")


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class CopilotChatRequest(BaseModel):
    """Schema for copilot chat request.

    The frontend sends whichever context IDs it has available.
    ``policy_number`` is the canonical key used across the DB and ChromaDB.
    ``policy_id`` is kept for backward-compatibility and mapped automatically.
    """
    message: str = Field(..., min_length=1)
    active_category: Optional[str] = None
    claim_id: Optional[str] = None
    policy_id: Optional[str] = None            # legacy / fallback
    policy_number: Optional[str] = None         # preferred


class CopilotChatResponse(BaseModel):
    """Schema for copilot chat response."""
    response: str
    sources: list[dict] = Field(
        default_factory=list,
        description="RAG source chunks used to generate this answer.",
    )
    rag_context_used: bool = Field(
        False,
        description="True if document context was injected into the prompt.",
    )
    suggested_questions: list[str] = Field(
        default_factory=list,
        description="Context-aware suggested questions for the user.",
    )
    selected_claim_id: Optional[str] = Field(
        None,
        description="The claim ID currently being discussed.",
    )


class RiskAnalysisResponse(BaseModel):
    """Schema for risk analysis response."""
    claim_id: str
    risk_score: int
    risk_level: str
    reasoning: str
    fraud_indicators: Optional[list[str]] = None
    recommendations: Optional[str] = None


# ---------------------------------------------------------------------------
# Risk Analysis endpoint (unchanged)
# ---------------------------------------------------------------------------

@router.post("/claims/{claim_id}/analyze", response_model=RiskAnalysisResponse)
async def analyze_claim_risk(
    claim_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Analyze claim risk using AI.

    Fetches the claim from the database, performs AI-powered risk analysis,
    updates the claim with the analysis results, and returns the analysis.
    """
    result = await db.execute(
        select(Claim)
        .options(selectinload(Claim.documents))
        .where(Claim.id == claim_id)
    )
    claim = result.scalar_one_or_none()

    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {claim_id} not found"
        )

    claim_data = {
        "id": claim.id,
        "policy_number": claim.policy_number,
        "claimant_name": claim.claimant_name,
        "type": claim.type,
        "amount": claim.amount,
        "description": claim.description,
        "submission_date": claim.submission_date.isoformat() if claim.submission_date else None,
        "polymorphic_data": claim.polymorphic_data,
        "ip_address": claim.ip_address,
        "phone_number": claim.phone_number,
        "device_fingerprint": claim.device_fingerprint,
    }

    try:
        analysis = await analyze_risk(claim_data)

        claim.risk_score = analysis["risk_score"]
        risk_level_map = {
            "Low": RiskLevel.LOW,
            "Medium": RiskLevel.MEDIUM,
            "High": RiskLevel.HIGH,
            "Critical": RiskLevel.CRITICAL
        }
        claim.risk_level = risk_level_map.get(analysis["risk_level"], RiskLevel.MEDIUM)
        claim.ai_analysis = analysis

        await db.commit()
        await db.refresh(claim)

        return RiskAnalysisResponse(
            claim_id=claim.id,
            risk_score=analysis["risk_score"],
            risk_level=analysis["risk_level"],
            reasoning=analysis["reasoning"],
            fraud_indicators=analysis.get("fraud_indicators", []),
            recommendations=analysis.get("recommendations")
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI analysis failed: {str(e)}"
        )


# ---------------------------------------------------------------------------
# RAG-Augmented Copilot Chat
# ---------------------------------------------------------------------------

def _resolve_policy_number(
    policy_id: Optional[str],
    policy_number: Optional[str],
) -> Optional[str]:
    """
    Normalize the two possible ways the frontend can identify a policy.
    ``policy_number`` takes priority; ``policy_id`` is a fallback that
    already maps to Policy.policy_number in the frontend types.
    """
    return policy_number or policy_id


def _extract_claim_id_from_message(message: str) -> Optional[str]:
    """
    Extract claim ID from user message using pattern matching.
    Looks for patterns like CLM-YYYY-XXX or claim CLM-YYYY-XXX.
    Returns the first match found, or None.
    """
    import re
    # Pattern: CLM-YYYY-XXX (case insensitive)
    pattern = r'\b(CLM-\d{4}-\d{3})\b'
    match = re.search(pattern, message, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return None


def _extract_policy_number_from_message(message: str) -> Optional[str]:
    """
    Extract policy number from user message using pattern matching.
    Looks for patterns like POL-YYYY-XXX or policy POL-YYYY-XXX.
    Returns the first match found, or None.
    """
    import re
    # Pattern: POL-YYYY-XXX (case insensitive)
    pattern = r'\b(POL-\d{4}-[A-Z0-9]{3})\b'
    match = re.search(pattern, message, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return None


@router.post("/copilot/chat", response_model=CopilotChatResponse)
async def chat_with_copilot(
    request: CopilotChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    RAG-augmented copilot chat via OpenRouter.

    **Flow:**
    1. Extract `user_id` from the JWT token (secure, server-side).
    2. Extract any context IDs from the request body (category, policy, claim).
    3. Call `rag_service.retrieve_context` with those IDs as privacy-scoped
       filters to fetch relevant document chunks from ChromaDB.
    4. Inject retrieved context into a system prompt.
    5. Instruct the model to answer **only** from the provided context.
    """
    if not _openrouter_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENROUTER_API_KEY not configured. AI features are disabled.",
        )

    # -- 1. Secure: user_id comes from JWT, not from the client ----------------
    user_id = current_user.id
    is_admin = current_user.role == UserRole.ADMIN

    # -- 2. Resolve context IDs and filter claims by category ------------------
    active_category = request.active_category
    
    # PRIORITY 1: Extract IDs from the message text (dynamic)
    message_claim_id = _extract_claim_id_from_message(request.message)
    message_policy_num = _extract_policy_number_from_message(request.message)

    # PRIORITY 2: Use UI context (fallback)
    ui_policy_num = _resolve_policy_number(request.policy_id, request.policy_number)
    ui_claim_id = request.claim_id

    # Use message-extracted IDs if available, otherwise fall back to UI context
    claim_id = message_claim_id or ui_claim_id
    policy_num = message_policy_num or ui_policy_num

    logger.info(
        "Copilot context resolution: category=%s, message_claim=%s, ui_claim=%s, final_claim=%s | "
        "message_policy=%s, ui_policy=%s, final_policy=%s",
        active_category, message_claim_id, ui_claim_id, claim_id,
        message_policy_num, ui_policy_num, policy_num,
    )
    
    # Get claims filtered by active category
    category_claims_context = ""
    if active_category and not claim_id:
        # Map frontend category to claim type
        category_to_claim_type = {
            "Vehicle": "Vehicle",
            "Health": "Health", 
            "Life": "Life",
            "Home": "Property"
        }
        claim_type = category_to_claim_type.get(active_category)
        
        if claim_type:
            # Fetch user's claims for this category
            if is_admin:
                result = await db.execute(
                    select(Claim)
                    .where(Claim.type == claim_type)
                    .order_by(Claim.created_at.desc())
                )
            else:
                result = await db.execute(
                    select(Claim)
                    .join(Policy)
                    .where(Policy.user_id == user_id, Claim.type == claim_type)
                    .order_by(Claim.created_at.desc())
                )
            category_claims = result.scalars().all()
            
            if category_claims:
                claims_list = []
                for c in category_claims:
                    claims_list.append(
                        f"- Claim #{c.id}: {c.type} | "
                        f"Amount: ${float(c.amount):,.2f} | "
                        f"Status: {c.status.value} | "
                        f"Filed: {c.created_at.strftime('%Y-%m-%d') if c.created_at else 'N/A'}"
                    )
                category_claims_context = (
                    f"## Your {active_category} Claims\n" + 
                    "\n".join(claims_list) +
                    "\n\nIf the user hasn't selected a specific claim yet, ask them: "
                    "\"Which claim would you like to discuss?\" and list the claim IDs above."
                )

    # If a claim_id is provided, look up its policy_number and validate tab
    if claim_id:
        result = await db.execute(
            select(Claim).where(Claim.id == claim_id)
        )
        claim_row = result.scalar_one_or_none()
        if claim_row:
            if not policy_num:
                policy_num = claim_row.policy_number
            # Strict tab check: claim must belong to the active category
            if active_category:
                expected_type = TAB_TO_CLAIM_TYPE.get(active_category)
                if expected_type and claim_row.type != expected_type:
                    correct_tab = CLAIM_TYPE_TO_TAB.get(claim_row.type, "the appropriate")
                    return CopilotChatResponse(
                        response=(
                            f"This claim (**{claim_id}**) does not belong to the current category. "
                            f"You're in the **{active_category}** tab, but this claim is a **{claim_row.type}** claim. "
                            f"Please switch to the **{correct_tab}** tab to discuss this claim."
                        ),
                        sources=[],
                        rag_context_used=False,
                        suggested_questions=[],
                        selected_claim_id=None,
                    )

    # -- 3. RAG retrieval (using simple_rag with JSON knowledge base) -----------
    rag_context_text = ""
    rag_sources: list[dict] = []
    rag_used = False
    
    # Skip RAG if user is asking for metadata lists/counts (use database instead)
    query_lower = request.message.lower()
    skip_rag_for_metadata = any(phrase in query_lower for phrase in [
        "how many", "list all", "list my", "show all", "show my"
    ])
    
    # Skip RAG only for specific claim-related questions when no claim is selected
    # Allow general policy questions (like "what's covered") even without claim selection
    claim_specific_queries = [
        "this claim", "my claim", "claim status", "claim details", 
        "claim amount", "claim progress", "when will my claim"
    ]
    skip_rag_no_claim = (
        active_category and not claim_id and not policy_num and
        any(phrase in query_lower for phrase in claim_specific_queries)
    )
    
    logger.info(f"Query: '{request.message}' | Skip RAG (metadata): {skip_rag_for_metadata} | Skip RAG (no claim): {skip_rag_no_claim}")

    if not skip_rag_for_metadata and not skip_rag_no_claim:
        try:
            # Use the new simple RAG service with JSON knowledge base
            from services.simple_rag import retrieve_with_fallback

            rag_result = retrieve_with_fallback(
                query=request.message,
                policy_type=active_category,  # Maps to Vehicle, Health, Life, Home
                top_k=10,
            )

            rag_context_text = rag_result.get("context_text", "")
            rag_used = bool(rag_context_text.strip())
            
            logger.info(f"RAG result: source_type={rag_result.get('source_type')}, has_context={rag_used}")

            # Build compact source list for the response
            for src in rag_result.get("sources", []):
                rag_sources.append({
                    "source": src.get("source", "Knowledge Base"),
                    "section": ", ".join(src.get("matched_sections", [])) or "general",
                    "policy_type": src.get("policy_type", ""),
                })

        except Exception as e:
            # RAG failure is non-fatal -- the chatbot falls back to general knowledge
            logger.warning("RAG retrieval failed (non-fatal): %s", e)

    # -- 4. Look up policy metadata for extra context --------------------------
    policy_context = ""
    all_policies_context = ""
    
    # If user asks about "my policies" or similar, provide ALL their policies
    query_lower = request.message.lower()
    if any(phrase in query_lower for phrase in [
        "my policies", "all policies", "list policies", "show policies", "what policies",
        "how many policies", "policies do i have", "do i have policies", "my policy"
    ]):
        # Fetch all user's policies
        if is_admin:
            result = await db.execute(select(Policy).order_by(Policy.created_at.desc()))
        else:
            result = await db.execute(
                select(Policy)
                .where(Policy.user_id == user_id)
                .order_by(Policy.created_at.desc())
            )
        all_policies = result.scalars().all()
        
        if all_policies:
            policies_list = []
            for p in all_policies:
                policies_list.append(
                    f"- {p.title} ({p.category.value}): "
                    f"Policy #{p.policy_number} | "
                    f"Coverage: ${float(p.coverage_amount):,.2f} | "
                    f"Premium: ${float(p.premium):,.2f}/month | "
                    f"Status: {p.status.value}"
                )
            all_policies_context = "## All Your Policies\n" + "\n".join(policies_list)
    
    # If a specific policy_num is provided, show that policy's details
    if policy_num:
        result = await db.execute(
            select(Policy).where(Policy.policy_number == policy_num)
        )
        policy = result.scalar_one_or_none()
        if policy:
            policy_context = (
                f"Active Policy: {policy.title} ({policy.category.value}) | "
                f"Policy #{policy.policy_number} | "
                f"Coverage: ${float(policy.coverage_amount):,.2f} | "
                f"Premium: ${float(policy.premium):,.2f}/month | "
                f"Status: {policy.status.value} | "
                f"Expires: {policy.expiry_date}"
            )

    claim_context = ""
    all_claims_context = ""
    claim_documents_context = ""
    base_policy_context = ""
    suggested_questions = []
    
    # If user asks about "my claims" or similar, provide ALL their claims
    if any(phrase in query_lower for phrase in [
        "my claims", "all claims", "list claims", "show claims", "what claims",
        "how many claims", "claims do i have", "do i have claims", "my claim"
    ]):
        # Fetch all user's claims
        if is_admin:
            result = await db.execute(select(Claim).order_by(Claim.created_at.desc()))
        else:
            result = await db.execute(
                select(Claim)
                .join(Policy)
                .where(Policy.user_id == user_id)
                .order_by(Claim.created_at.desc())
            )
        all_claims = result.scalars().all()
        
        if all_claims:
            claims_list = []
            for c in all_claims:
                claims_list.append(
                    f"- Claim #{c.id}: {c.type} | "
                    f"Amount: ${float(c.amount):,.2f} | "
                    f"Status: {c.status.value} | "
                    f"Policy: {c.policy_number} | "
                    f"Filed: {c.created_at.strftime('%Y-%m-%d') if c.created_at else 'N/A'}"
                )
            all_claims_context = "## All Your Claims\n" + "\n".join(claims_list)
    
    # If a specific claim_id is provided, load COMPLETE claim context
    if claim_id:
        result = await db.execute(
            select(Claim)
            .options(selectinload(Claim.documents))
            .where(Claim.id == claim_id)
        )
        claim = result.scalar_one_or_none()
        
        if claim:
            # Basic claim info
            claim_context = (
                f"## Selected Claim Details\n"
                f"Claim ID: #{claim.id}\n"
                f"Type: {claim.type}\n"
                f"Amount: ${float(claim.amount):,.2f}\n"
                f"Status: {claim.status.value}\n"
                f"Risk Level: {claim.risk_level.value} (Score: {claim.risk_score}/100)\n"
                f"Description: {claim.description}\n"
                f"Filed: {claim.created_at.strftime('%Y-%m-%d %H:%M') if claim.created_at else 'N/A'}"
            )
            
            # Claim documents
            if claim.documents:
                docs_list = []
                for doc in claim.documents:
                    docs_list.append(
                        f"- {doc.name} ({doc.type}) | "
                        f"Category: {doc.category.value if doc.category else 'N/A'} | "
                        f"Uploaded: {doc.created_at.strftime('%Y-%m-%d') if doc.created_at else 'N/A'}"
                    )
                claim_documents_context = (
                    f"## Uploaded Documents for This Claim\n" +
                    "\n".join(docs_list)
                )
            
            # Get user's policy for this claim
            if claim.policy_number:
                result = await db.execute(
                    select(Policy).where(Policy.policy_number == claim.policy_number)
                )
                user_policy = result.scalar_one_or_none()
                
                if user_policy:
                    policy_context = (
                        f"## User's Policy for This Claim\n"
                        f"Policy: {user_policy.title} ({user_policy.category.value})\n"
                        f"Policy Number: {user_policy.policy_number}\n"
                        f"Coverage: ${float(user_policy.coverage_amount):,.2f}\n"
                        f"Premium: ${float(user_policy.premium):,.2f}/month\n"
                        f"Status: {user_policy.status.value}\n"
                        f"Expires: {user_policy.expiry_date}"
                    )
                    
                    # Generate suggested questions based on claim type
                    if claim.type == "Vehicle":
                        suggested_questions = [
                            "What damages are covered under my policy?",
                            "What is my deductible for this claim?",
                            "Is rental car coverage included?",
                            "How long does the claim process take?",
                            "What documents do I still need to submit?"
                        ]
                    elif claim.type == "Health":
                        suggested_questions = [
                            "What medical procedures are covered?",
                            "What is my co-pay for this treatment?",
                            "Are pre-existing conditions covered?",
                            "What is the claim reimbursement timeline?",
                            "Do I need pre-authorization?"
                        ]
                    elif claim.type == "Life":
                        suggested_questions = [
                            "What is the payout amount?",
                            "Who are the beneficiaries?",
                            "What documents are required?",
                            "How long is the processing time?",
                            "Are there any exclusions?"
                        ]
                    elif claim.type == "Property":
                        suggested_questions = [
                            "What types of damage are covered?",
                            "Is temporary housing covered?",
                            "What is my deductible?",
                            "How do I file for additional damages?",
                            "What is the inspection process?"
                        ]

    # -- 5. Build the system prompt --------------------------------------------
    system_prompt = _build_system_prompt(
        user_name=current_user.name,
        user_role=current_user.role.value,
        active_category=active_category,
        category_claims_context=category_claims_context,
        policy_context=policy_context,
        all_policies_context=all_policies_context,
        claim_context=claim_context,
        claim_documents_context=claim_documents_context,
        all_claims_context=all_claims_context,
        suggested_questions=suggested_questions,
        rag_context=rag_context_text,
        rag_used=rag_used,
    )

    # -- 6. Generate response via OpenRouter (with retry) ----------------------
    max_retries = 3
    last_error = None

    for attempt in range(max_retries):
        try:
            completion = _openrouter_client.chat.completions.create(
                model=_COPILOT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request.message},
                ],
                max_tokens=1024,
                temperature=0.4,
            )

            response_text = completion.choices[0].message.content.strip()

            return CopilotChatResponse(
                response=response_text,
                sources=rag_sources,
                rag_context_used=rag_used,
                suggested_questions=suggested_questions,
                selected_claim_id=claim_id,
            )

        except Exception as e:
            last_error = e
            error_str = str(e)

            # Retry on 429 rate-limit errors with exponential backoff
            if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                wait_seconds = 2 ** attempt * 3  # 3s, 6s, 12s
                logger.warning(
                    "OpenRouter rate-limited (attempt %d/%d), retrying in %ds: %s",
                    attempt + 1, max_retries, wait_seconds, error_str[:200],
                )
                if attempt < max_retries - 1:
                    time.sleep(wait_seconds)
                    continue

            # Non-retryable error -- break immediately
            logger.exception("OpenRouter generation failed (non-retryable)")
            break

    # All retries exhausted or non-retryable error
    error_msg = str(last_error) if last_error else "Unknown error"
    if "429" in error_msg or "quota" in error_msg.lower():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="The AI service is temporarily rate-limited. Please wait a moment and try again.",
        )
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Copilot chat failed: {error_msg}",
    )


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _build_system_prompt(
    *,
    user_name: str,
    user_role: str,
    active_category: Optional[str],
    category_claims_context: str,
    policy_context: str,
    all_policies_context: str,
    claim_context: str,
    claim_documents_context: str,
    all_claims_context: str,
    suggested_questions: list[str],
    rag_context: str,
    rag_used: bool,
) -> str:
    """
    Construct the full system prompt for the copilot, dynamically injecting
    RAG-retrieved document context when available.
    """
    parts: list[str] = []

    # -- Identity & rules ------------------------------------------------------
    parts.append(
        "You are the Vantage Insurance Copilot, an expert AI assistant "
        "embedded in an insurance management platform. You are speaking "
        f"with {user_name} (role: {user_role})."
    )

    parts.append(
        "RULES:\n"
        "- Be concise, professional, and friendly.\n"
        "- ALWAYS use proper markdown formatting with line breaks between sections.\n"
        "- Use bullet points (with proper spacing) or numbered lists for clarity.\n"
        "- Start new paragraphs on separate lines with blank lines between sections.\n"
        "- Format lists with proper spacing: each bullet on its own line.\n"
        "- When citing policy details, reference the specific section or source.\n"
        "- NEVER fabricate coverage amounts, policy terms, or claim details.\n"
        "- CRITICAL: Distinguish between CLAIM-SPECIFIC questions and GENERAL POLICY questions:\n"
        "  * CLAIM-SPECIFIC questions (need a claim): 'claim status', 'my claim', 'claim amount', 'this claim progress'\n"
        "  * GENERAL POLICY questions (answer directly): 'what is covered', 'is surgery covered', 'deductible', 'submit invoice', 'coverage', 'premium', 'benefits'\n"
        "  * For GENERAL POLICY questions, answer directly from the knowledge base - do NOT ask which claim.\n"
        "  * For CLAIM-SPECIFIC questions without a selected claim, ask which claim they mean.\n"
        "- If the user asks about a specific policy or claim, answer based ONLY "
        "on the context provided below. If the context is empty or does not "
        "contain the answer, clearly state: \"I don't have enough information "
        "in your documents to answer that. Please check your policy details "
        "or contact support.\"\n"
        "- IMPORTANT: If the user asks 'how many policies/claims' or 'list my policies/claims', "
        "use the 'All Your Policies' or 'All Your Claims' section below (if provided), "
        "NOT just the 'Active Policy/Claim Metadata' which shows only the currently selected item.\n"
        "- For general insurance questions (not about a specific policy), "
        "you may use your general knowledge.\n"
        "\n**FORMATTING EXAMPLE:**\n"
        "Here's what your coverage includes:\n"
        "\n"
        "• **Accidental Death Benefit:** Additional ₹2,00,000 in case of accidental death\n"
        "• **Critical Illness Rider:** Lump sum of ₹5,00,000 upon diagnosis of 32 defined illnesses  \n"
        "• **Waiver of Premium:** All future premiums waived if totally disabled\n"
        "\n"
        "(Source: Platinum_Life_L-100.pdf | Section: table)"
    )

    # -- Active view context (tab-strict) --------------------------------------
    if active_category:
        parts.append(
            f"The user is currently in the **{active_category}** tab. "
            "You must ONLY answer about " + active_category + " policies and claims. "
            "If the user asks about a claim or policy that belongs to another category "
            "(e.g. Vehicle vs Health vs Life vs Home), reply clearly: "
            "\"This does not belong to the current category. You're in the [X] tab. "
            "Please switch to the correct tab to discuss that claim/policy.\""
        )
    
    # Category-filtered claims (when no specific claim selected)
    if category_claims_context:
        parts.append(category_claims_context)
        parts.append(
            "\nNOTE: The user has NOT selected a specific claim yet. "
            "For CLAIM-SPECIFIC questions (status, amounts, documents), ask which claim they mean. "
            "For GENERAL POLICY questions (coverage, deductibles, benefits, what's covered, surgery, invoice), "
            "answer directly from the policy knowledge base WITHOUT asking about claims."
        )
    
    # Specific claim selected - show comprehensive context
    if claim_context:
        parts.append(claim_context)
    
    if claim_documents_context:
        parts.append(claim_documents_context)

    if policy_context:
        parts.append(policy_context)
    
    # Suggested questions for the selected claim
    if suggested_questions:
        parts.append(
            "## Suggested Questions You Can Answer\n" +
            "\n".join(f"{i+1}. {q}" for i, q in enumerate(suggested_questions)) +
            "\n\nIf the user asks a general question, offer these specific questions to help them."
        )
    
    # All policies context (for list/count queries)
    if all_policies_context:
        parts.append(all_policies_context)
        parts.append(
            "NOTE: The 'All Your Policies' section above shows your ACTUAL policies "
            "from the database. Use this to answer questions about 'how many policies' "
            "or 'list policies', NOT the document excerpts below."
        )
    
    # All claims context (for list/count queries)
    if all_claims_context:
        parts.append(all_claims_context)
        parts.append(
            "NOTE: The 'All Your Claims' section above shows your ACTUAL claims "
            "from the database. Use this to answer questions about 'how many claims' "
            "or 'list claims', NOT the document excerpts below."
        )

    # -- RAG document context --------------------------------------------------
    if rag_used and rag_context:
        parts.append(
            "## Relevant Policy & Document Information\n"
            "The following sections were retrieved from the user's uploaded "
            "documents. Base your answer on this information:\n\n"
            f"{rag_context}"
        )
    else:
        parts.append(
            "## Document Context\n"
            "No document content was retrieved for this query. If the user "
            "asks about specific policy terms or document contents, let them "
            "know that their documents may not have been processed yet."
        )

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Fraud Analysis Endpoint
# ---------------------------------------------------------------------------

class FraudAnalysisRequest(BaseModel):
    """Schema for fraud analysis request."""
    claim_id: str = Field(..., description="Claim ID to analyze")
    document_ids: list[str] = Field(..., description="List of document IDs to analyze")


class FraudAnalysisResponse(BaseModel):
    """Schema for fraud analysis response."""
    claim_id: str
    fraud_score: int = Field(..., ge=0, le=100, description="Fraud risk score (0-100)")
    anomaly_score: Optional[float] = Field(None, description="Anomaly detection score (0-1)")
    risk_level: str = Field(..., description="Risk level: LOW, MEDIUM, HIGH")
    decision: str = Field(..., description="Decision: AUTO_APPROVE, MANUAL_REVIEW, FRAUD_ALERT")
    extracted_fields: dict = Field(default_factory=dict, description="Fields extracted from documents")
    fraud_indicators: list[str] = Field(default_factory=list, description="List of fraud red flags")
    reasoning: str = Field(..., description="Detailed explanation of the fraud analysis")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    confidence: Optional[str] = Field(None, description="Confidence level: LOW, MEDIUM, HIGH")


@router.post("/analyze-claim-fraud", response_model=FraudAnalysisResponse)
async def analyze_claim_fraud_endpoint(
    request: FraudAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Analyze claim documents for fraud using OCR + LLM pipeline.
    
    **Flow:**
    1. Fetch claim and documents from database
    2. Extract text from documents using TrOCR
    3. Extract structured fields using LLM
    4. Analyze fraud risk using LLM with database context and RAG
    5. Update claim with fraud analysis results
    6. Return comprehensive fraud analysis
    """
    start_time = time.time()
    
    try:
        # Import fraud detection services
        from services.ocr_service import extract_text_from_document
        from services.field_extraction_service import extract_fields_from_text, validate_extracted_fields
        from services.fraud_detection_service import analyze_claim_fraud
        
        # Step 1: Fetch claim from database
        result = await db.execute(
            select(Claim)
            .options(selectinload(Claim.documents))
            .where(Claim.id == request.claim_id)
        )
        claim = result.scalar_one_or_none()
        
        if not claim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Claim {request.claim_id} not found"
            )
        
        # Authorization check: users can only analyze their own claims
        if current_user.role != UserRole.ADMIN:
            result = await db.execute(
                select(Policy).where(Policy.policy_number == claim.policy_number)
            )
            policy = result.scalar_one_or_none()
            if not policy or policy.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only analyze your own claims"
                )
        
        # Step 2: Fetch documents
        from models import Document
        result = await db.execute(
            select(Document).where(Document.id.in_(request.document_ids))
        )
        documents = result.scalars().all()
        
        if not documents:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No documents found for analysis"
            )
        
        # Step 3: Extract text from all documents using TrOCR
        logger.info(f"Extracting text from {len(documents)} document(s) using TrOCR")
        all_ocr_text = []
        
        for doc in documents:
            try:
                ocr_text = extract_text_from_document(
                    file_data=doc.file_data,
                    file_type=doc.type
                )
                all_ocr_text.append(ocr_text)
                logger.info(f"Extracted {len(ocr_text)} characters from {doc.name}")
            except Exception as e:
                logger.error(f"OCR failed for document {doc.name}: {e}")
                # Continue with other documents
        
        if not all_ocr_text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Failed to extract text from any document"
            )
        
        # Merge all OCR text
        merged_ocr_text = "\n\n=== DOCUMENT SEPARATOR ===\n\n".join(all_ocr_text)
        
        # Step 4: Extract structured fields using LLM
        logger.info("Extracting structured fields using LLM")
        extracted_fields = extract_fields_from_text(
            ocr_text=merged_ocr_text,
            claim_category=claim.type
        )
        extracted_fields = validate_extracted_fields(extracted_fields)
        
        # Step 5: Analyze fraud using LLM-based approach
        logger.info("Analyzing fraud risk")
        fraud_analysis = await analyze_claim_fraud(
            extracted_fields=extracted_fields,
            claim_category=claim.type,
            user_id=current_user.id,
            policy_number=claim.policy_number,
            db=db
        )
        
        # Step 6: Update claim with fraud analysis results
        claim.fraud_score = fraud_analysis["fraud_score"] / 100.0  # Store as 0-1
        claim.fraud_risk_level = fraud_analysis["risk_level"]
        claim.fraud_decision = fraud_analysis["decision"]
        claim.fraud_indicators = fraud_analysis.get("fraud_indicators", [])
        claim.fraud_reasoning = fraud_analysis["reasoning"]
        claim.extracted_fields = extracted_fields
        claim.fraud_analyzed_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(claim)
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return FraudAnalysisResponse(
            claim_id=claim.id,
            fraud_score=fraud_analysis["fraud_score"],
            anomaly_score=fraud_analysis.get("anomaly_score"),
            risk_level=fraud_analysis["risk_level"],
            decision=fraud_analysis["decision"],
            extracted_fields=extracted_fields,
            fraud_indicators=fraud_analysis.get("fraud_indicators", []),
            reasoning=fraud_analysis["reasoning"],
            processing_time_ms=processing_time_ms,
            confidence=fraud_analysis.get("confidence", "MEDIUM")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Fraud analysis failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fraud analysis failed: {str(e)}"
        )
