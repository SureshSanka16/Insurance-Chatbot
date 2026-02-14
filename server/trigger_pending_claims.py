"""
Trigger fraud detection for all pending claims.
Useful for fixing claims that are stuck in PENDING status.
"""

import asyncio
from sqlalchemy import select
from database import async_session_maker
from models import Claim, FraudStatus
import sys
import os

# Add server directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def trigger_pending_claims():
    """Find and trigger fraud detection for all pending claims."""
    
    # Import here to avoid circular imports
    from routers.claims import run_fraud_detection_background
    
    async with async_session_maker() as db:
        # Find all pending claims
        result = await db.execute(
            select(Claim).where(Claim.fraud_status == FraudStatus.PENDING)
        )
        pending_claims = result.scalars().all()
        
        if not pending_claims:
            print("✅ No pending claims found")
            return
        
        print(f"Found {len(pending_claims)} pending claims:")
        for claim in pending_claims:
            print(f"  - {claim.id}: {claim.claimant_name} - ${claim.amount:,.2f}")
        
        print("\n🔄 Triggering fraud detection for all pending claims...")
        
        # Trigger fraud detection for each claim
        tasks = []
        for claim in pending_claims:
            print(f"  Starting analysis for {claim.id}...")
            task = asyncio.create_task(run_fraud_detection_background(claim.id))
            tasks.append(task)
        
        # Wait for all to complete
        await asyncio.gather(*tasks)
        
        print("\n✅ All fraud detection tasks completed!")
        print("   Claims should now have fraud scores and risk levels.")

if __name__ == "__main__":
    asyncio.run(trigger_pending_claims())
