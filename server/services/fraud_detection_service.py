"""
Fraud Detection Service using LLM-based analysis.

This service:
1. Queries database for claim history
2. Retrieves category-specific context from RAG
3. Uses LLM to analyze fraud risk
4. Returns fraud score, risk level, decision, and reasoning
"""

import logging
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from models import Claim, Policy, User
from services.rag_service import retrieve_for_user

load_dotenv()

logger = logging.getLogger("fraud_detection_service")

# API Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


async def analyze_claim_fraud(
    extracted_fields: Dict[str, Any],
    claim_category: str,
    user_id: str,
    policy_number: str,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Analyze claim for fraud using LLM-based approach.
    
    Args:
        extracted_fields: Fields extracted from claim documents
        claim_category: Type of claim (Health, Vehicle, Life, Property)
        user_id: User ID for database queries
        policy_number: Policy number
        db: Database session
        
    Returns:
        Fraud analysis results
    """
    
    logger.info(f"Analyzing fraud for claim category: {claim_category}")
    
    # Step 1: Get claim history from database
    claim_history = await _get_claim_history(user_id, claim_category, db)
    
    # Step 2: Get policy information from database
    policy_info = await _get_policy_info(policy_number, db)
    
    # Step 3: Get category-specific context from RAG
    rag_context = await _get_category_context(claim_category, user_id, extracted_fields)
    
    # Step 4: Build fraud analysis prompt
    prompt = _build_fraud_analysis_prompt(
        extracted_fields=extracted_fields,
        claim_category=claim_category,
        claim_history=claim_history,
        policy_info=policy_info,
        rag_context=rag_context
    )
    
    # Step 5: Get LLM fraud analysis
    fraud_analysis = await _get_llm_fraud_analysis(prompt)
    
    return fraud_analysis


async def _get_claim_history(
    user_id: str,
    claim_category: str,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Get user's claim history from database.
    """
    logger.info(f"Fetching claim history for user: {user_id}")
    
    try:
        # Get all claims for this user
        result = await db.execute(
            select(Claim)
            .join(Policy, Claim.policy_number == Policy.policy_number)
            .where(Policy.user_id == user_id)
            .order_by(Claim.submission_date.desc())
        )
        claims = result.scalars().all()
        
        # Get category-specific claims
        category_claims = [c for c in claims if c.type == claim_category]
        
        # Calculate statistics
        total_claims = len(claims)
        category_claims_count = len(category_claims)
        
        # Get recent claims (last 6 months)
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        recent_claims = [c for c in claims if c.submission_date >= six_months_ago]
        
        # Calculate total claimed amount
        total_claimed = sum(float(c.amount) for c in claims)
        
        # Get last claim date
        last_claim_date = claims[0].submission_date if claims else None
        days_since_last_claim = (
            (datetime.utcnow() - last_claim_date).days
            if last_claim_date else None
        )
        
        # Check for duplicate invoice numbers
        invoice_numbers = [
            c.polymorphic_data.get("invoice_number")
            for c in claims
            if c.polymorphic_data and c.polymorphic_data.get("invoice_number")
        ]
        
        return {
            "total_claims": total_claims,
            "category_claims_count": category_claims_count,
            "recent_claims_count": len(recent_claims),
            "total_claimed_amount": total_claimed,
            "days_since_last_claim": days_since_last_claim,
            "invoice_numbers": invoice_numbers,
            "claim_frequency": len(recent_claims) / 6.0,  # Claims per month
            "has_rejected_claims": any(c.status == "Rejected" for c in claims),
            "has_flagged_claims": any(c.status == "Flagged" for c in claims)
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch claim history: {e}")
        return {
            "total_claims": 0,
            "error": str(e)
        }


async def _get_policy_info(policy_number: str, db: AsyncSession) -> Dict[str, Any]:
    """
    Get policy information from database.
    """
    logger.info(f"Fetching policy info for: {policy_number}")
    
    try:
        result = await db.execute(
            select(Policy).where(Policy.policy_number == policy_number)
        )
        policy = result.scalar_one_or_none()
        
        if not policy:
            return {"error": "Policy not found"}
        
        # Calculate policy age
        policy_start = policy.created_at
        days_since_start = (datetime.utcnow() - policy_start).days
        
        return {
            "policy_number": policy.policy_number,
            "category": policy.category.value,
            "coverage_amount": float(policy.coverage_amount),
            "premium": float(policy.premium),
            "status": policy.status.value,
            "days_since_start": days_since_start,
            "expiry_date": policy.expiry_date.isoformat() if policy.expiry_date else None,
            "features": policy.features
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch policy info: {e}")
        return {"error": str(e)}


async def _get_category_context(
    claim_category: str,
    user_id: str,
    extracted_fields: Dict[str, Any]
) -> str:
    """
    Get category-specific context from RAG (FAISS).
    
    This retrieves:
    - Hospital information (for Health claims)
    - Policy coverage rules
    - Category-specific guidelines
    """
    logger.info(f"Fetching RAG context for category: {claim_category}")
    
    try:
        # Build query based on extracted fields
        hospital_name = extracted_fields.get("hospital_name", "")
        diagnosis = extracted_fields.get("diagnosis", "")
        treatment = extracted_fields.get("treatment_type", "")
        
        # Query for category-specific information
        query = f"{claim_category} insurance claim for {diagnosis} treatment at {hospital_name}"
        
        # Retrieve context from RAG
        rag_results = retrieve_for_user(
            query=query,
            user_id=user_id,
            n_results=5
        )
        
        # Format context
        context_parts = []
        # Fix: rag_service returns "chunks", not "results"
        for chunk in rag_results.get("chunks", []):
            text = chunk.get("text", "")
            source = chunk.get("metadata", {}).get("source", "Unknown")
            context_parts.append(f"[Source: {source}]\n{text}")
        
        return "\n\n".join(context_parts) if context_parts else "No relevant context found"
        
    except Exception as e:
        logger.error(f"Failed to fetch RAG context: {e}")
        return f"Error retrieving context: {str(e)}"


def _build_fraud_analysis_prompt(
    extracted_fields: Dict[str, Any],
    claim_category: str,
    claim_history: Dict[str, Any],
    policy_info: Dict[str, Any],
    rag_context: str
) -> str:
    """
    Build comprehensive fraud analysis prompt for LLM.
    """
    
    prompt = f"""You are an expert insurance fraud investigator with 20+ years of experience. Analyze this {claim_category} insurance claim for fraud risk.

=== CLAIM INFORMATION ===
Category: {claim_category}
Extracted Fields:
{json.dumps(extracted_fields, indent=2)}

=== POLICY INFORMATION ===
{json.dumps(policy_info, indent=2)}

=== CLAIM HISTORY ===
{json.dumps(claim_history, indent=2)}

=== RELEVANT POLICY RULES & HOSPITAL INFORMATION ===
{rag_context}

=== FRAUD INDICATORS TO CHECK ===

1. **Claim Amount Analysis**
   - Is claim amount reasonable for the treatment?
   - Does it exceed policy coverage?
   - Is it suspiciously round (e.g., exactly 100,000)?

2. **Timing Analysis**
   - Was claim submitted within waiting period?
   - Is there rapid claim frequency?
   - Days since policy start vs claim date

3. **Hospital/Provider Analysis**
   - Is hospital in network?
   - Is hospital blacklisted or high-risk?
   - Hospital reputation and accreditation

4. **Treatment Consistency**
   - Does diagnosis match treatment?
   - Is treatment duration reasonable?
   - Are itemized expenses consistent?

5. **Document Authenticity**
   - Are invoice numbers unique (no duplicates)?
   - Is submission timing reasonable?
   - Are dates logical (admission < discharge)?

6. **Historical Patterns**
   - Claim frequency (too many claims)?
   - Previous rejected/flagged claims?
   - Escalating claim amounts?

7. **Category-Specific Checks**
   {"- Pre-existing condition claims within waiting period" if claim_category == "Health" else ""}
   {"- Accident location and police report consistency" if claim_category == "Vehicle" else ""}
   {"- Cause of death and policy terms alignment" if claim_category == "Life" else ""}

=== YOUR TASK ===

Provide a comprehensive fraud analysis in JSON format:

{{
    "fraud_score": <0-100 integer>,
    "risk_level": "<LOW|MEDIUM|HIGH>",
    "decision": "<AUTO_APPROVE|MANUAL_REVIEW|FRAUD_ALERT>",
    "fraud_indicators": [
        "Specific indicator 1",
        "Specific indicator 2",
        ...
    ],
    "reasoning": "Detailed explanation of your analysis and decision",
    "red_flags_count": <number of red flags found>,
    "confidence": "<LOW|MEDIUM|HIGH>"
}}

=== DECISION CRITERIA ===
- fraud_score 0-39: LOW risk → AUTO_APPROVE
- fraud_score 40-69: MEDIUM risk → MANUAL_REVIEW  
- fraud_score 70-100: HIGH risk → FRAUD_ALERT

Be thorough, objective, and specific. Cite exact numbers and facts.

JSON OUTPUT:
"""
    
    return prompt


async def _get_llm_fraud_analysis(prompt: str) -> Dict[str, Any]:
    """
    Get fraud analysis from LLM.
    """
    
    try:
        if OPENROUTER_API_KEY:
            return await _analyze_with_openrouter(prompt)
        elif GEMINI_API_KEY:
            return await _analyze_with_gemini(prompt)
        else:
            logger.error("No API keys configured for fraud analysis")
            return _fallback_analysis()
    except Exception as e:
        logger.error(f"LLM fraud analysis failed: {e}")
        return _fallback_analysis()


async def _analyze_with_openrouter(prompt: str) -> Dict[str, Any]:
    """
    Analyze fraud using OpenRouter API.
    """
    logger.info("Analyzing fraud using OpenRouter")
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "meta-llama/llama-3.1-8b-instruct:free",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2,
        "max_tokens": 3000
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    
    result = response.json()
    content = result["choices"][0]["message"]["content"]
    
    # Parse JSON from response
    return _parse_fraud_json(content)


async def _analyze_with_gemini(prompt: str) -> Dict[str, Any]:
    """
    Analyze fraud using Google Gemini API.
    """
    logger.info("Analyzing fraud using Gemini")
    
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 3000
            }
        )
        
        content = response.text
        return _parse_fraud_json(content)
        
    except Exception as e:
        logger.error(f"Gemini fraud analysis failed: {e}")
        raise


def _parse_fraud_json(content: str) -> Dict[str, Any]:
    """
    Parse JSON from LLM fraud analysis response.
    """
    # Remove markdown code blocks if present
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    
    content = content.strip()
    
    try:
        analysis = json.loads(content)
        
        # Validate required fields
        required_fields = ["fraud_score", "risk_level", "decision", "reasoning"]
        for field in required_fields:
            if field not in analysis:
                raise ValueError(f"Missing required field: {field}")
        
        # Ensure fraud_indicators is a list
        if "fraud_indicators" not in analysis:
            analysis["fraud_indicators"] = []
        
        return analysis
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse fraud analysis JSON: {e}")
        logger.error(f"Content: {content[:500]}")
        return _fallback_analysis()


def _fallback_analysis() -> Dict[str, Any]:
    """
    Fallback analysis when LLM is unavailable.
    """
    logger.warning("Using fallback fraud analysis")
    
    return {
        "fraud_score": 50,
        "risk_level": "MEDIUM",
        "decision": "MANUAL_REVIEW",
        "fraud_indicators": ["LLM analysis unavailable - manual review required"],
        "reasoning": "Automated fraud detection is currently unavailable. This claim requires manual review by a fraud analyst.",
        "red_flags_count": 0,
        "confidence": "LOW",
        "fallback": True
    }
