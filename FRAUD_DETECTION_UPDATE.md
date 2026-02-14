# 🔄 Updated Fraud Detection Workflow

## ✅ Changes Made

The fraud detection system has been updated to properly handle the document upload flow where users upload **all documents during claim submission**.

---

## 📋 New Workflow

### **User Perspective:**
1. User fills out claim form in the wizard
2. User uploads required documents (Death Certificate, ID Proof, etc.)
3. User clicks "Submit"
4. System shows "Claim submitted successfully"

### **System Flow:**
1. **Frontend** creates claim via `POST /claims`
   - Backend sets `fraud_status = PENDING`
   - Backend sets `risk_score = NULL`
   - Claim appears in Admin Queue as **"📋 IN REVIEW"**

2. **Frontend** uploads all documents in parallel
   - Multiple `POST /claims/{id}/documents` calls
   - Backend saves documents but does NOT trigger fraud detection yet

3. **Frontend** finalizes claim after all uploads
   - Calls `POST /claims/{id}/finalize`
   - Backend triggers fraud detection in background
   - `fraud_status` changes to `ANALYZING`

4. **Background Agent** analyzes fraud
   - Extracts claim data
   - Queries user history
   - Gets RAG context
   - Runs LLM analysis
   - Updates `risk_score` and `fraud_status = COMPLETED`

5. **Admin** sees updated risk score
   - Refresh Claims Queue
   - Status changes from "⏳ ANALYZING..." to **Risk Score %**

---

## 🔧 Technical Changes

### **Backend Changes:**

#### `server/routers/claims.py`
1. **Removed** fraud detection trigger from `upload_document()`
2. **Added** new endpoint: `POST /claims/{claim_id}/finalize`
   - Triggers fraud detection after all documents uploaded
   - Only triggers if claim is still `PENDING`
   - Returns status message

**New Endpoint:**
```python
@router.post("/{claim_id}/finalize", status_code=status.HTTP_202_ACCEPTED)
async def finalize_claim(claim_id: str, ...):
    """
    Finalize claim submission after all documents are uploaded.
    This triggers the fraud detection analysis.
    """
    # ... authorization checks ...
    
    if claim.fraud_status == FraudStatus.PENDING:
        # Trigger background fraud detection
        background_tasks.add_task(run_fraud_detection_background, claim_id)
        
        return {
            "message": "Claim finalized, fraud detection started",
            "claim_id": claim_id,
            "fraud_status": "ANALYZING"
        }
```

### **Frontend Changes:**

#### `src/api/endpoints.ts`
**Added** new API function:
```typescript
export const finalizeClaim = async (claimId: string): Promise<any> => {
    const response = await apiClient.post<any>(`/claims/${claimId}/finalize`);
    return response.data;
};
```

#### `views/UserDashboard.tsx`
**Updated** claim submission flow:
```typescript
// 1. Create claim
const newClaim = await createClaim(claimPayload);

// 2. Upload all documents in parallel
await Promise.all(uploadPromises);

// 3. Finalize claim to trigger fraud detection (NEW!)
await finalizeClaim(newClaim.id);
```

---

## 🎯 Why This Change?

### **Previous Behavior:**
- Fraud detection triggered on **first document upload**
- Analysis could start before all documents were uploaded
- Incomplete data could lead to inaccurate fraud scores

### **New Behavior:**
- Fraud detection triggers **after ALL documents uploaded**
- Analysis has complete information
- More accurate fraud detection results
- Cleaner separation of concerns

---

## 🧪 Testing

### **Test Case 1: Normal Flow**
1. Login as User
2. Submit Life Insurance claim with all 5 documents:
   - Death Certificate
   - ID Proof
   - Policy Document
   - Medical Records
   - Bank Proof
3. Submit claim

**Expected:**
- All documents upload successfully
- Claim is finalized automatically
- Admin sees "IN REVIEW" → "ANALYZING" → Risk Score

### **Test Case 2: Partial Upload**
1. Submit claim
2. Upload only 2 out of 5 documents
3. Close modal without completing

**Expected:**
- Documents are saved
- Claim remains in `PENDING` state
- Fraud detection does NOT run
- Admin sees "IN REVIEW" (waiting for finalization)

### **Test Case 3: Manual Finalization**
If user later uploads remaining documents:
```bash
# Manually finalize via API
curl -X POST http://localhost:8000/claims/CLM-2026-001/finalize \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📊 API Reference

### **Finalize Claim**
```
POST /claims/{claim_id}/finalize
```

**Request:**
- Headers: `Authorization: Bearer <JWT>`
- Path: `claim_id` (string)

**Response:**
```json
{
  "message": "Claim finalized, fraud detection started",
  "claim_id": "CLM-2026-001",
  "fraud_status": "ANALYZING"
}
```

**Or if already finalized:**
```json
{
  "message": "Claim already finalized",
  "claim_id": "CLM-2026-001",
  "fraud_status": "COMPLETED"
}
```

**Errors:**
- `404` - Claim not found
- `403` - Not authorized to finalize this claim

---

## 🔍 Monitoring

### **Backend Logs:**
```
[DOCUMENT-UPLOAD] Document 'death_cert.pdf' uploaded for claim CLM-2026-001
[DOCUMENT-UPLOAD] Document 'id_proof.pdf' uploaded for claim CLM-2026-001
[CLAIM-FINALIZE] Claim CLM-2026-001 finalized, triggering fraud detection
[FRAUD-DETECTION] Starting background analysis for claim CLM-2026-001
[FRAUD-DETECTION] Claim CLM-2026-001 status: ANALYZING
[FRAUD-DETECTION] ✅ Completed for claim CLM-2026-001 - Score: 45, Level: MEDIUM
```

### **Frontend Console:**
```
Uploading deathCertificate...
Uploaded deathCertificate
Uploading nomineeIdProof...
Uploaded nomineeIdProof
All documents uploaded successfully
Finalizing claim and triggering fraud detection...
Claim finalized, fraud detection started
```

---

## ✨ Benefits

1. **Accuracy**: Fraud detection has all documents before analyzing
2. **Performance**: No duplicate analysis triggers during parallel uploads
3. **Control**: Explicit finalization step allows for future enhancements
4. **Flexibility**: Can add validation/business logic before finalization
5. **Testing**: Easier to test with clear separation between upload and analysis

---

## 🚀 Deployment

No database migration needed - the finalize endpoint uses existing fields.

**To deploy:**
1. Restart backend: `python -m uvicorn main:app --reload`
2. Restart frontend: `npm run dev`
3. Test with new claim submission

---

## 📝 Future Enhancements

Potential improvements:
1. Add document validation before finalization
2. Allow manual re-finalization if documents are updated
3. Add webhook for real-time updates to admin UI
4. Track finalization timestamp in database
5. Add progress indicator during document uploads

---

**Status: ✅ IMPLEMENTED AND READY FOR TESTING**
