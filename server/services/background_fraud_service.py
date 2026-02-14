"""
Background Fraud Detection Service

This service runs fraud detection in the background after claim submission.
It automatically updates claim status based on fraud score thresholds.
"""

import logging
import asyncio
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models import Claim, ClaimStatus, RiskLevel
from services.fraud_detection_service import analyze_claim_fraud
from services.ocr_service import extract_text_from_document
from services.field_extraction_service import extract_fields_from_text
from database import get_db

logger = logging.getLogger("background_fraud_service")


async def run_fraud_detection_background(
    claim_id: str,
    user_id: str,
    policy_number: str,
    claim_category: str
):
    """
    Run fraud detection in the background.
    
    This function:
    1. Sets claim status to ANALYZING
    2. Waits for documents to be uploaded (if needed)
    3. Runs OCR + Field Extraction + Fraud Analysis
    4. Updates claim with fraud results
    5. Auto-approves/rejects based on fraud score
    
    Args:
        claim_id: Claim ID
        user_id: User ID
        policy_number: Policy number
        claim_category: Claim category (Health, Vehicle, etc.)
    """
    
    logger.info(f"Starting background fraud detection for claim {claim_id}")
    
    # Get database session
    async for db in get_db():
        try:
            # Step 1: Update claim status to ANALYZING
            await _update_claim_status(db, claim_id, ClaimStatus.ANALYZING)
            logger.info(f"Claim {claim_id} status set to ANALYZING")
            
            # Step 2: Wait for documents (simulate processing time)
            await asyncio.sleep(5)  # Give user time to upload documents
            
            # Step 3: Get claim documents
            result = await db.execute(
                select(Claim).where(Claim.id == claim_id)
            )
            claim = result.scalar_one_or_none()
            
            if not claim:
                logger.error(f"Claim {claim_id} not found")
                return
            
            # Step 4: Extract fields from documents (if available)
            extracted_fields = {}
            
            if claim.documents and len(claim.documents) > 0:
                # Process first document
                doc = claim.documents[0]
                logger.info(f"Processing document: {doc.name}")
                
                try:
                    # OCR
                    ocr_text = extract_text_from_document(doc.content, doc.type)
                    logger.info(f"OCR extracted {len(ocr_text)} characters")
                    
                    # Field extraction
                    extracted_fields = extract_fields_from_text(ocr_text, claim_category)
                    logger.info(f"Extracted fields: {list(extracted_fields.keys())}")
                    
                except Exception as e:
                    logger.warning(f"Document processing failed: {e}")
                    # Continue with claim data only
            
            # If no documents or extraction failed, use claim data
            if not extracted_fields:
                extracted_fields = {
                    "claim_amount": float(claim.amount),
                    "claim_type": claim.type,
                    "description": claim.description,
                    "claimant_name": claim.claimant_name
                }
            
            # Step 5: Run fraud analysis
            logger.info(f"Running fraud analysis for claim {claim_id}")
            fraud_result = await analyze_claim_fraud(
                extracted_fields=extracted_fields,
                claim_category=claim_category,
                user_id=user_id,
                policy_number=policy_number,
                db=db
            )
            
            # Step 6: Update claim with fraud results
            fraud_score = fraud_result.get("fraud_score", 50)
            fraud_decision = fraud_result.get("decision", "MANUAL_REVIEW")
            
            logger.info(f"Fraud analysis complete: score={fraud_score}, decision={fraud_decision}")
            
            # Step 7: Determine new status based on fraud score
            new_status = _determine_status_from_fraud(fraud_score, fraud_decision)
            
            # Step 8: Update claim
            claim.fraud_score = fraud_score / 100.0  # Convert to 0.0-1.0
            claim.fraud_risk_level = fraud_result.get("risk_level", "MEDIUM")
            claim.fraud_decision = fraud_decision
            claim.fraud_indicators = fraud_result.get("fraud_indicators", [])
            claim.fraud_reasoning = fraud_result.get("reasoning", "")
            claim.extracted_fields = extracted_fields
            claim.risk_score = fraud_score  # Also update risk_score
            claim.risk_level = _get_risk_level(fraud_score)
            claim.status = new_status
            
            await db.commit()
            
            logger.info(f"Claim {claim_id} updated: status={new_status.value}, score={fraud_score}")
            
        except Exception as e:
            logger.error(f"Background fraud detection failed for claim {claim_id}: {e}")
            # Set claim back to IN_REVIEW on error
            await _update_claim_status(db, claim_id, ClaimStatus.IN_REVIEW)
        
        finally:
            break  # Exit the async for loop


async def _update_claim_status(db: AsyncSession, claim_id: str, status: ClaimStatus):
    """Update claim status."""
    result = await db.execute(
        select(Claim).where(Claim.id == claim_id)
    )
    claim = result.scalar_one_or_none()
    
    if claim:
        claim.status = status
        await db.commit()


def _determine_status_from_fraud(fraud_score: int, fraud_decision: str) -> ClaimStatus:
    """
    Determine claim status based on fraud score and decision.
    
    Thresholds:
    - 0-39: AUTO_APPROVE → Approved
    - 40-69: MANUAL_REVIEW → In Review
    - 70-100: FRAUD_ALERT → Rejected
    """
    
    if fraud_decision == "AUTO_APPROVE" or fraud_score < 40:
        return ClaimStatus.APPROVED
    elif fraud_decision == "FRAUD_ALERT" or fraud_score >= 70:
        return ClaimStatus.REJECTED
    else:
        return ClaimStatus.IN_REVIEW


def _get_risk_level(fraud_score: int) -> RiskLevel:
    """Convert fraud score to risk level."""
    if fraud_score >= 70:
        return RiskLevel.CRITICAL
    elif fraud_score >= 40:
        return RiskLevel.MEDIUM
    else:
        return RiskLevel.LOW
