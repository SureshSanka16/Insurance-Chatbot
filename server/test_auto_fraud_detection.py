"""
Test script to verify rule-based fraud detection workflow.

This tests the simplified fraud detection system that uses ONLY structured form data
(NO OCR or document processing).

Run this to test:
    python test_auto_fraud_detection.py
"""

import asyncio
import sys
from datetime import datetime

sys.path.append('.')

from database import async_session_maker
from models import Claim, FraudStatus
from sqlalchemy import select


async def check_fraud_status():
    """Check the fraud status of all claims."""
    async with async_session_maker() as db:
        result = await db.execute(
            select(Claim).order_by(Claim.created_at.desc()).limit(10)
        )
        claims = result.scalars().all()
        
        print("=" * 80)
        print("RULE-BASED FRAUD DETECTION STATUS CHECK")
        print("=" * 80)
        print()
        
        if not claims:
            print("❌ No claims found in database.")
            return
        
        for claim in claims:
            print(f"Claim ID: {claim.id}")
            print(f"  Type: {claim.type}")
            print(f"  Amount: ${float(claim.amount):,.2f}")
            print(f"  Status: {claim.status.value}")
            print(f"  Fraud Status: {claim.fraud_status.value if claim.fraud_status else 'NULL'}")
            print(f"  Risk Score: {claim.risk_score if claim.risk_score is not None else 'NULL (in progress)'}")
            
            if claim.fraud_status == FraudStatus.COMPLETED:
                print(f"  ✅ Analysis Complete")
                print(f"  Fraud Score: {float(claim.fraud_score) * 100:.1f}%" if claim.fraud_score else "N/A")
                print(f"  Risk Level: {claim.fraud_risk_level}")
                print(f"  Decision: {claim.fraud_decision}")
                if claim.fraud_indicators:
                    print(f"  Indicators: {len(claim.fraud_indicators)} red flags")
                if claim.fraud_analyzed_at:
                    print(f"  Analyzed At: {claim.fraud_analyzed_at}")
            elif claim.fraud_status == FraudStatus.ANALYZING:
                print(f"  🔄 Analysis in progress...")
            elif claim.fraud_status == FraudStatus.PENDING:
                print(f"  📋 Pending analysis (waiting for finalization)")
            elif claim.fraud_status == FraudStatus.FAILED:
                print(f"  ❌ Analysis failed")
            
            print()


async def trigger_manual_fraud_detection(claim_id: str):
    """Manually trigger fraud detection for a claim."""
    from routers.claims import run_fraud_detection_background
    
    print(f"🚀 Triggering rule-based fraud detection for claim {claim_id}...")
    await run_fraud_detection_background(claim_id)
    print(f"✅ Fraud detection triggered!")


if __name__ == "__main__":
    print("\n🔍 Checking fraud detection status...\n")
    asyncio.run(check_fraud_status())
    
    print("\n" + "=" * 80)
    print("SIMPLIFIED WORKFLOW TEST INSTRUCTIONS")
    print("=" * 80)
    print("""
✅ NEW RULE-BASED FRAUD DETECTION (No OCR/LLM Required!)

1. Submit a new claim through the user interface
   - Fill in all form fields (name, amount, hospital, etc.)
   - Upload documents (they're stored but NOT processed)

2. The system will automatically:
   - Set fraud_status = PENDING when claim is created
   - Show "IN PROGRESS" status in admin queue
   - Trigger rule-based fraud detection after finalization
   - Analyze using ONLY the structured form data

3. Fraud detection checks:
   ✓ Claim amount vs policy coverage
   ✓ Policy age (new policies are higher risk)
   ✓ Claim frequency (multiple recent claims)
   ✓ Round number detection
   ✓ Historical patterns
   ✓ Claim type-specific rules

4. Refresh the admin claims queue to see the updated risk score
5. Analysis completes in 1-3 seconds (NO LLM calls!)

To manually trigger fraud detection for a specific claim:
    python -c "import asyncio; from test_auto_fraud_detection import trigger_manual_fraud_detection; asyncio.run(trigger_manual_fraud_detection('CLM-2026-XXX'))"

📋 System Features:
- Uses structured form data only
- No OCR or document processing
- Fast analysis (1-3 seconds)
- Rule-based scoring (no API costs)
- Multiple fraud indicators
- Policy validation
- Claim history analysis
""")
