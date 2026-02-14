"""
Claims management routes for the insurance application.
"""

import logging
import asyncio
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, BackgroundTasks
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract, and_
import io
from sqlalchemy.orm import selectinload

from database import get_db, async_session_maker
from models import Claim, Policy, User, ClaimStatus, RiskLevel, Document, DocumentType, UserRole, DocumentCategory, FraudStatus
from schemas import (
    ClaimCreate, ClaimResponse, ClaimStatusUpdate, DocumentResponse, DocumentUpload
)
from dependencies import get_current_user

logger = logging.getLogger("claims_router")

router = APIRouter()


# ============================================================================
# Background Fraud Detection Service
# ============================================================================

async def run_fraud_detection_background(claim_id: str):
    """
    Background task to run fraud detection on a claim.
    Uses ONLY structured form data - NO OCR or document processing.
    This runs asynchronously after claim is finalized.
    
    Auto-approves/rejects based on fraud score:
    - 0-39: AUTO_APPROVE → Status: Approved
    - 40-69: MANUAL_REVIEW → Status: In Review  
    - 70-100: FRAUD_ALERT → Status: Rejected
    """
    logger.info(f"[FRAUD-DETECTION] Starting rule-based analysis for claim {claim_id}")
    
    # Create a new database session for this background task
    async with async_session_maker() as db:
        try:
            # Import rule-based fraud detection service
            from services.rule_based_fraud_detection import analyze_claim_with_rules
            
            # Fetch claim with documents
            result = await db.execute(
                select(Claim)
                .options(selectinload(Claim.documents))
                .where(Claim.id == claim_id)
            )
            claim = result.scalar_one_or_none()
            
            if not claim:
                logger.error(f"[FRAUD-DETECTION] Claim {claim_id} not found")
                return
            
            # Update status to ANALYZING
            claim.status = ClaimStatus.ANALYZING  # Show "Analyzing" in admin queue
            claim.fraud_status = FraudStatus.ANALYZING
            await db.commit()
            logger.info(f"[FRAUD-DETECTION] Claim {claim_id} status: ANALYZING")
            
            # Simulate detailed analysis process (20 seconds for demo purposes)
            logger.info(f"[FRAUD-DETECTION] Starting comprehensive fraud analysis...")
            import asyncio
            await asyncio.sleep(20)  # 20-second delay to show ANALYZING status
            
            # Get policy info for user_id
            policy_result = await db.execute(
                select(Policy).where(Policy.policy_number == claim.policy_number)
            )
            policy = policy_result.scalar_one_or_none()
            
            if not policy:
                logger.error(f"[FRAUD-DETECTION] Policy {claim.policy_number} not found")
                claim.fraud_status = FraudStatus.FAILED
                claim.status = ClaimStatus.IN_REVIEW  # Fallback to manual review
                await db.commit()
                return
            
            # Extract structured data from claim (NO OCR - just form data)
            from services.field_extraction_service import extract_fields_from_claim
            claim_data = extract_fields_from_claim(claim)
            
            logger.info(f"[FRAUD-DETECTION] Using structured form data only (no OCR)")
            
            # Run rule-based fraud analysis
            logger.info(f"[FRAUD-DETECTION] Running rule-based fraud analysis")
            fraud_analysis = await analyze_claim_with_rules(
                claim_data=claim_data,
                user_id=policy.user_id,
                policy_number=claim.policy_number,
                db=db
            )
            
            # Update claim with fraud analysis results
            fraud_score = fraud_analysis["fraud_score"]
            claim.fraud_score = fraud_score / 100.0  # Store as 0-1
            claim.fraud_risk_level = fraud_analysis["risk_level"]
            claim.fraud_decision = fraud_analysis["decision"]
            claim.fraud_indicators = fraud_analysis.get("fraud_indicators", [])
            claim.fraud_reasoning = fraud_analysis["reasoning"]
            claim.extracted_fields = claim_data
            claim.fraud_analyzed_at = datetime.utcnow()
            claim.fraud_status = FraudStatus.COMPLETED
            
            # Update the risk_score field (0-100) for display in admin queue
            claim.risk_score = fraud_score
            
            # Update risk_level based on fraud score
            if claim.risk_score >= 75:
                claim.risk_level = RiskLevel.CRITICAL
            elif claim.risk_score >= 60:
                claim.risk_level = RiskLevel.HIGH
            elif claim.risk_score >= 40:
                claim.risk_level = RiskLevel.MEDIUM
            else:
                claim.risk_level = RiskLevel.LOW
            
            # ========== AUTO-APPROVAL/REJECTION LOGIC ==========
            # Automatically change claim status based on fraud score
            if fraud_score < 40:
                # LOW RISK (0-39) → AUTO-APPROVE
                claim.status = ClaimStatus.APPROVED
                logger.info(f"[AUTO-DECISION] Claim {claim_id} AUTO-APPROVED (score: {fraud_score})")
            elif fraud_score >= 70:
                # HIGH RISK (70-100) → AUTO-REJECT
                claim.status = ClaimStatus.REJECTED
                logger.info(f"[AUTO-DECISION] Claim {claim_id} AUTO-REJECTED (score: {fraud_score})")
            else:
                # MEDIUM RISK (40-69) → MANUAL REVIEW
                claim.status = ClaimStatus.IN_REVIEW
                logger.info(f"[AUTO-DECISION] Claim {claim_id} requires MANUAL REVIEW (score: {fraud_score})")
            
            await db.commit()
            
            logger.info(
                f"[FRAUD-DETECTION] ✅ Completed for claim {claim_id} - "
                f"Score: {claim.risk_score}, Level: {claim.risk_level.value}, "
                f"Decision: {claim.fraud_decision}, Status: {claim.status.value}, "
                f"Indicators: {len(fraud_analysis.get('fraud_indicators', []))}"
            )
            
        except Exception as e:
            logger.exception(f"[FRAUD-DETECTION] ❌ Failed for claim {claim_id}: {e}")
            # Mark as failed and set to manual review
            try:
                result = await db.execute(select(Claim).where(Claim.id == claim_id))
                claim = result.scalar_one_or_none()
                if claim:
                    claim.fraud_status = FraudStatus.FAILED
                    claim.status = ClaimStatus.IN_REVIEW  # Fallback to manual review on error
                    await db.commit()
            except Exception as commit_error:
                logger.error(f"[FRAUD-DETECTION] Failed to mark claim as FAILED: {commit_error}")



