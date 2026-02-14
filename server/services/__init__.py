"""
AI service for risk analysis and copilot chat using Google Gemini.
"""

import os
import json
from typing import Optional
import google.generativeai as genai

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # Use Gemini 1.5 Flash for fast responses
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None
    print("WARNING: GEMINI_API_KEY not set. AI features will be disabled.")


async def analyze_risk(claim_data: dict) -> dict:
    """
    Analyze claim risk using Google Gemini AI.
    
    Args:
        claim_data: Dictionary containing claim information
        
    Returns:
        Dictionary with risk_score, risk_level, reasoning, and fraud_indicators
        
    Raises:
        ValueError: If API key is not configured
        Exception: If AI analysis fails
    """
    if not model:
        raise ValueError("GEMINI_API_KEY not configured. Cannot perform AI analysis.")
    
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
    
    # Create prompt for Gemini
    prompt = f"""You are an expert insurance fraud detection and risk assessment AI. Analyze the following insurance claim and provide a comprehensive risk assessment.

Claim Details:
{json.dumps(claim_summary, indent=2)}

Please analyze this claim and provide your assessment in the following JSON format:
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
5. Type-specific risk factors (vehicle, health, life, property)

Provide ONLY the JSON response, no additional text."""

    try:
        # Generate AI response
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
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
        print(f"Response text: {response_text}")
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
    Handle copilot chat interactions using Google Gemini AI.
    
    Args:
        message: User's message/question
        context: Optional context dictionary with:
            - active_category: Current category (e.g., "claims", "policies")
            - claim_id: Optional claim ID for context
            - policy_id: Optional policy ID for context
            - user_role: User's role (e.g., "User", "Admin")
            
    Returns:
        AI-generated response text
        
    Raises:
        ValueError: If API key is not configured
        Exception: If AI chat fails
    """
    if not model:
        raise ValueError("GEMINI_API_KEY not configured. Cannot perform AI chat.")
    
    context = context or {}
    
    # Build context-aware prompt
    system_context = """You are an intelligent insurance assistant copilot. You help users with:
- Understanding insurance policies and coverage
- Guidance on submitting claims
- Explaining claim statuses and processes
- Answering general insurance questions
- Providing helpful, accurate, and friendly assistance

Be concise, professional, and helpful. If you don't have specific information, guide users on how to find it or who to contact."""

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
    
    # Create full prompt
    prompt = f"""{system_context}

Context: {context_str}

User Question: {message}

Please provide a helpful, concise response:"""

    try:
        # Generate AI response
        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        print(f"Copilot chat error: {e}")
        raise


async def summarize_document(document_text: str, document_type: str) -> dict:
    """
    Summarize a document using Google Gemini AI.
    
    Args:
        document_text: Text content of the document
        document_type: Type of document (e.g., "medical_report", "police_report")
        
    Returns:
        Dictionary with summary and extracted entities
        
    Raises:
        ValueError: If API key is not configured
        Exception: If summarization fails
    """
    if not model:
        raise ValueError("GEMINI_API_KEY not configured. Cannot perform document summarization.")
    
    prompt = f"""Analyze the following {document_type} document and provide:
1. A concise summary (2-3 sentences)
2. Key entities extracted (names, dates, amounts, locations, etc.)

Document:
{document_text[:5000]}  # Limit to first 5000 characters

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
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
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
