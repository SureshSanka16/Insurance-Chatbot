"""
Test script for fraud detection system
Run this to verify the fraud detection pipeline is working correctly.
"""
import asyncio
import sys
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from database import get_db
from models import Claim, Document, Policy, User
from services.ocr_service import extract_text_from_document
from services.field_extraction_service import extract_fields_from_text
from services.fraud_detection_service import analyze_claim_fraud
from sqlalchemy import select


async def create_test_document():
    """Create a fake hospital bill image for testing"""
    print("📄 Creating test hospital bill image...")
    
    # Create a simple image with text (simulating a hospital bill)
    img = Image.new('RGB', (800, 1000), color='white')
    draw = ImageDraw.Draw(img)
    
    # Add text content
    text_content = """
    CITY HOSPITAL
    Invoice No: INV-2026-001
    Date: 2026-02-10
    
    Patient Name: John Doe
    Policy Number: POL-2026-H85
    
    MEDICAL BILL
    
    Diagnosis: Appendicitis
    Treatment: Appendectomy Surgery
    
    Doctor: Dr. Smith
    Admission Date: 2026-02-10
    Discharge Date: 2026-02-14
    
    Room Charges: ₹20,000
    Surgery Charges: ₹80,000
    Medicines: ₹15,000
    Doctor Fees: ₹35,000
    
    TOTAL AMOUNT: ₹150,000
    """
    
    y_position = 50
    for line in text_content.strip().split('\n'):
        draw.text((50, y_position), line.strip(), fill='black')
        y_position += 30
    
    # Save to bytes
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes.getvalue()


async def test_ocr_service():
    """Test 1: OCR Text Extraction"""
    print("\n" + "="*60)
    print("TEST 1: OCR Service (TrOCR)")
    print("="*60)
    
    # Create test document
    doc_bytes = await create_test_document()
    
    print("✓ Test document created (800x1000 PNG)")
    print("⏳ Running TrOCR extraction...")
    
    try:
        extracted_text = extract_text_from_document(doc_bytes, "image/png")
        print(f"✅ OCR Success! Extracted {len(extracted_text)} characters")
        print(f"\nExtracted Text Preview:\n{extracted_text[:200]}...")
        return extracted_text
    except Exception as e:
        print(f"❌ OCR Failed: {e}")
        return None


async def test_field_extraction(ocr_text):
    """Test 2: LLM Field Extraction"""
    print("\n" + "="*60)
    print("TEST 2: Field Extraction Service (LLM)")
    print("="*60)
    
    if not ocr_text:
        print("⚠️  Skipping (no OCR text available)")
        return None
    
    print("⏳ Extracting structured fields using LLM...")
    
    try:
        fields = extract_fields_from_text(ocr_text, "Health")
        print("✅ Field Extraction Success!")
        print(f"\nExtracted Fields:")
        for key, value in fields.items():
            print(f"  • {key}: {value}")
        return fields
    except Exception as e:
        print(f"❌ Field Extraction Failed: {e}")
        return None


async def test_fraud_detection(extracted_fields):
    """Test 3: Fraud Detection Analysis"""
    print("\n" + "="*60)
    print("TEST 3: Fraud Detection Service (LLM + RAG)")
    print("="*60)
    
    if not extracted_fields:
        print("⚠️  Skipping (no extracted fields available)")
        return
    
    print("⏳ Analyzing fraud risk...")
    
    # Get database session
    async for db in get_db():
        try:
            # Get a test user (first user in database)
            result = await db.execute(select(User).limit(1))
            user = result.scalar_one_or_none()
            
            if not user:
                print("❌ No users found in database. Please create a user first.")
                return
            
            # Get a test policy
            result = await db.execute(
                select(Policy).where(Policy.user_id == user.id).limit(1)
            )
            policy = result.scalar_one_or_none()
            
            if not policy:
                print("❌ No policies found. Please create a policy first.")
                return
            
            print(f"✓ Using test user: {user.email}")
            print(f"✓ Using test policy: {policy.policy_number}")
            
            # Run fraud analysis
            fraud_result = await analyze_claim_fraud(
                extracted_fields=extracted_fields,
                claim_category="Health",
                user_id=user.id,
                policy_number=policy.policy_number,
                db=db
            )
            
            print("\n✅ Fraud Analysis Complete!")
            print("\n" + "-"*60)
            print("FRAUD ANALYSIS RESULTS")
            print("-"*60)
            print(f"Fraud Score: {fraud_result['fraud_score']}/100")
            print(f"Risk Level: {fraud_result['risk_level']}")
            print(f"Decision: {fraud_result['decision']}")
            print(f"Confidence: {fraud_result.get('confidence', 'N/A')}")
            
            if fraud_result.get('fraud_indicators'):
                print(f"\nFraud Indicators ({len(fraud_result['fraud_indicators'])}):")
                for indicator in fraud_result['fraud_indicators']:
                    print(f"  ⚠️  {indicator}")
            else:
                print("\n✓ No fraud indicators detected")
            
            print(f"\nReasoning:\n{fraud_result['reasoning']}")
            print("-"*60)
            
        except Exception as e:
            print(f"❌ Fraud Detection Failed: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Run all tests"""
    print("\n" + "🔍 FRAUD DETECTION SYSTEM TEST SUITE 🔍".center(60))
    print("="*60)
    
    # Test 1: OCR
    ocr_text = await test_ocr_service()
    
    # Test 2: Field Extraction
    extracted_fields = await test_field_extraction(ocr_text)
    
    # Test 3: Fraud Detection
    await test_fraud_detection(extracted_fields)
    
    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETED")
    print("="*60)
    print("\nNext Steps:")
    print("1. If all tests passed, the fraud detection system is working!")
    print("2. Test via API: POST /ai/analyze-claim-fraud")
    print("3. Check the installation guide for more details")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
