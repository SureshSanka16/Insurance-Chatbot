"""
Policy Management API Router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import uuid
from datetime import datetime

from database import get_db
from models import Policy, User, PolicyStatus
from schemas import PolicyCreate, PolicyResponse, PolicyUpdate
from dependencies import get_current_user

router = APIRouter(prefix="/policies", tags=["policies"])


def generate_policy_number() -> str:
    """Generate unique policy number in format POL-YYYY-XXX"""
    year = datetime.now().year
    random_suffix = str(uuid.uuid4())[:3].upper()
    return f"POL-{year}-{random_suffix}"


@router.get("", response_model=List[PolicyResponse])
async def get_user_policies(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all policies for the authenticated user. Admins see all policies."""
    from models import UserRole
    
    if current_user.role == UserRole.ADMIN:
        # Admin sees ALL policies across all users
        result = await db.execute(select(Policy))
    else:
        # Regular users see only their own policies
        result = await db.execute(
            select(Policy).where(Policy.user_id == current_user.id)
        )
    policies = result.scalars().all()
    return policies


@router.post("", response_model=PolicyResponse)
async def create_policy(
    policy_data: PolicyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new policy for the authenticated user"""
    
    # Generate policy number
    policy_number = generate_policy_number()
    
    # Calculate expiry date (default 1 year from now)
    if policy_data.expiry_date:
        # Assuming ISO format YYYY-MM-DD
        expiry_date = datetime.strptime(policy_data.expiry_date, "%Y-%m-%d").date()
    else:
        expiry_date = datetime.now().date().replace(year=datetime.now().year + 1)

    # Map status string to enum
    policy_status = PolicyStatus.ACTIVE
    if policy_data.status:
        if policy_data.status.lower() == "pending":
            policy_status = PolicyStatus.PENDING
        elif policy_data.status.lower() == "expired":
            policy_status = PolicyStatus.EXPIRED
        else:
            policy_status = PolicyStatus.ACTIVE
    
    # Create policy
    new_policy = Policy(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        policy_number=policy_number,
        category=policy_data.category,
        title=policy_data.title,
        coverage_amount=policy_data.coverage_amount,
        premium=policy_data.premium,
        expiry_date=expiry_date,
        status=policy_status,
        features=policy_data.features or []
    )
    
    db.add(new_policy)
    await db.commit()
    await db.refresh(new_policy)
    
    return new_policy


@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific policy by ID. Admins can view any policy."""
    from models import UserRole
    
    if current_user.role == UserRole.ADMIN:
        result = await db.execute(
            select(Policy).where(Policy.id == policy_id)
        )
    else:
        result = await db.execute(
            select(Policy).where(
                Policy.id == policy_id,
                Policy.user_id == current_user.id
            )
        )
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    return policy


@router.patch("/{policy_id}", response_model=PolicyResponse)
async def update_policy_status(
    policy_id: str,
    policy_update: PolicyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update policy status. Only admins can update policies."""
    from models import UserRole
    
    # Check if user is admin
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can update policy status")
    
    # Get the policy
    result = await db.execute(
        select(Policy).where(Policy.id == policy_id)
    )
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # Update status if provided
    if policy_update.status:
        if policy_update.status.lower() == "active":
            policy.status = PolicyStatus.ACTIVE
        elif policy_update.status.lower() == "pending":
            policy.status = PolicyStatus.PENDING
        elif policy_update.status.lower() == "expired":
            policy.status = PolicyStatus.EXPIRED
        else:
            raise HTTPException(status_code=400, detail=f"Invalid status: {policy_update.status}")
    
    await db.commit()
    await db.refresh(policy)
    
    return policy
