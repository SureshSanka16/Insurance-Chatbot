"""
Pydantic schemas for request/response validation.
"""

from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field
from models import UserRole


# User Schemas
class UserCreate(BaseModel):
    """Schema for user registration."""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)  # bcrypt max is 72 bytes
    role: UserRole = UserRole.USER
    avatar: Optional[str] = None


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user details."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    avatar: Optional[str] = None
    notifications_enabled: Optional[bool] = None


class UserResponse(BaseModel):
    """Schema for user response (excludes password)."""
    id: str
    name: str
    email: str
    role: UserRole
    avatar: Optional[str] = None
    notifications_enabled: bool = True
    
    class Config:
        from_attributes = True  # Allows creating from ORM models


# Token Schemas
class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for JWT token payload data."""
    user_id: Optional[str] = None
    email: Optional[str] = None


# Policy Schemas
class PolicyCreate(BaseModel):
    """Schema for creating a new policy."""
    category: str  # 'Life', 'Health', 'Vehicle', 'Property'
    title: str
    coverage_amount: float
    premium: float
    policy_number: Optional[str] = None  # Auto-generated if not provided
    expiry_date: Optional[str] = None  # Can be set later
    status: Optional[str] = "Active"  # 'Active', 'Expired', 'Pending'
    features: Optional[list[str]] = None



class PolicyResponse(BaseModel):
    """Schema for policy response."""
    id: str
    policy_number: str
    user_id: str
    category: str
    title: str
    coverage_amount: float
    premium: float
    expiry_date: date
    status: str
    features: Optional[list[str]] = None
    
    class Config:
        from_attributes = True


class PolicyUpdate(BaseModel):
    """Schema for updating a policy."""
    status: Optional[str] = None  # 'Active', 'Expired', 'Pending'
    
    class Config:
        from_attributes = True


# Document Schemas
class DocumentUpload(BaseModel):
    """Schema for uploading a document."""
    document_type: str  # Type/category of document


class DocumentCreate(BaseModel):
    """Schema for creating a document."""
    name: str
    type: str  # 'PDF', 'DOCX', 'JPG', 'PNG'
    url: Optional[str] = None
    size: str
    summary: Optional[str] = None
    category: Optional[str] = None  # 'Legal', 'Evidence', 'Medical', 'Financial', 'Other'


class DocumentResponse(BaseModel):
    """Schema for document response."""
    id: str
    claim_id: Optional[str] = None
    name: str
    type: str
    url: Optional[str] = None
    size: str
    file_size_bytes: Optional[int] = None
    content_type: Optional[str] = None
    date: datetime
    summary: Optional[str] = None
    category: Optional[str] = None
    extracted_entities: Optional[dict] = None
    user_email: Optional[str] = None
    user_id: Optional[str] = None
    policy_number: Optional[str] = None
    
    class Config:
        from_attributes = True


class DocumentListResponse(DocumentResponse):
    """Document with claim context for list views (e.g. Documents Hub)."""
    claimant: Optional[str] = None
    claimId: Optional[str] = None
    claimType: Optional[str] = None


# Claim Schemas - Nested objects for polymorphic data
class VehicleInfo(BaseModel):
    """Vehicle-specific claim information."""
    makeModel: Optional[str] = None
    regNumber: Optional[str] = None
    vin: Optional[str] = None
    odometer: Optional[str] = None
    policeReportFiled: Optional[bool] = None
    policeReportNo: Optional[str] = None
    location: Optional[str] = None
    time: Optional[str] = None
    incidentType: Optional[str] = None


class HealthInfo(BaseModel):
    """Health-specific claim information."""
    dob: Optional[str] = None
    patientName: Optional[str] = None
    relationship: Optional[str] = None
    hospitalName: Optional[str] = None
    hospitalAddress: Optional[str] = None
    admissionDate: Optional[str] = None
    dischargeDate: Optional[str] = None
    doctorName: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    surgeryPerformed: Optional[bool] = None


class LifeInfo(BaseModel):
    """Life insurance-specific claim information."""
    deceasedName: Optional[str] = None
    deceasedDob: Optional[str] = None
    dateOfDeath: Optional[str] = None
    causeOfDeath: Optional[str] = None
    nomineeName: Optional[str] = None
    nomineeRelationship: Optional[str] = None
    nomineeContact: Optional[str] = None
    bankDetails: Optional[str] = None
    sumAssured: Optional[float] = None
    policyStartDate: Optional[str] = None


class PropertyInfo(BaseModel):
    """Property-specific claim information."""
    address: Optional[str] = None
    incidentType: Optional[str] = None
    locationOfDamage: Optional[str] = None
    fireDeptInvolved: Optional[bool] = None
    reportNumber: Optional[str] = None


class ItemizedLoss(BaseModel):
    """Itemized loss entry."""
    item: str
    cost: float


class ClaimCreate(BaseModel):
    """Schema for creating a new claim."""
    policy_number: str
    claimant_name: str
    type: str  # PolicyCategory or custom string
    amount: float
    description: str
    
    # Optional polymorphic fields
    vehicle_info: Optional[VehicleInfo] = None
    health_info: Optional[HealthInfo] = None
    life_info: Optional[LifeInfo] = None
    property_info: Optional[PropertyInfo] = None
    itemized_loss: Optional[list[ItemizedLoss]] = None
    
    # Optional metadata
    ip_address: Optional[str] = None
    phone_number: Optional[str] = None
    device_fingerprint: Optional[str] = None


class ClaimResponse(BaseModel):
    """Schema for claim response."""
    id: str
    policy_number: str
    claimant_name: str
    type: str
    amount: float
    status: str
    risk_score: Optional[int] = None  # Changed to Optional - NULL during analysis
    risk_level: str
    submission_date: datetime
    description: str
    assignee_id: Optional[str] = None
    assignment_note: Optional[str] = None
    polymorphic_data: Optional[dict] = None
    ai_analysis: Optional[dict] = None
    documents: list[DocumentResponse] = []
    
    # Fraud detection fields
    fraud_status: Optional[str] = None
    fraud_score: Optional[float] = None
    fraud_risk_level: Optional[str] = None
    fraud_decision: Optional[str] = None
    fraud_indicators: Optional[list[str]] = None
    fraud_reasoning: Optional[str] = None
    
    class Config:
        from_attributes = True


class ClaimStatusUpdate(BaseModel):
    """Schema for updating claim status."""
    status: str  # 'New', 'In Review', 'Approved', 'Rejected', 'Flagged', 'Paid'