def generate_claim_id(year: int, sequence: int) -> str:
    """
    Generate a custom claim ID in the format CLM-{Year}-{Sequence}.
    
    Args:
        year: Current year
        sequence: Sequential number for the year
        
    Returns:
        Formatted claim ID (e.g., 'CLM-2026-001')
    """
    return f"CLM-{year}-{sequence:03d}"


async def get_next_claim_sequence(db: AsyncSession, year: int) -> int:
    """
    Get the next sequential number for claims in the given year.
    
    Args:
        db: Database session
        year: Year to get sequence for
        
    Returns:
        Next sequence number
    """
    # Count claims in the current year
    result = await db.execute(
        select(func.count(Claim.id)).where(
            extract('year', Claim.submission_date) == year
        )
    )
    count = result.scalar() or 0
    return count + 1


def calculate_risk_score(claim_data: ClaimCreate) -> tuple[int, RiskLevel]:
    """
    Calculate risk score and level for a claim.
    This is a placeholder implementation - should be replaced with actual ML model.
    
    Args:
        claim_data: Claim creation data
        
    Returns:
        Tuple of (risk_score, risk_level)
    """
    # Placeholder logic - in production, use ML model
    score = 50  # Default medium risk
    
    # Adjust based on amount
    if claim_data.amount > 100000:
        score += 20
    elif claim_data.amount > 50000:
        score += 10
    
    # Adjust based on claim type
    if claim_data.type.lower() == "life":
        score += 15
    
    # Determine risk level
    if score >= 75:
        level = RiskLevel.CRITICAL
    elif score >= 60:
        level = RiskLevel.HIGH
    elif score >= 40:
        level = RiskLevel.MEDIUM
    else:
        level = RiskLevel.LOW
    
    return min(score, 100), level


