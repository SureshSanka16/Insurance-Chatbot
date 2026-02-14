"""
AI service for risk analysis and document summarization via OpenRouter.

Uses the OpenAI-compatible API provided by OpenRouter to access models
like Gemini, Claude, GPT, etc. through a single API key.
"""

import os
import json
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# ---------------------------------------------------------------------------
# OpenRouter client setup
# ---------------------------------------------------------------------------
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
_AI_MODEL = "google/gemini-2.0-flash-001"  # fast + capable on OpenRouter

if OPENROUTER_API_KEY:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )
    print(f"[OK] OpenRouter AI service ready (model: {_AI_MODEL})")
else:
    client = None
    print("[WARN] OPENROUTER_API_KEY not set. AI features will be disabled.")


def _chat(system_prompt: str, user_prompt: str, *, temperature: float = 0.3, max_tokens: int = 1024) -> str:
    """
    Send a chat completion request to OpenRouter and return the text response.
    """
    if not client:
        raise ValueError("OPENROUTER_API_KEY not configured. Cannot perform AI operations.")

    completion = client.chat.completions.create(
        model=_AI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return completion.choices[0].message.content.strip()


async def analyze_risk(claim_data: dict) -> dict:
    """
    Analyze claim risk using OpenRouter AI.

    Args:
        claim_data: Dictionary containing claim information

    Returns:
        Dictionary with risk_score, risk_level, reasoning, and fraud_indicators

    Raises:
        ValueError: If API key is not configured
        Exception: If AI analysis fails
    """
    if not client:
        raise ValueError("OPENROUTER_API_KEY not configured. Cannot perform AI analysis.")

    # Prepare claim data for analysis
    claim_summary = {
        "claim_id": claim_data.get("id"),
        "type": claim_data.get("type"),
        "amount": claim_data.get("amount"),
        "claimant_name": claim_data.get("claimant_name"),
        "description": claim_data.get("description"),
        "polymorphic_data": claim_data.get("polymorphic_data", {}),
        "submission_date": claim_data.get("submission_date"),
    }

    system_prompt = (
        "You are an expert insurance fraud detection and risk assessment AI. "
        "Analyze insurance claims and provide risk assessments in JSON format. "
        "Provide ONLY the JSON response, no additional text or markdown."
    )

    user_prompt = f"""Analyze the following insurance claim and provide a comprehensive risk assessment.

Claim Details:
{json.dumps(claim_summary, indent=2)}

Respond in this exact JSON format:
{{
    "risk_score": <number between 0-100>,
    "risk_level": "<Low|Medium|High|Critical>",
    "reasoning": "<detailed explanation of your risk assessment>",
    "fraud_indicators": [<list of potential fraud signals, if any>],
    "recommendations": "<recommendations for claim processing>"
}}

Consider the following factors in your analysis:
1. Claim amount relative to typical claims of this type
2. Completeness and consistency of information provided
3. Any unusual patterns or red flags
4. Historical context (if available)
5. Type-specific risk factors (vehicle, health, life, property)"""

    try:
        response_text = _chat(system_prompt, user_prompt, temperature=0.2, max_tokens=1024)

        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        # Parse JSON response
        analysis = json.loads(response_text)

        # Validate required fields
        required_fields = ["risk_score", "risk_level", "reasoning"]
        for field in required_fields:
            if field not in analysis:
                raise ValueError(f"AI response missing required field: {field}")

        # Ensure risk_score is within bounds
        analysis["risk_score"] = max(0, min(100, int(analysis["risk_score"])))

        # Validate risk_level
        valid_levels = ["Low", "Medium", "High", "Critical"]
        if analysis["risk_level"] not in valid_levels:
            # Map to valid level based on score
            score = analysis["risk_score"]
            if score >= 75:
                analysis["risk_level"] = "Critical"
            elif score >= 60:
                analysis["risk_level"] = "High"
            elif score >= 40:
                analysis["risk_level"] = "Medium"
            else:
                analysis["risk_level"] = "Low"

        return analysis

    except json.JSONDecodeError as e:
        print(f"Failed to parse AI response as JSON: {e}")
        # Return fallback analysis
        return {
            "risk_score": 50,
            "risk_level": "Medium",
            "reasoning": "AI analysis failed to parse. Manual review recommended.",
            "fraud_indicators": [],
            "recommendations": "Manual review required due to AI parsing error."
        }
    except Exception as e:
        print(f"AI analysis error: {e}")
        raise


async def copilot_chat(message: str, context: Optional[dict] = None) -> str:
    """
    Handle copilot chat interactions using OpenRouter AI.

    Args:
        message: User's message/question
        context: Optional context dictionary

    Returns:
        AI-generated response text
    """
    if not client:
        raise ValueError("OPENROUTER_API_KEY not configured. Cannot perform AI chat.")

    context = context or {}

    # Build context-aware system prompt
    system_prompt = (
        "You are an intelligent insurance assistant copilot. You help users with:\n"
        "- Understanding insurance policies and coverage\n"
        "- Guidance on submitting claims\n"
        "- Explaining claim statuses and processes\n"
        "- Answering general insurance questions\n"
        "- Providing helpful, accurate, and friendly assistance\n\n"
        "Be concise, professional, and helpful. If you don't have specific "
        "information, guide users on how to find it or who to contact."
    )

    # Add context information
    context_info = []
    if context.get("active_category"):
        context_info.append(f"Current context: {context['active_category']}")
    if context.get("user_role"):
        context_info.append(f"User role: {context['user_role']}")
    if context.get("claim_id"):
        context_info.append(f"Discussing claim: {context['claim_id']}")
    if context.get("policy_id"):
        context_info.append(f"Discussing policy: {context['policy_id']}")

    context_str = "\n".join(context_info) if context_info else "General inquiry"
    user_prompt = f"Context: {context_str}\n\nUser Question: {message}"

    try:
        return _chat(system_prompt, user_prompt)
    except Exception as e:
        print(f"Copilot chat error: {e}")
        raise


async def summarize_document(document_text: str, document_type: str) -> dict:
    """
    Summarize a document using OpenRouter AI.

    Args:
        document_text: Text content of the document
        document_type: Type of document (e.g., "medical_report", "police_report")

    Returns:
        Dictionary with summary and extracted entities
    """
    if not client:
        raise ValueError("OPENROUTER_API_KEY not configured. Cannot perform document summarization.")

    system_prompt = (
        "You are a document analysis AI. Extract summaries and key entities "
        "from documents. Respond ONLY in JSON format, no markdown."
    )

    user_prompt = f"""Analyze the following {document_type} document and provide:
1. A concise summary (2-3 sentences)
2. Key entities extracted (names, dates, amounts, locations, etc.)

Document:
{document_text[:5000]}

Provide your response in JSON format:
{{
    "summary": "<concise summary>",
    "entities": {{
        "names": [<list of names>],
        "dates": [<list of dates>],
        "amounts": [<list of monetary amounts>],
        "locations": [<list of locations>],
        "other": [<other relevant entities>]
    }}
}}"""

    try:
        response_text = _chat(system_prompt, user_prompt, max_tokens=1024)

        # Clean response
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        return json.loads(response_text)

    except Exception as e:
        print(f"Document summarization error: {e}")
        return {
            "summary": "Failed to generate summary.",
            "entities": {}
        }
