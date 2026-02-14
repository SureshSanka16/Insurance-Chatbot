"""
🧪 COMPREHENSIVE TESTING GUIDE FOR FRAUD DETECTION SYSTEM
==========================================================

This script will help you test the complete fraud detection workflow.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://localhost:3001"

print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                   FRAUD DETECTION TESTING GUIDE                          ║
╚══════════════════════════════════════════════════════════════════════════╝

📋 TESTING WORKFLOW:
-------------------

STEP 1: Login as User
   → Go to: {FRONTEND_URL}
   → Click "Login" (top right)
   → Use existing account or register new one
   
STEP 2: Go to User Dashboard
   → Click "Dashboard" after login
   → You should see your active policies
   
STEP 3: Submit a New Claim
   → Click "File New Claim" button
   → Fill out the claim form with test data:
   
   Example Test Cases:
   
   🟢 LOW RISK CLAIM (Score < 30):
      - Select a policy that's 1+ year old
      - Amount: $5,000 (small amount)
      - Claimant: "John Doe"
      - Type: Health
      - Hospital: "City Hospital"
      - Diagnosis: "Minor Surgery"
      - Treatment: "Outpatient procedure"
      - Doctor: "Dr. Smith"
      
   🟡 MEDIUM RISK CLAIM (Score 40-60):
      - Select a policy that's 2-3 months old
      - Amount: $40,000 (high but not exceeding limit)
      - Claimant: "Jane Doe"
      - Type: Health
      - Hospital: "ABC Medical Center"
      - Diagnosis: "Cardiac Surgery"
      - Treatment: "Heart bypass surgery"
      - Doctor: "Dr. Johnson"
      
   🔴 HIGH RISK CLAIM (Score > 75):
      - Select a policy that's < 30 days old
      - Amount: $100,000 (exceeds typical coverage)
      - Claimant: "Test User"
      - Type: Health
      - Hospital: "XYZ Hospital"
      - Diagnosis: "Complex Surgery"
      - Treatment: "Emergency procedure"
      - Doctor: "Dr. Williams"

STEP 4: Upload Documents (Optional)
   → Upload any test PDF/image files
   → Click "Upload" for each document
   → Documents are stored but NOT processed (as per design)

STEP 5: Submit Claim
   → Click "Submit Claim" button
   → System will:
     a) Create claim with fraud_status = PENDING
     b) Trigger finalizeClaim() automatically
     c) Run rule-based fraud detection in background
     d) Update fraud_status = COMPLETED with risk_score

STEP 6: View as Admin
   → Open new browser tab/window
   → Go to: {FRONTEND_URL}
   → Login as Admin:
      Email: admin@vantage.com
      Password: admin123
   
   → Click "Claims Queue" in sidebar
   → You should see your test claim

STEP 7: Check Fraud Status
   
   Immediately after submission, you'll see:
   ┌─────────────────────────────────────┐
   │ CLM-2026-XXX │ 🔄 IN PROGRESS       │
   └─────────────────────────────────────┘
   
   After 1-3 seconds (refresh page), you'll see:
   ┌─────────────────────────────────────┐
   │ CLM-2026-XXX │ 45% ━━━━━━░░░░░ 🟡  │
   └─────────────────────────────────────┘

STEP 8: View Claim Details
   → Click on the claim in admin queue
   → You should see:
     ✅ Claim information (claimant, amount, policy)
     ✅ Risk score with color-coded bar
     ✅ Fraud indicators list
     ✅ Decision recommendation (AUTO_APPROVE, MANUAL_REVIEW, FRAUD_ALERT)
     ✅ All structured data formatted nicely

═══════════════════════════════════════════════════════════════════════════

🧪 API TESTING (Alternative - for developers)
============================================

You can also test via API directly using the functions below.
""".format(FRONTEND_URL=FRONTEND_URL))

def test_health_check():
    """Test if backend is running"""
    print("\n[TEST 1] Checking backend health...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ Backend is running!")
            return True
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend not reachable: {e}")
        return False

