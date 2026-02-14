"""
Field Extraction Service using LLM.

Converts OCR text into structured JSON fields using OpenRouter/Gemini AI.
"""

import logging
import json
import os
from typing import Dict, Optional, Any
from dotenv import load_dotenv
import requests

load_dotenv()

logger = logging.getLogger("field_extraction_service")

# API Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def extract_fields_from_text(
    ocr_text: str,
    claim_category: str = "Health"
) -> Dict[str, Any]:
    """
    Extract structured fields from OCR text using LLM.
    
    Args:
        ocr_text: Raw text extracted from claim documents
        claim_category: Type of claim (Health, Vehicle, Life, Property)
        
    Returns:
        Dictionary with extracted fields
    """
    
    # Build extraction prompt based on category
    prompt = _build_extraction_prompt(ocr_text, claim_category)
    
    # Try OpenRouter first, fallback to Gemini
    try:
        if OPENROUTER_API_KEY:
            return _extract_with_openrouter(prompt)
        elif GEMINI_API_KEY:
            return _extract_with_gemini(prompt)
        else:
            logger.error("No API keys configured for LLM extraction")
            return _extract_fallback(ocr_text)
    except Exception as e:
        logger.error(f"LLM extraction failed: {e}")
        return _extract_fallback(ocr_text)


def _build_extraction_prompt(ocr_text: str, claim_category: str) -> str:
    """
    Build extraction prompt based on claim category.
    """
    
    base_fields = """
    Extract the following fields from the insurance claim document text:
    
    REQUIRED FIELDS:
    - claim_amount: Total claim amount (number)
    - hospital_name: Name of the hospital/medical facility
    - admission_date: Date of admission (YYYY-MM-DD format)
    - discharge_date: Date of discharge (YYYY-MM-DD format)
    - diagnosis: Medical diagnosis
    - treatment_type: Type of treatment provided
    - invoice_number: Invoice or bill number
    - policy_number: Insurance policy number
    - patient_name: Name of the patient
    - doctor_name: Name of the treating doctor
    - hospital_address: Hospital address
    - room_type: Type of room (General/Semi-Private/Private/ICU)
    - surgery_performed: Whether surgery was performed (true/false)
    - itemized_expenses: List of expense items with amounts
    """
    
    category_specific = {
        "Health": """
        ADDITIONAL HEALTH FIELDS:
        - relationship_to_policyholder: Relationship (Self/Spouse/Child/Parent)
        - pre_existing_condition: Any pre-existing conditions mentioned
        - emergency_admission: Was it an emergency admission (true/false)
        """,
        
        "Vehicle": """
        ADDITIONAL VEHICLE FIELDS:
        - vehicle_make_model: Vehicle make and model
        - registration_number: Vehicle registration number
        - accident_date: Date of accident
        - accident_location: Location of accident
        - police_report_number: Police report number if filed
        - repair_garage: Name of repair garage
        """,
        
        "Life": """
        ADDITIONAL LIFE FIELDS:
        - deceased_name: Name of deceased
        - date_of_death: Date of death
        - cause_of_death: Cause of death
        - nominee_name: Nominee name
        - nominee_relationship: Relationship to deceased
        """,
        
        "Property": """
        ADDITIONAL PROPERTY FIELDS:
        - property_address: Address of damaged property
        - incident_type: Type of incident (Fire/Theft/Natural Disaster)
        - incident_date: Date of incident
        - fire_dept_report: Fire department report number if applicable
        """
    }
    
    specific = category_specific.get(claim_category, "")
    
    prompt = f"""You are an expert at extracting structured data from insurance claim documents.

{base_fields}
{specific}

DOCUMENT TEXT:
{ocr_text}

INSTRUCTIONS:
1. Extract ALL available fields from the text
2. Use null for fields not found in the text
3. Convert dates to YYYY-MM-DD format
4. Extract numbers without currency symbols
5. Be precise and accurate
6. If multiple values exist, use the most relevant one

OUTPUT FORMAT:
Return ONLY a valid JSON object with the extracted fields. No additional text.

Example:
{{
    "claim_amount": 150000.00,
    "hospital_name": "City Hospital",
    "admission_date": "2026-02-10",
    "discharge_date": "2026-02-14",
    ...
}}

JSON OUTPUT:
"""
    
    return prompt


def _extract_with_openrouter(prompt: str) -> Dict[str, Any]:
    """
    Extract fields using OpenRouter API.
    """
    logger.info("Extracting fields using OpenRouter")
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "meta-llama/llama-3.1-8b-instruct:free",  # Fast and free model
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.1,  # Low temperature for consistent extraction
        "max_tokens": 2000
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    
    result = response.json()
    content = result["choices"][0]["message"]["content"]
    
    # Parse JSON from response
    return _parse_json_response(content)


def _extract_with_gemini(prompt: str) -> Dict[str, Any]:
    """
    Extract fields using Google Gemini API.
    """
    logger.info("Extracting fields using Gemini")
    
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.1,
                "max_output_tokens": 2000
            }
        )
        
        content = response.text
        return _parse_json_response(content)
        
    except Exception as e:
        logger.error(f"Gemini extraction failed: {e}")
        raise