@router.get("/", response_model=list[ClaimResponse])
async def get_claims(
    status: Optional[str] = Query(None, description="Filter by claim status"),
    min_risk_score: Optional[int] = Query(None, description="Filter by minimum risk score"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a list of claims with optional filtering.
    
    - **status**: Filter by claim status (optional)
    - **min_risk_score**: Filter by minimum risk score (optional)
    - **skip**: Pagination offset
    - **limit**: Maximum number of results
    """
    # Build query
    query = select(Claim).options(selectinload(Claim.documents))
    
    # Apply filters
    if status:
        try:
            status_enum = ClaimStatus(status)
            query = query.where(Claim.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}"
            )
    
    if min_risk_score is not None:
        query = query.where(Claim.risk_score >= min_risk_score)
    
    # Apply pagination
    if current_user.role != UserRole.ADMIN:
        query = query.join(Policy).where(Policy.user_id == current_user.id)
    
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    claims = result.scalars().all()
    
    print(f"[DEBUG] Fetched {len(claims)} claims")
    if claims:
        c = claims[0]
        print(f"[DEBUG] First claim: id={c.id}, claimant_name={c.claimant_name}, status={c.status}")
    
    return claims


@router.post("/{claim_id}/trigger-fraud-detection", status_code=status.HTTP_202_ACCEPTED)
async def trigger_fraud_detection(
    claim_id: str,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger fraud detection for a claim.
    Useful for re-analyzing or when automatic detection didn't run.
    """
    # Verify claim exists
    result = await db.execute(
        select(Claim).where(Claim.id == claim_id)
    )
    claim = result.scalar_one_or_none()
    
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {claim_id} not found"
        )
    
    # Check if already analyzing
    if claim.fraud_status == FraudStatus.ANALYZING:
        return {
            "message": "Fraud detection already in progress",
            "claim_id": claim_id,
            "status": "ANALYZING"
        }
    
    # Trigger background analysis
    logger.info(f"[MANUAL-TRIGGER] Fraud detection requested for claim {claim_id}")
    
    if background_tasks:
        background_tasks.add_task(run_fraud_detection_background, claim_id)
    else:
        asyncio.create_task(run_fraud_detection_background(claim_id))
    
    return {
        "message": "Fraud detection triggered successfully",
        "claim_id": claim_id,
        "status": "TRIGGERED"
    }


@router.post("/{claim_id}/finalize", status_code=status.HTTP_202_ACCEPTED)
async def finalize_claim(
    claim_id: str,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Finalize claim submission after all documents are uploaded.
    This triggers the fraud detection analysis.
    
    Should be called by frontend after all documents are successfully uploaded.
    """
    # Verify claim exists
    result = await db.execute(
        select(Claim).where(Claim.id == claim_id)
    )
    claim = result.scalar_one_or_none()
    
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {claim_id} not found"
        )
    
    # Authorization check
    if current_user.role != UserRole.ADMIN:
        result = await db.execute(
            select(Policy).where(Policy.policy_number == claim.policy_number)
        )
        policy = result.scalar_one_or_none()
        if not policy or policy.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only finalize your own claims"
            )
    
    # Only trigger if still pending
    if claim.fraud_status == FraudStatus.PENDING:
        logger.info(f"[CLAIM-FINALIZE] Claim {claim_id} finalized, triggering fraud detection")
        
        # Trigger background fraud detection
        if background_tasks:
            background_tasks.add_task(run_fraud_detection_background, claim_id)
        else:
            asyncio.create_task(run_fraud_detection_background(claim_id))
        
        return {
            "message": "Claim finalized, fraud detection started",
            "claim_id": claim_id,
            "fraud_status": "ANALYZING"
        }
    else:
        return {
            "message": "Claim already finalized",
            "claim_id": claim_id,
            "fraud_status": claim.fraud_status.value
        }


@router.post("/", response_model=ClaimResponse, status_code=status.HTTP_201_CREATED)
async def create_claim(
    claim_data: ClaimCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new claim.
    
    Generates a custom claim ID in the format CLM-{Year}-{Sequence}.
    Accepts nested JSON objects for type-specific information.
    """
    print(f"[DEBUG] Creating claim for policy: {claim_data.policy_number}")
    print(f"[DEBUG] Claimant: {claim_data.claimant_name}, Type: {claim_data.type}, Amount: {claim_data.amount}")
    
    # Verify policy exists
    result = await db.execute(
        select(Policy).where(Policy.policy_number == claim_data.policy_number)
    )
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy {claim_data.policy_number} not found"
        )
    
    # Verify policy ownership
    if current_user.role != UserRole.ADMIN and policy.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to create a claim for this policy"
        )
    
    # Check for existing active claims on this policy
    # Active claims are those not in final states (Paid or Rejected)
    existing_claim_result = await db.execute(
        select(Claim).where(
            Claim.policy_number == claim_data.policy_number,
            Claim.status.in_([ClaimStatus.NEW, ClaimStatus.IN_REVIEW, ClaimStatus.APPROVED, ClaimStatus.FLAGGED])
        )
    )
    existing_claim = existing_claim_result.scalar_one_or_none()
    
    if existing_claim:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An active claim ({existing_claim.id}) already exists for this policy. Please wait for it to be processed before filing a new claim."
        )
    
    # Generate claim ID
    current_year = datetime.utcnow().year
    sequence = await get_next_claim_sequence(db, current_year)
    claim_id = generate_claim_id(current_year, sequence)
    
    # Don't calculate risk score yet - will be done by fraud detection
    # Initially set to NULL to indicate analysis is pending
    risk_score = None
    risk_level = RiskLevel.LOW  # Default until analysis completes
    
    # Prepare polymorphic data
    polymorphic_data = {}
    if claim_data.vehicle_info:
        polymorphic_data["vehicleInfo"] = claim_data.vehicle_info.model_dump()
    if claim_data.health_info:
        polymorphic_data["healthInfo"] = claim_data.health_info.model_dump()
    if claim_data.life_info:
        polymorphic_data["lifeInfo"] = claim_data.life_info.model_dump()
    if claim_data.property_info:
        polymorphic_data["propertyInfo"] = claim_data.property_info.model_dump()
    if claim_data.itemized_loss:
        polymorphic_data["itemizedLoss"] = [item.model_dump() for item in claim_data.itemized_loss]
    
    # Create claim with fraud analysis pending
    new_claim = Claim(
        id=claim_id,
        policy_number=claim_data.policy_number,
        claimant_name=claim_data.claimant_name,
        type=claim_data.type,
        amount=claim_data.amount,
        description=claim_data.description,
        status=ClaimStatus.NEW,
        risk_score=risk_score,  # NULL until fraud analysis completes
        risk_level=risk_level,
        fraud_status=FraudStatus.PENDING,  # Initially pending fraud analysis
        polymorphic_data=polymorphic_data if polymorphic_data else None,
        ip_address=claim_data.ip_address,
        phone_number=claim_data.phone_number,
        device_fingerprint=claim_data.device_fingerprint,
    )
    
    db.add(new_claim)
    await db.commit()
    await db.refresh(new_claim, attribute_names=['documents'])
    
    print(f"[DEBUG] Claim created successfully: {new_claim.id}")
    print(f"[DEBUG] Returning claim - status: {new_claim.status}, claimant_name: {new_claim.claimant_name}")
    print(f"[DEBUG] Fraud status: {new_claim.fraud_status.value}, will run analysis when documents uploaded")
    
    return new_claim


