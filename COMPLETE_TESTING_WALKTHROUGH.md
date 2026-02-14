# 🎯 COMPLETE TESTING WALKTHROUGH

## ✅ System Status: READY

**Backend:** Running on http://127.0.0.1:8000  
**Frontend:** Running on http://localhost:3001  
**Database:** Configured with fraud_status column  
**Fraud Detection:** Active (rule-based, 1-3 seconds)  

---

## 📺 VISUAL STEP-BY-STEP GUIDE

### 🔵 STEP 1: Test as USER (Submit Claim)

1. **Open Browser**
   ```
   http://localhost:3001
   ```

2. **Login as User**
   - Click **"Login"** (top right)
   - Email: `user@example.com`
   - Password: `password123`
   - (or register a new account)

3. **Go to Dashboard**
   - After login, click **"Dashboard"** in the side menu
   - You should see your active policies listed

4. **Click "File New Claim"**
   - Big button at the top of Dashboard
   - A modal/form will appear

5. **Fill Claim Form:**
   ```
   Policy: [Select any policy from dropdown]
   
   Claimant Name: Test User
   
   Type: Health
   
   Amount: 40000
   
   Description: Test claim for fraud detection system
   
   === Health Information ===
   Hospital Name: ABC Medical Center
   Diagnosis: Cardiac Surgery
   Treatment Details: Heart bypass surgery
   Doctor Name: Dr. Smith
   Admission Date: 2026-02-14
   Discharge Date: 2026-02-14
   ```

6. **Upload Documents (Optional)**
   - You can upload any PDF or image
   - Or skip this step
   - Documents are stored but NOT processed

7. **Click "Submit Claim"**
   - Wait for success message
   - Claim is now created with `fraud_status = PENDING`
   - Fraud detection automatically triggered

---

### 🔴 STEP 2: Test as ADMIN (View Results)

1. **Open NEW Browser Tab**
   - Keep user session open
   - Or use private/incognito window

2. **Go to Same URL**
   ```
   http://localhost:3001
   ```

3. **Login as Admin**
   - Click **"Login"**
   - Email: `admin@vantage.com`
   - Password: `admin123`

4. **Click "Claims Queue"**
   - In the left sidebar
   - You should see all submitted claims

5. **Check Fraud Status - IMMEDIATELY AFTER SUBMISSION**

   You should see:
   ```
   ┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
   ┃ Claim ID      ┃ Claimant   ┃ Amount    ┃ Status            ┃
   ┣━━━━━━━━━━━━━━━╋━━━━━━━━━━━━╋━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━┫
   ┃ CLM-2026-036  ┃ Test User  ┃ $40,000   ┃ 🔄 IN PROGRESS    ┃
   ┗━━━━━━━━━━━━━━━┻━━━━━━━━━━━━┻━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━┛
   ```
   
   **Blue animated badge** = Fraud analysis is running

6. **Refresh Page After 2-3 Seconds**
   - Press F5 or Ctrl+R
   - Or wait and refresh

7. **Check Fraud Status - AFTER ANALYSIS**

   You should now see:
   ```
   ┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
   ┃ Claim ID      ┃ Claimant   ┃ Amount    ┃ Risk Score        ┃
   ┣━━━━━━━━━━━━━━━╋━━━━━━━━━━━━╋━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━┫
   ┃ CLM-2026-036  ┃ Test User  ┃ $40,000   ┃ 45% ━━━━━━░░░░░░  ┃
   ┗━━━━━━━━━━━━━━━┻━━━━━━━━━━━━┻━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━┛
   ```
   
   **Color-coded bar:**
   - 🟢 Green (0-29%) = Low Risk
   - 🟡 Yellow (30-49%) = Medium Risk
   - 🟠 Amber (50-74%) = Medium-High Risk
   - 🔴 Red (75-100%) = High Risk