def test_login(email="admin@vantage.com", password="admin123"):
    """Test login and get token"""
    print(f"\n[TEST 2] Logging in as {email}...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={"username": email, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"✅ Login successful! Token: {token[:20]}...")
            return token
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_get_policies(token):
    """Get available policies"""
    print("\n[TEST 3] Fetching policies...")
    try:
        response = requests.get(
            f"{BASE_URL}/policies",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            policies = response.json()
            print(f"✅ Found {len(policies)} policies")
            if policies:
                print(f"   First policy: {policies[0].get('policy_number')} - {policies[0].get('title')}")
                return policies[0].get('policy_number')
            return None
        else:
            print(f"❌ Failed to fetch policies: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_create_claim(token, policy_number, test_case="MEDIUM"):
    """Create a test claim"""
    print(f"\n[TEST 4] Creating {test_case} risk claim...")
    
    # Test case configurations
    if test_case == "LOW":
        amount = 5000
        claimant = "John Doe - Low Risk"
    elif test_case == "MEDIUM":
        amount = 40000
        claimant = "Jane Doe - Medium Risk"
    else:  # HIGH
        amount = 100000
        claimant = "Test User - High Risk"
    
    claim_data = {
        "policy_number": policy_number,
        "claimant_name": claimant,
        "type": "Health",
        "amount": amount,
        "description": f"Test claim for fraud detection - {test_case} risk scenario",
        "health_info": {
            "hospital_name": "ABC Medical Center",
            "diagnosis": "Cardiac Surgery",
            "treatment_details": "Heart surgery procedure",
            "doctor_name": "Dr. Smith",
            "admission_date": datetime.now().strftime("%Y-%m-%d"),
            "discharge_date": datetime.now().strftime("%Y-%m-%d")
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/claims/",
            json=claim_data,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 201:
            claim = response.json()
            claim_id = claim.get("id")
            print(f"✅ Claim created: {claim_id}")
            print(f"   Status: {claim.get('status')}")
            print(f"   Fraud Status: {claim.get('fraudStatus', 'PENDING')}")
            return claim_id
        else:
            print(f"❌ Failed to create claim: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_finalize_claim(token, claim_id):
    """Finalize claim to trigger fraud detection"""
    print(f"\n[TEST 5] Finalizing claim {claim_id} (triggering fraud detection)...")
    try:
        response = requests.post(
            f"{BASE_URL}/claims/{claim_id}/finalize",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Claim finalized!")
            print(f"   Message: {result.get('message')}")
            print(f"   Fraud Status: {result.get('fraud_status')}")
            return True
        else:
            print(f"❌ Failed to finalize: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_get_claim_details(token, claim_id):
    """Get claim details including fraud analysis"""
    print(f"\n[TEST 6] Fetching claim details...")
    try:
        # Wait a bit for fraud detection to complete
        print("   ⏳ Waiting 3 seconds for fraud analysis to complete...")
        time.sleep(3)
        
        response = requests.get(
            f"{BASE_URL}/claims/{claim_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            claim = response.json()
            print(f"✅ Claim details retrieved!")
            print(f"\n   📊 FRAUD ANALYSIS RESULTS:")
            print(f"   ─────────────────────────────────────")
            print(f"   Claim ID: {claim.get('id')}")
            print(f"   Claimant: {claim.get('claimant_name')}")
            print(f"   Amount: ${claim.get('amount'):,.2f}")
            print(f"   Status: {claim.get('status')}")
            print(f"   Fraud Status: {claim.get('fraudStatus', 'N/A')}")
            print(f"   Risk Score: {claim.get('riskScore', 'N/A')}")
            print(f"   Risk Level: {claim.get('fraud_risk_level', 'N/A')}")
            print(f"   Decision: {claim.get('fraud_decision', 'N/A')}")
            
            if claim.get('fraud_indicators'):
                print(f"\n   🚩 Fraud Indicators:")
                for indicator in claim['fraud_indicators']:
                    print(f"      • {indicator}")
            
            return claim
        else:
            print(f"❌ Failed to get claim: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def run_full_test():
    """Run complete test workflow"""
    print("\n" + "="*80)
    print("🧪 RUNNING AUTOMATED API TESTS")
    print("="*80)
    
    # Step 1: Health check
    if not test_health_check():
        print("\n❌ Backend is not running. Please start it first:")
        print("   cd server")
        print("   python -m uvicorn main:app --reload --port 8000")
        return
    
    # Step 2: Login
    token = test_login()
    if not token:
        print("\n❌ Login failed. Cannot continue tests.")
        return
    
    # Step 3: Get policies
    policy_number = test_get_policies(token)
    if not policy_number:
        print("\n❌ No policies found. Please create a policy first.")
        return
    
    # Step 4: Create claim
    claim_id = test_create_claim(token, policy_number, test_case="MEDIUM")
    if not claim_id:
        print("\n❌ Failed to create claim. Cannot continue.")
        return
    
    # Step 5: Finalize claim (trigger fraud detection)
    if not test_finalize_claim(token, claim_id):
        print("\n❌ Failed to finalize claim.")
        return
    
    # Step 6: Get results
    test_get_claim_details(token, claim_id)
    
    print("\n" + "="*80)
    print("✅ AUTOMATED TESTS COMPLETED!")
    print("="*80)
    print(f"\nNow check the Admin Claims Queue at: {FRONTEND_URL}")
    print("Login as admin@vantage.com / admin123")

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                   CHOOSE TESTING METHOD                                  ║
╚══════════════════════════════════════════════════════════════════════════╝

1. 🌐 UI TESTING (Recommended for users)
   → Follow the step-by-step guide above
   → Test using the web interface

2. 🔧 API TESTING (For developers)
   → Automated test via API calls
   → Shows detailed responses
   
Enter your choice (1 or 2), or 'q' to quit: """)
    
    choice = input().strip()
    
    if choice == "2":
        run_full_test()
    elif choice == "1":
        print("\n✅ Follow the UI testing guide above!")
        print(f"\n🌐 Open your browser and go to: {FRONTEND_URL}")
    elif choice == "q":
        print("Exiting...")
    else:
        print("Invalid choice. Please run the script again.")
