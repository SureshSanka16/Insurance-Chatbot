# 🧪 QUICK TEST & DEBUG GUIDE

## 🎯 How to Check Responses & Test Everything

### Method 1: Using the Web UI (EASIEST)

#### **Step 1: Login as User**
1. Open browser: http://localhost:3001
2. Click **"Login"** (top right)
3. Use credentials:
   - **Email:** user@example.com
   - **Password:** password123
   - OR register new account

#### **Step 2: Create a Test Claim**
1. Click **"Dashboard"**
2. Click **"File New Claim"** button
3. Fill the form:
   ```
   Policy: Select any policy
   Claimant Name: Test User
   Type: Health
   Amount: 40000
   Hospital: ABC Hospital
   Diagnosis: Cardiac Surgery
   Treatment: Heart surgery
   Doctor: Dr. Smith
   Admission Date: Today
   Discharge Date: Today
   ```
4. Click **"Submit Claim"**

#### **Step 3: Check as Admin**
1. Open **NEW BROWSER TAB/WINDOW** (keep user session)
2. Go to: http://localhost:3001
3. Click **"Login"**
4. Use admin credentials:
   - **Email:** admin@vantage.com
   - **Password:** admin123
5. Click **"Claims Queue"** in left sidebar

#### **Step 4: See the Results**

**IMMEDIATELY (within 1-2 seconds):**
```
┌────────────────────────────────────────────────────┐
│ CLM-2026-036  │  Test User  │  $40,000  │  🔄 IN PROGRESS  │
└────────────────────────────────────────────────────┘
```

**AFTER 2-3 seconds (REFRESH PAGE):**
```
┌────────────────────────────────────────────────────┐
│ CLM-2026-036  │  Test User  │  $40,000  │  45% ━━━━━━░░░░  │
└────────────────────────────────────────────────────┘
```

**CLICK ON THE CLAIM to see details:**
```
╔══════════════════════════════════════════════════════╗
║  CLAIM DETAILS - CLM-2026-036                        ║
╠══════════════════════════════════════════════════════╣
║  Claimant: Test User                                 ║
║  Amount: $40,000                                     ║
║  Type: Health                                        ║
║  Policy: POL-2026-XXX                                ║
║                                                      ║
║  🎯 FRAUD ANALYSIS                                   ║
║  Risk Score: 45/100                                  ║
║  Risk Level: MEDIUM                                  ║
║  Decision: MANUAL_REVIEW                             ║
║                                                      ║
║  🚩 Fraud Indicators:                                ║
║  • Claim amount is high (>70% of coverage)           ║
║  • Policy activated recently                         ║
║  • High-cost medical procedure                       ║
╚══════════════════════════════════════════════════════╝
```

---

### Method 2: Using API Testing Script (FOR DEVELOPERS)

Run the automated test:
```bash
cd server
python test_fraud_detection_workflow.py
```

Select option **2** for API testing.

The script will:
1. ✅ Check backend health
2. ✅ Login as admin
3. ✅ Fetch policies
4. ✅ Create test claim
5. ✅ Finalize claim (trigger fraud detection)
6. ✅ Show fraud analysis results

---

### Method 3: Using Browser DevTools (DEBUGGING)

#### **Check Frontend Requests:**

1. Open browser DevTools (F12)
2. Go to **Network** tab
3. Submit a claim
4. Look for these requests:

**Request 1: Create Claim**
```
POST http://127.0.0.1:8000/claims/
Status: 201 Created

Response:
{
  "id": "CLM-2026-036",
  "claimant_name": "Test User",
  "amount": 40000,
  "status": "NEW",
  "fraudStatus": "PENDING",  // <-- Should be PENDING initially
  "riskScore": null
}
```

**Request 2: Finalize Claim** (if documents uploaded)
```
POST http://127.0.0.1:8000/claims/CLM-2026-036/finalize
Status: 200 OK

Response:
{
  "message": "Claim finalized successfully",
  "fraud_status": "ANALYZING"  // <-- Fraud detection triggered
}
```

**Request 3: Get Claims (Admin)**
```
GET http://127.0.0.1:8000/claims
Status: 200 OK

Response:
[
  {
    "id": "CLM-2026-036",
    "fraudStatus": "COMPLETED",  // <-- After 2-3 seconds
    "riskScore": 45,
    "fraud_risk_level": "MEDIUM",
    "fraud_decision": "MANUAL_REVIEW",
    "fraud_indicators": [
      "Claim amount is high (>70% of coverage)",
      "High-cost medical procedure"
    ]
  }
]
```