def _parse_json_response(content: str) -> Dict[str, Any]:
    """
    Parse JSON from LLM response, handling markdown code blocks.
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
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        logger.error(f"Content: {content[:500]}")
        raise ValueError("LLM did not return valid JSON")


def _extract_fallback(ocr_text: str) -> Dict[str, Any]:
    """
    Fallback extraction using simple pattern matching.
    Returns empty/null fields if LLM is unavailable.
    """
    logger.warning("Using fallback extraction (no LLM available)")
    
    return {
        "claim_amount": None,
        "hospital_name": None,
        "admission_date": None,
        "discharge_date": None,
        "diagnosis": None,
        "treatment_type": None,
        "invoice_number": None,
        "policy_number": None,
        "patient_name": None,
        "doctor_name": None,
        "extraction_method": "fallback",
        "raw_text_preview": ocr_text[:500] if ocr_text else None
    }


def validate_extracted_fields(fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and clean extracted fields.
    
    Args:
        fields: Extracted fields dictionary
        
    Returns:
        Validated and cleaned fields
    """
    # Ensure numeric fields are numbers
    if fields.get("claim_amount"):
        try:
            fields["claim_amount"] = float(str(fields["claim_amount"]).replace(",", ""))
        except (ValueError, TypeError):
            fields["claim_amount"] = None
    
    # Validate date formats (basic check)
    for date_field in ["admission_date", "discharge_date", "accident_date", "date_of_death"]:
        if fields.get(date_field):
            # Basic validation: should be YYYY-MM-DD format
            date_str = str(fields[date_field])
            if len(date_str) != 10 or date_str.count("-") != 2:
                logger.warning(f"Invalid date format for {date_field}: {date_str}")
    
    return fields


def extract_fields_from_claim(claim) -> Dict[str, Any]:
    """
    Extract structured fields from claim object data.
    This extracts the fields from the claim's polymorphic_data without needing OCR.
    
    Args:
        claim: Claim model instance
        
    Returns:
        Dictionary with extracted fields for fraud analysis
    """
    extracted = {
        "claim_id": claim.id,
        "policy_number": claim.policy_number,
        "claimant_name": claim.claimant_name,
        "claim_type": claim.type,
        "claim_amount": float(claim.amount),
        "description": claim.description,
        "submission_date": claim.submission_date.isoformat() if claim.submission_date else None,
        "ip_address": claim.ip_address,
        "phone_number": claim.phone_number,
        "device_fingerprint": claim.device_fingerprint,
    }
    
    # Extract polymorphic data based on claim type
    poly_data = claim.polymorphic_data or {}
    
    if claim.type == "Health" and "healthInfo" in poly_data:
        health = poly_data["healthInfo"]
        extracted.update({
            "patient_name": health.get("patientName"),
            "dob": health.get("dob"),
            "relationship": health.get("relationship"),
            "hospital_name": health.get("hospitalName"),
            "hospital_address": health.get("hospitalAddress"),
            "admission_date": health.get("admissionDate"),
            "discharge_date": health.get("dischargeDate"),
            "doctor_name": health.get("doctorName"),
            "diagnosis": health.get("diagnosis"),
            "treatment": health.get("treatment"),
            "surgery_performed": health.get("surgeryPerformed"),
        })
    
    elif claim.type == "Vehicle" and "vehicleInfo" in poly_data:
        vehicle = poly_data["vehicleInfo"]
        extracted.update({
            "vehicle_make_model": vehicle.get("makeModel"),
            "registration_number": vehicle.get("regNumber"),
            "vin": vehicle.get("vin"),
            "odometer": vehicle.get("odometer"),
            "police_report_filed": vehicle.get("policeReportFiled"),
            "police_report_number": vehicle.get("policeReportNo"),
            "accident_location": vehicle.get("location"),
            "accident_time": vehicle.get("time"),
            "incident_type": vehicle.get("incidentType"),
        })
    
    elif claim.type == "Life" and "lifeInfo" in poly_data:
        life = poly_data["lifeInfo"]
        extracted.update({
            "deceased_name": life.get("deceasedName"),
            "deceased_dob": life.get("deceasedDob"),
            "date_of_death": life.get("dateOfDeath"),
            "cause_of_death": life.get("causeOfDeath"),
            "nominee_name": life.get("nomineeName"),
            "nominee_relationship": life.get("nomineeRelationship"),
            "nominee_contact": life.get("nomineeContact"),
            "bank_details": life.get("bankDetails"),
            "sum_assured": life.get("sumAssured"),
            "policy_start_date": life.get("policyStartDate"),
        })
    
    elif claim.type == "Property" and "propertyInfo" in poly_data:
        prop = poly_data["propertyInfo"]
        extracted.update({
            "property_address": prop.get("address"),
            "incident_type": prop.get("incidentType"),
            "location_of_damage": prop.get("locationOfDamage"),
            "fire_dept_involved": prop.get("fireDeptInvolved"),
            "report_number": prop.get("reportNumber"),
        })
    
    # Add itemized loss if present
    if "itemizedLoss" in poly_data:
        extracted["itemized_loss"] = poly_data["itemizedLoss"]
    
    # Add document count
    extracted["document_count"] = len(claim.documents) if claim.documents else 0
    
    return extracted