@router.get("/{claim_id}", response_model=ClaimResponse)
async def get_claim(
    claim_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific claim.
    
    Includes all claim details and associated documents.
    """
    if current_user.role != UserRole.ADMIN:
        result = await db.execute(
            select(Claim)
            .options(selectinload(Claim.documents))
            .join(Policy)
            .where(
                and_(
                    Claim.id == claim_id,
                    Policy.user_id == current_user.id
                )
            )
        )
    else:
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
    
    return claim


@router.patch("/{claim_id}/status", response_model=ClaimResponse)
async def update_claim_status(
    claim_id: str,
    status_update: ClaimStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update the status of a claim.
    
    - **status**: New status value (New, In Review, Approved, Rejected, Flagged, Paid)
    """
    # Get claim
    if current_user.role != UserRole.ADMIN:
        result = await db.execute(
            select(Claim)
            .options(selectinload(Claim.documents))
            .join(Policy)
            .where(
                and_(
                    Claim.id == claim_id,
                    Policy.user_id == current_user.id
                )
            )
        )
    else:
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
    
    # Validate status
    try:
        new_status = ClaimStatus(status_update.status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {status_update.status}"
        )
    
    # Update status
    claim.status = new_status
    
    await db.commit()
    await db.refresh(claim)
    
    return claim


# Document upload endpoints
@router.post("/{claim_id}/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    claim_id: str,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    document_type: str = Query(..., description="Type of document (e.g., 'Police Report', 'Medical Bills')"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a PDF document for a claim.
    
    - **claim_id**: ID of the claim to attach document to
    - **file**: PDF file to upload
    - **document_type**: Type/category of the document
    """
    # Fetch claim with policy and user eagerly loaded
    result = await db.execute(
        select(Claim)
        .options(selectinload(Claim.policy).selectinload(Policy.user))
        .where(Claim.id == claim_id)
    )
    claim = result.scalar_one_or_none()
    
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {claim_id} not found in DB lookup"
        )

    # Verify ownership
    if current_user.role != UserRole.ADMIN:
        if not claim.policy or claim.policy.user_id != current_user.id:
            debug_info = f"User: {current_user.id}, Policy Owner: {claim.policy.user_id if claim.policy else 'None'}, Policy: {claim.policy_number}"
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Claim {claim_id} ownership check failed: {debug_info}"
            )
        
        # Validate file type
        if not file.content_type or file.content_type != "application/pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are allowed"
            )
        
        # Read file data
        file_data = await file.read()
        file_size_bytes = len(file_data)
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if file_size_bytes > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed size of {max_size / (1024 * 1024)}MB"
            )
        
        # Format file size for display
        if file_size_bytes < 1024:
            size_str = f"{file_size_bytes} B"
        elif file_size_bytes < 1024 * 1024:
            size_str = f"{file_size_bytes / 1024:.1f} KB"
        else:
            size_str = f"{file_size_bytes / (1024 * 1024):.1f} MB"
        
        # Map frontend document types to backend categories
        category_map = {
            "incidentReport": DocumentCategory.LEGAL,
            "medicalReport": DocumentCategory.MEDICAL,
            "damagePhotos": DocumentCategory.EVIDENCE,
            "witnessStatement": DocumentCategory.LEGAL, 
            "repairEstimate": DocumentCategory.FINANCIAL,
            "otherDocs": DocumentCategory.OTHER,
            "policeReport": DocumentCategory.LEGAL,
            "medicalBills": DocumentCategory.FINANCIAL
        }
        
        # Determine category (case-insensitive fallback)
        doc_category = category_map.get(document_type)
        if not doc_category:
            # Try to match by value
            try:
                doc_category = DocumentCategory(document_type)
            except ValueError:
                # Default to OTHER
                doc_category = DocumentCategory.OTHER

        # Create document record
        document = Document(
            claim_id=claim_id,
            name=file.filename or "document.pdf",
            type=DocumentType.PDF,
            url="",  # Empty string for uploaded files
            size=size_str,
            file_size_bytes=file_size_bytes,
            file_data=file_data,
            content_type=file.content_type,
            category=doc_category,
            date=datetime.utcnow(),
            # Direct mapping
            user_id=claim.policy.user_id if claim.policy else None,
            user_email=claim.policy.user.email if claim.policy and claim.policy.user else None,
            policy_number=claim.policy_number
        )
        
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        logger.info(f"[DOCUMENT-UPLOAD] Document '{document.name}' uploaded for claim {claim_id}. Fraud detection will trigger after finalization.")
        
        return document
        
        
        return document


@router.get("/{claim_id}/documents", response_model=List[DocumentResponse])
async def get_claim_documents(
    claim_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all documents for a specific claim.
    
    - **claim_id**: ID of the claim
    """
    # Verify claim exists
    if current_user.role != UserRole.ADMIN:
        result = await db.execute(
            select(Claim)
            .join(Policy)
            .where(
                and_(
                    Claim.id == claim_id,
                    Policy.user_id == current_user.id
                )
            )
        )
    else:
        result = await db.execute(
            select(Claim).where(Claim.id == claim_id)
        )
    claim = result.scalar_one_or_none()
    
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {claim_id} not found"
        )
    
    # Get all documents for this claim
    result = await db.execute(
        select(Document).where(Document.claim_id == claim_id).order_by(Document.created_at.desc())
    )
    documents = result.scalars().all()
    
    return documents


@router.get("/documents/{document_id}")
async def download_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download a specific document by ID.
    
    Returns the PDF file as a binary response.
    """
    # Get document
    if current_user.role != UserRole.ADMIN:
        result = await db.execute(
            select(Document)
            .join(Claim)
            .join(Policy)
            .where(
                and_(
                    Document.id == document_id,
                    Policy.user_id == current_user.id
                )
            )
        )
    else:
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )
    
    if not document.file_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file data not found"
        )
    
    # Return file as response
    return Response(
        content=document.file_data,
        media_type=document.content_type or "application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{document.name}"'
        }
    )
