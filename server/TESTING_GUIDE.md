# Quick Test Guide - Fraud Detection System

## Method 1: Run Automated Test Script (Recommended)

This will test all 3 components: OCR → Field Extraction → Fraud Analysis

```bash
cd server
python test_fraud_detection.py
```

**What it tests:**
- ✅ TrOCR extracts text from a fake hospital bill
- ✅ LLM converts text to structured JSON
- ✅ Fraud analysis with database + RAG context

**Expected output:**
```
TEST 1: OCR Service (TrOCR)
✅ OCR Success! Extracted 250 characters

TEST 2: Field Extraction Service (LLM)
✅ Field Extraction Success!
  • claim_amount: 150000
  • hospital_name: City Hospital
  • diagnosis: Appendicitis

TEST 3: Fraud Detection Service (LLM + RAG)
✅ Fraud Analysis Complete!
Fraud Score: 45/100
Risk Level: MEDIUM
Decision: MANUAL_REVIEW
```

---

## Method 2: Test via API (Postman/cURL)

### Step 1: Create a Test Claim
```bash
POST http://localhost:8000/claims
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "policy_number": "POL-2026-H85",
  "claimant_name": "John Doe",
  "type": "Health",
  "amount": 150000,
  "description": "Appendicitis surgery",
  "submission_date": "2026-02-14T00:00:00Z"
}
```

Response: `{ "id": "CLM-2026-001", ... }`

### Step 2: Upload Documents
```bash
POST http://localhost:8000/documents/upload
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: multipart/form-data

file: hospital_bill.pdf
claim_id: CLM-2026-001
category: Medical
```

Response: `{ "id": "doc-uuid-123", ... }`

### Step 3: Analyze for Fraud
```bash
POST http://localhost:8000/ai/analyze-claim-fraud
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "claim_id": "CLM-2026-001",
  "document_ids": ["doc-uuid-123"]
}
```

Response:
```json
{
  "claim_id": "CLM-2026-001",
  "fraud_score": 35,
  "risk_level": "LOW",
  "decision": "AUTO_APPROVE",
  "extracted_fields": {
    "claim_amount": 150000,
    "hospital_name": "Apollo Hospital",
    "diagnosis": "Appendicitis"
  },
  "fraud_indicators": [],
  "reasoning": "This claim appears legitimate...",
  "processing_time_ms": 4523
}
```

---

## Method 3: Test Individual Components

### Test OCR Only
```python
cd server
python -c "
from services.ocr_service import extract_text_from_document
import open('test_bill.pdf', 'rb') as f:
    text = extract_text_from_document(f.read(), 'application/pdf')
    print('Extracted:', text[:200])
"
```

### Test Field Extraction Only
```python
python -c "
from services.field_extraction_service import extract_fields_from_text
text = 'Hospital: Apollo, Amount: 50000, Diagnosis: Fever'
fields = extract_fields_from_text(text, 'Health')
print('Fields:', fields)
"
```

---

## Method 4: Check API Documentation

Visit the interactive API docs:
```
http://localhost:8000/docs
```

Look for:
- **POST /ai/analyze-claim-fraud** - Try it out directly in the browser!

---

## Troubleshooting

### Issue: "TrOCR model not found"
**Solution**: Install dependencies
```bash
pip install transformers torch pdf2image Pillow
```

### Issue: "No users found in database"
**Solution**: Create a test user via the UI or API first

### Issue: "OpenRouter API error"
**Solution**: Check your `.env` file has `OPENROUTER_API_KEY`

---

## Quick Verification Checklist

- [ ] Server running on port 8000
- [ ] Database has fraud columns (`fraud_score`, `fraud_risk_level`, etc.)
- [ ] Dependencies installed (transformers, torch, pdf2image, Pillow)
- [ ] Environment variables set (OPENROUTER_API_KEY, GEMINI_API_KEY)
- [ ] At least one user and policy in database

---

## Expected Performance

| Component | Time |
|-----------|------|
| OCR (1 page) | 2-3s |
| Field Extraction | 3-4s |
| Fraud Analysis | 2-3s |
| **Total** | **7-10s** |

---

## Next Steps After Testing

1. ✅ If tests pass → System is working!
2. 🎨 Integrate with frontend UI (add "Analyze for Fraud" button)
3. 🤖 Auto-trigger fraud analysis on claim submission
4. 📊 Display fraud results in claims dashboard
