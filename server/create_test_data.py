"""
Script to create test data for claims API testing.
"""
import asyncio
from datetime import datetime, timedelta
from database import async_session_maker
from models import User, Policy, PolicyCategory, PolicyStatus, UserRole

async def create_test_data():
    """Create test user and policy for claims testing."""
    async with async_session_maker() as db:
        try:
            # Create or get test user
            from sqlalchemy import select
            result = await db.execute(select(User).where(User.email == "test@example.com"))
            user = result.scalar_one_or_none()
            
            if not user:
                print("❌ Test user not found. Please register first.")
                return
            
            print(f"✅ Found test user: {user.email}")
            
            # Create test policy
            result = await db.execute(select(Policy).where(Policy.policy_number == "POL-2026-001"))
            existing_policy = result.scalar_one_or_none()
            
            if existing_policy:
                print(f"✅ Test policy already exists: {existing_policy.policy_number}")
            else:
                test_policy = Policy(
                    policy_number="POL-2026-001",
                    user_id=user.id,
                    category=PolicyCategory.VEHICLE,
                    title="Comprehensive Vehicle Insurance",
                    coverage_amount=100000.00,
                    premium=1200.00,
                    expiry_date=(datetime.now() + timedelta(days=365)).date(),
                    status=PolicyStatus.ACTIVE,
                    features=["Collision Coverage", "Theft Protection", "Roadside Assistance"]
                )
                
                db.add(test_policy)
                await db.commit()
                await db.refresh(test_policy)
                
                print(f"✅ Created test policy: {test_policy.policy_number}")
                print(f"   Category: {test_policy.category.value}")
                print(f"   Coverage: ${test_policy.coverage_amount:,.2f}")
            
        except Exception as e:
            print(f"❌ Error creating test data: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(create_test_data())
