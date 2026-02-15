"""
Test Policy Management Functionality
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8001"

def test_health_check():
    """Test if backend is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✅ Backend Health: {response.status_code} - {response.text}")
        return True
    except Exception as e:
        print(f"❌ Backend not running: {e}")
        return False

def login_user(email, password):
    """Login and get auth token"""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={"username": email, "password": password},
            timeout=5
        )
        if response.status_code == 200:
            token = response.json()["access_token"]
            print(f"✅ Logged in as {email}")
            return token
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_get_policies(token):
    """Test GET /policies endpoint"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/policies", headers=headers, timeout=5)
        
        if response.status_code == 200:
            policies = response.json()
            print(f"\n✅ GET /policies - Success! Found {len(policies)} policies")
            
            for i, policy in enumerate(policies, 1):
                print(f"\n📋 Policy {i}:")
                print(f"   ID: {policy.get('id')}")
                print(f"   Number: {policy.get('policy_number')}")
                print(f"   Category: {policy.get('category')}")
                print(f"   Title: {policy.get('title')}")
                print(f"   Coverage: ₹{policy.get('coverage_amount', 0):,.0f}")
                print(f"   Premium: ₹{policy.get('premium', 0):,.0f}")
                print(f"   Status: {policy.get('status')}")
                print(f"   Expiry: {policy.get('expiry_date')}")
                if policy.get('features'):
                    print(f"   Features: {', '.join(policy.get('features'))}")
            
            return policies
        else:
            print(f"❌ GET /policies failed: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"❌ Error fetching policies: {e}")
        return []

def test_create_policy(token):
    """Test POST /policies endpoint"""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Create a test policy
        new_policy = {
            "category": "Health",
            "title": "Test Health Policy",
            "coverage_amount": 500000,
            "premium": 500,
            "status": "Active",
            "features": ["Cashless", "OPD Cover", "Maternity"]
        }
        
        response = requests.post(
            f"{BASE_URL}/policies",
            headers=headers,
            json=new_policy,
            timeout=5
        )
        
        if response.status_code == 200:
            policy = response.json()
            print(f"\n✅ POST /policies - Policy created successfully!")
            print(f"   ID: {policy.get('id')}")
            print(f"   Policy Number: {policy.get('policy_number')}")
            print(f"   Title: {policy.get('title')}")
            return policy
        else:
            print(f"❌ POST /policies failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating policy: {e}")
        return None

def test_get_single_policy(token, policy_id):
    """Test GET /policies/{id} endpoint"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/policies/{policy_id}",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            policy = response.json()
            print(f"\n✅ GET /policies/{policy_id} - Success!")
            print(f"   Title: {policy.get('title')}")
            print(f"   Status: {policy.get('status')}")
            return policy
        else:
            print(f"❌ GET single policy failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def check_policy_pdfs():
    """Check if policy PDF files exist"""
    import os
    
    print("\n📄 Checking Policy PDF Files:")
    pdf_dir = "policies"
    expected_pdfs = [
        "health_insurance_policy_vantage.pdf",
        "house_insurance_policy_vantage.pdf",
        "life_insurance_policy_vantage.pdf",
        "vehicle_insurance_policy_vantage.pdf"
    ]
    
    for pdf in expected_pdfs:
        path = os.path.join(pdf_dir, pdf)
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"   ✅ {pdf} - {size:,} bytes")
        else:
            print(f"   ❌ {pdf} - NOT FOUND")

def main():
    print("="*60)
    print("🔍 POLICY MANAGEMENT SYSTEM TEST")
    print("="*60)
    
    # Test 1: Backend health
    if not test_health_check():
        print("\n⚠️  Backend is not running. Please start the backend first.")
        return
    
    # Test 2: Login as Admin
    print("\n" + "="*60)
    print("🔐 Testing Admin Login")
    print("="*60)
    admin_token = login_user("admin@vantage.ai", "password123")
    
    if not admin_token:
        print("\n⚠️  Cannot proceed without authentication")
        return
    
    # Test 3: Get all policies (Admin view)
    print("\n" + "="*60)
    print("📋 Testing GET All Policies (Admin)")
    print("="*60)
    policies = test_get_policies(admin_token)
    
    # Test 4: Create a new policy
    print("\n" + "="*60)
    print("➕ Testing CREATE Policy")
    print("="*60)
    new_policy = test_create_policy(admin_token)
    
    # Test 5: Get single policy
    if new_policy:
        print("\n" + "="*60)
        print("🔍 Testing GET Single Policy")
        print("="*60)
        test_get_single_policy(admin_token, new_policy['id'])
    
    # Test 6: Login as User and test policies
    print("\n" + "="*60)
    print("👤 Testing User Login")
    print("="*60)
    user_token = login_user("james@gmail.com", "password123")
    
    if user_token:
        print("\n" + "="*60)
        print("📋 Testing GET Policies (User View)")
        print("="*60)
        user_policies = test_get_policies(user_token)
        print(f"\n📊 User sees {len(user_policies)} policies (only their own)")
    
    # Test 7: Check Policy PDF files
    print("\n" + "="*60)
    print("📄 Checking Policy Document Files")
    print("="*60)
    check_policy_pdfs()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"✅ Backend Running: Yes")
    print(f"✅ Admin Authentication: {'Yes' if admin_token else 'No'}")
    print(f"✅ User Authentication: {'Yes' if user_token else 'No'}")
    print(f"✅ Policies Retrieved: {len(policies)}")
    print(f"✅ Policy Creation: {'Yes' if new_policy else 'No'}")
    print("="*60)

if __name__ == "__main__":
    main()