#### **Check Backend Logs:**

Look at the terminal running the backend server. You should see:
```
[DEBUG] Creating claim for policy: POL-2026-XXX
[DEBUG] Claimant: Test User, Type: Health, Amount: 40000.0
INFO: 127.0.0.1:xxxxx - "POST /claims/ HTTP/1.1" 201 Created
[FRAUD] Starting fraud detection for claim CLM-2026-036
[FRAUD] Risk Score: 45, Decision: MANUAL_REVIEW
[FRAUD] Fraud detection completed for CLM-2026-036
```

---

### Method 4: Direct Database Check

Check the database to see fraud status:
```bash
cd server
python -c "
import sqlite3
conn = sqlite3.connect('vantage.db')
cursor = conn.cursor()
cursor.execute('SELECT id, claimant_name, amount, fraud_status, fraud_score, fraud_decision FROM claims ORDER BY created_at DESC LIMIT 5')
for row in cursor.fetchall():
    print(f'{row[0]} | {row[1]} | \${row[2]} | {row[3]} | Score:{row[4]} | {row[5]}')
conn.close()
"
```

Expected output:
```
CLM-2026-036 | Test User | $40000 | COMPLETED | Score:45 | MANUAL_REVIEW
```

---

## 🐛 Troubleshooting

### ❌ Problem: "IN PROGRESS" never changes

**Solution:**
1. Check backend terminal for errors
2. Refresh the admin page (Ctrl+R or F5)
3. Check if finalize endpoint was called:
   ```bash
   # In backend terminal, look for:
   POST /claims/{claim_id}/finalize
   ```

### ❌ Problem: Claims not showing in admin queue

**Solution:**
1. Make sure you're logged in as admin (admin@vantage.com)
2. Check browser console (F12) for errors
3. Verify backend is running: http://127.0.0.1:8000/docs

### ❌ Problem: Risk score is NULL

**Solution:**
1. Check if fraud_status is still "PENDING" or "ANALYZING"
2. Wait 2-3 seconds and refresh
3. Check backend logs for fraud detection errors

### ❌ Problem: Cannot submit claim

**Solution:**
1. Clear old claims: `python server/clear_claims.py`
2. Check browser console for network errors
3. Verify backend is running on port 8000

---

## 📊 Expected Test Results

### Test Case 1: LOW RISK
```
Policy Age: 1+ year
Amount: $5,000
Expected Score: 0-29 (GREEN)
Expected Decision: AUTO_APPROVE
```

### Test Case 2: MEDIUM RISK
```
Policy Age: 2-3 months
Amount: $40,000
Expected Score: 40-60 (YELLOW)
Expected Decision: MANUAL_REVIEW
```

### Test Case 3: HIGH RISK
```
Policy Age: < 30 days
Amount: $100,000 (exceeds coverage)
Expected Score: 75+ (RED)
Expected Decision: FRAUD_ALERT
```

---

## 🎯 What You Should See

### User Dashboard:
- ✅ List of your policies
- ✅ "File New Claim" button
- ✅ Claim submission form
- ✅ Success message after submission

### Admin Claims Queue:
- ✅ All submitted claims listed
- ✅ "🔄 IN PROGRESS" for analyzing claims
- ✅ Risk score bar (0-100%) with colors
- ✅ Claim details on click

### Admin Claim Details:
- ✅ All claim information
- ✅ Fraud analysis section
- ✅ Risk score with visual bar
- ✅ List of fraud indicators
- ✅ Decision recommendation
- ✅ Formatted structured data

---

## 🚀 Quick Start Commands

```bash
# Clear old test data
cd server
python clear_claims.py

# Run automated test
python test_fraud_detection_workflow.py

# Check last 5 claims in database
python -c "
import sqlite3
conn = sqlite3.connect('vantage.db')
cursor = conn.cursor()
cursor.execute('SELECT id, claimant_name, fraud_status, fraud_score FROM claims ORDER BY created_at DESC LIMIT 5')
print('Recent Claims:')
for row in cursor.fetchall():
    print(f'  {row[0]} | {row[1]} | {row[2]} | Score: {row[3]}')
conn.close()
"
```

---

**📧 Need Help?**
If you're still having issues, check:
1. Backend terminal for error messages
2. Browser console (F12) for frontend errors
3. Network tab to see API responses