8. **Click on Claim to View Details**
   
   You should see:
   ```
   ╔══════════════════════════════════════════════════════════╗
   ║  CLAIM DETAILS - CLM-2026-036                            ║
   ╠══════════════════════════════════════════════════════════╣
   ║                                                          ║
   ║  📋 BASIC INFORMATION                                    ║
   ║  ─────────────────────────────────────────               ║
   ║  Claimant: Test User                                     ║
   ║  Amount: $40,000                                         ║
   ║  Type: Health                                            ║
   ║  Policy: POL-2026-XXX                                    ║
   ║  Status: NEW                                             ║
   ║                                                          ║
   ║  🏥 HEALTH INFORMATION                                   ║
   ║  ─────────────────────────────────────────               ║
   ║  Hospital: ABC Medical Center                            ║
   ║  Diagnosis: Cardiac Surgery                              ║
   ║  Treatment: Heart bypass surgery                         ║
   ║  Doctor: Dr. Smith                                       ║
   ║  Admission: 2026-02-14                                   ║
   ║  Discharge: 2026-02-14                                   ║
   ║                                                          ║
   ║  🎯 FRAUD ANALYSIS                                       ║
   ║  ─────────────────────────────────────────               ║
   ║  Risk Score: 45/100                                      ║
   ║  Risk Level: MEDIUM                                      ║
   ║  Decision: MANUAL_REVIEW                                 ║
   ║                                                          ║
   ║  🚩 Fraud Indicators:                                    ║
   ║  • Claim amount is high (>70% of coverage)               ║
   ║  • Policy activated recently                             ║
   ║  • High-cost medical procedure                           ║
   ║                                                          ║
   ║  💡 Recommendation: Review this claim manually           ║
   ║                                                          ║
   ╚══════════════════════════════════════════════════════════╝
   ```

---

## 🧪 TESTING DIFFERENT RISK LEVELS

### Test Case 1: LOW RISK (0-29%)
```
Policy: Choose a policy that's 1+ year old
Amount: $5,000
Result: 🟢 Green bar, AUTO_APPROVE decision
```

### Test Case 2: MEDIUM RISK (30-59%)
```
Policy: Choose a policy that's 2-3 months old
Amount: $40,000
Result: 🟡 Yellow bar, MANUAL_REVIEW decision
```

### Test Case 3: HIGH RISK (75-100%)
```
Policy: Choose a policy that's < 30 days old
Amount: $100,000 (exceeds coverage)
Result: 🔴 Red bar, FRAUD_ALERT decision
```

---

## 🐛 CHECKING RESPONSES IN BROWSER

### Open Developer Tools (F12)

