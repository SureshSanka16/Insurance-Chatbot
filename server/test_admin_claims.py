"""
Test script to debug admin claims fetching
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models import Claim, User, UserRole, Policy
from schemas import ClaimResponse

DATABASE_URL = "sqlite+aiosqlite:///./vantage.db"

async def test_admin_claims():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get admin user
        result = await session.execute(
            select(User).where(User.email == "admin@vantage.ai")
        )
        admin = result.scalar_one_or_none()
        print(f"Admin user: {admin.email}, role: {admin.role}")
        
        # Fetch claims as admin would
        query = select(Claim).options(selectinload(Claim.documents))
        
        if admin.role != UserRole.ADMIN:
            query = query.join(Policy).where(Policy.user_id == admin.id)
        
        query = query.limit(5)
        
        try:
            result = await session.execute(query)
            claims = result.scalars().all()
            print(f"\nFetched {len(claims)} claims")
            
            for claim in claims:
                print(f"\nClaim {claim.id}:")
                print(f"  - Claimant: {claim.claimant_name}")
                print(f"  - Amount: {claim.amount} (type: {type(claim.amount)})")
                print(f"  - Status: {claim.status}")
                print(f"  - Documents: {len(claim.documents)}")
                
                # Try to serialize with Pydantic
                try:
                    claim_response = ClaimResponse.model_validate(claim)
                    print(f"  - Serialization: SUCCESS")
                except Exception as e:
                    print(f"  - Serialization: FAILED - {e}")
                    
        except Exception as e:
            print(f"ERROR fetching claims: {e}")
            import traceback
            traceback.print_exc()
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_admin_claims())
