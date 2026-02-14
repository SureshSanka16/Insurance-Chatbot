"""
SQLAlchemy models for the insurance application.
Matches frontend TypeScript types defined in types.ts.
"""

import enum
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column, String, Integer, Numeric, DateTime, Date, Text, 
    ForeignKey, Enum as SQLEnum, JSON, Boolean, LargeBinary
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from database import Base


# Custom UUID type that works with both SQLite and PostgreSQL
def generate_uuid():
    return str(uuid.uuid4())


# Enums matching frontend types
class UserRole(str, enum.Enum):
    ADMIN = "Admin"
    USER = "User"


class PolicyCategory(str, enum.Enum):
    LIFE = "Life"
    HEALTH = "Health"
    VEHICLE = "Vehicle"
    PROPERTY = "Property"
    TRAVEL = "Travel"


class PolicyStatus(str, enum.Enum):
    ACTIVE = "Active"
    EXPIRED = "Expired"
    PENDING = "Pending"


class ClaimStatus(str, enum.Enum):
    NEW = "New"
    ANALYZING = "Analyzing"  # Fraud detection in progress
    IN_REVIEW = "In Review"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    FLAGGED = "Flagged"
    PAID = "Paid"



class RiskLevel(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class DocumentType(str, enum.Enum):
    PDF = "PDF"
    DOCX = "DOCX"
    JPG = "JPG"
    PNG = "PNG"


class DocumentCategory(str, enum.Enum):
    LEGAL = "Legal"
    EVIDENCE = "Evidence"
    MEDICAL = "Medical"
    FINANCIAL = "Financial"
    OTHER = "Other"


class Severity(str, enum.Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class FraudStatus(str, enum.Enum):
    PENDING = "PENDING"  # Claim submitted, waiting for analysis
    ANALYZING = "ANALYZING"  # Fraud detection in progress
    COMPLETED = "COMPLETED"  # Analysis completed
    FAILED = "FAILED"  # Analysis failed


# Models
class User(Base):
    """User model matching frontend User interface"""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.USER)
    password_hash = Column(String, nullable=False)
    avatar = Column(String, nullable=True)
    notifications_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    policies = relationship("Policy", back_populates="user")
    assigned_claims = relationship("Claim", back_populates="assignee")


class Policy(Base):
    """Policy model matching frontend Policy interface"""
    __tablename__ = "policies"

    id = Column(String, primary_key=True, default=generate_uuid)
    policy_number = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    category = Column(SQLEnum(PolicyCategory), nullable=False)
    title = Column(String, nullable=False)
    coverage_amount = Column(Numeric(12, 2), nullable=False)
    premium = Column(Numeric(10, 2), nullable=False)
    expiry_date = Column(Date, nullable=False)
    status = Column(SQLEnum(PolicyStatus), nullable=False, default=PolicyStatus.PENDING)
    features = Column(JSON, nullable=True)  # Array of strings
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="policies")
    claims = relationship("Claim", back_populates="policy")


class Claim(Base):
    """
    Claim model matching frontend Claim interface.
    Uses JSON column for polymorphic type-specific data.
    """
    __tablename__ = "claims"

    id = Column(String, primary_key=True)  # e.g., 'CLM-2024-001'
    policy_number = Column(String, ForeignKey("policies.policy_number"), nullable=False)
    claimant_name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # PolicyCategory or custom string
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(SQLEnum(ClaimStatus), nullable=False, default=ClaimStatus.NEW)
    risk_score = Column(Integer, nullable=False, default=0)  # 0-100
    risk_level = Column(SQLEnum(RiskLevel), nullable=False, default=RiskLevel.LOW)
    submission_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    description = Column(Text, nullable=False)
    
    # Optional fields
    assignee_id = Column(String, ForeignKey("users.id"), nullable=True)
    assignment_note = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    device_fingerprint = Column(String, nullable=True)
    
    # JSON columns for polymorphic and complex data
    polymorphic_data = Column(JSON, nullable=True)  # vehicleInfo, healthInfo, lifeInfo, propertyInfo, itemizedLoss
    ai_analysis = Column(JSON, nullable=True)  # {score, reasoning, recommendations[]}
    
    # Fraud detection fields
    fraud_status = Column(SQLEnum(FraudStatus), nullable=True, default=FraudStatus.PENDING)  # Analysis workflow status
    fraud_score = Column(Numeric(5, 4), nullable=True)  # 0.0000 - 1.0000 (stored as decimal)
    fraud_risk_level = Column(String, nullable=True)  # LOW, MEDIUM, HIGH
    fraud_decision = Column(String, nullable=True)  # AUTO_APPROVE, MANUAL_REVIEW, FRAUD_ALERT
    fraud_indicators = Column(JSON, nullable=True)  # List of fraud red flags
    fraud_reasoning = Column(Text, nullable=True)  # LLM explanation
    extracted_fields = Column(JSON, nullable=True)  # OCR + LLM extracted data
    fraud_analyzed_at = Column(DateTime, nullable=True)  # Timestamp of fraud analysis
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    policy = relationship("Policy", back_populates="claims")
    assignee = relationship("User", back_populates="assigned_claims")
    documents = relationship("Document", back_populates="claim", cascade="all, delete-orphan")


class Document(Base):
    """Document model matching frontend Document interface"""
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    claim_id = Column(String, ForeignKey("claims.id"), nullable=True)  # Nullable for base policy documents
    name = Column(String, nullable=False)  # Original filename
    type = Column(SQLEnum(DocumentType), nullable=False)
    url = Column(String, nullable=False, default="")  # File path or URL (empty string for uploaded files)
    size = Column(String, nullable=False)  # e.g., "2.3 MB"
    file_size_bytes = Column(Integer, nullable=True)  # Actual size in bytes
    file_data = Column(LargeBinary, nullable=True)  # Binary PDF data
    content_type = Column(String, nullable=True)  # MIME type (e.g., "application/pdf")
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    summary = Column(Text, nullable=True)  # AI-generated summary
    category = Column(SQLEnum(DocumentCategory), nullable=True)
    extracted_entities = Column(JSON, nullable=True)  # Record<string, string>
    
    # Direct mapping for easier access
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    user_email = Column(String, nullable=True)
    policy_number = Column(String, ForeignKey("policies.policy_number"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    claim = relationship("Claim", back_populates="documents")


class FraudAlert(Base):
    """FraudAlert model matching frontend FraudAlert interface"""
    __tablename__ = "fraud_alerts"

    id = Column(String, primary_key=True, default=generate_uuid)
    severity = Column(SQLEnum(Severity), nullable=False)
    type = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    related_claims = Column(JSON, nullable=False)  # Array of claim IDs
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