1. **Network Tab**
   - Click **Network** tab in DevTools
   - Submit a claim
   - Look for these requests:

   **POST /claims/**
   ```json
   Status: 201 Created
   
   Response:
   {
     "id": "CLM-2026-036",
     "claimant_name": "Test User",
     "amount": 40000,
     "status": "NEW",
     "fraudStatus": "PENDING",  ← Initially PENDING
     "riskScore": null          ← Initially NULL
   }
   ```

   **POST /claims/{id}/finalize**
   ```json
   Status: 200 OK
   
   Response:
   {
     "message": "Claim finalized successfully",
     "fraud_status": "ANALYZING"  ← Analysis started
   }
   ```

   **GET /claims/**
   ```json
   Status: 200 OK
   
   Response:
   [
     {
       "id": "CLM-2026-036",
       "fraudStatus": "COMPLETED",  ← Analysis done
       "riskScore": 45,             ← Risk score calculated
       "fraud_risk_level": "MEDIUM",
       "fraud_decision": "MANUAL_REVIEW",
       "fraud_indicators": [
         "Claim amount is high (>70% of coverage)",
         "High-cost medical procedure"
       ]
     }
   ]
   ```

2. **Console Tab**
   - Check for any errors (red messages)
   - Should see no errors if working correctly

---

## 📊 CHECKING BACKEND RESPONSES

### View Backend Terminal Logs

Look at the terminal running the backend. You should see:

```
[DEBUG] Creating claim for policy: POL-2026-XXX
[DEBUG] Claimant: Test User, Type: Health, Amount: 40000.0
INFO: 127.0.0.1:xxxxx - "POST /claims/ HTTP/1.1" 201 Created

[FRAUD] Starting fraud detection for claim CLM-2026-036
[FRAUD] Extracted fields from claim
[FRAUD] Retrieved policy information
[FRAUD] Checking fraud indicators...
[FRAUD] Risk Score: 45, Decision: MANUAL_REVIEW
[FRAUD] Fraud detection completed for CLM-2026-036
INFO: 127.0.0.1:xxxxx - "POST /claims/CLM-2026-036/finalize HTTP/1.1" 200 OK
```

---

## 🛠️ QUICK COMMANDS

### Check System Status
```bash
cd server
python check_status.py
```

Output shows:
- ✅ Backend running status
- ✅ Database status
- 📊 Recent claims with fraud status
- 📈 Statistics

### Run Automated Test
```bash
cd server
python test_fraud_detection_workflow.py
```
- Choose option **2** for automated API testing
- See complete workflow with responses

### Clear Test Data
```bash
cd server
python clear_claims.py
```
- Removes all claims and documents
- Start fresh for testing

### Check Database Directly
```bash
cd server
python -c "
import sqlite3
conn = sqlite3.connect('vantage.db')
cursor = conn.cursor()
cursor.execute('''
    SELECT id, claimant_name, amount, fraud_status, fraud_score, fraud_decision 
    FROM claims 
    ORDER BY created_at DESC 
    LIMIT 5
''')
print('Recent Claims:')
for row in cursor.fetchall():
    print(f'  {row[0]} | {row[1]} | ${row[2]} | {row[3]} | Score: {row[4]} | {row[5]}')
conn.close()
"
```

---

## 📱 WHAT YOU SHOULD SEE

### ✅ Success Indicators:

1. **User Dashboard:**
   - Policies load successfully
   - Can open claim form
   - Form submits without errors
   - Success message appears

2. **Admin Claims Queue:**
   - Shows "🔄 IN PROGRESS" immediately
   - Shows risk score after 2-3 seconds
   - Color-coded risk bar displays

3. **Admin Claim Details:**
   - All claim data displays
   - Fraud analysis section visible
   - Risk score with visual bar
   - List of fraud indicators
   - Decision recommendation

4. **Backend Terminal:**
   - No error messages
   - Shows "[FRAUD]" log messages
   - Returns 200/201 status codes

---

## ❌ Troubleshooting

### Problem: "IN PROGRESS" never changes
**Solution:**
- Wait 3-5 seconds
- Refresh page (F5)
- Check backend terminal for errors
- Run: `python check_status.py`

### Problem: Network error when submitting
**Solution:**
- Backend not running: `python -m uvicorn main:app --reload --port 8000`
- Check browser console (F12) for error details

### Problem: Claims not showing in admin
**Solution:**
- Make sure logged in as admin (admin@vantage.com)
- Check network tab for API errors
- Verify backend running on port 8000

### Problem: Risk score shows NULL
**Solution:**
- Wait for analysis to complete (2-3 seconds)
- Check fraud_status field (should be COMPLETED)
- Run: `python check_status.py` to see database status

---

## 🎉 EXPECTED RESULTS

After following this guide, you should be able to:

✅ Submit claims as a user  
✅ See "IN PROGRESS" status in admin queue  
✅ See risk score appear after 2-3 seconds  
✅ View detailed fraud analysis  
✅ See color-coded risk indicators  
✅ Review fraud indicators list  
✅ Understand decision recommendations  

---

**📧 Need More Help?**

Review these files:
- `QUICK_TEST_GUIDE.md` - Quick reference
- `SIMPLIFIED_FRAUD_DETECTION_FINAL.md` - Complete documentation
- `server/test_fraud_detection_workflow.py` - Automated testing
- `server/check_status.py` - System status checker

**System is ready for testing! 🚀**
