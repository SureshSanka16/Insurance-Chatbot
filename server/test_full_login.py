"""
Quick test to verify the login system end-to-end
"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("="*70)
print("TESTING INSURANCE CHATBOT LOGIN SYSTEM")
print("="*70)

# Test 1: Check backend health
print("\n[1] Checking backend health...")
try:
    r = requests.get(f"{BASE_URL}/health", timeout=5)
    print(f"    ✅ Backend is healthy: {r.json()}")
except Exception as e:
    print(f"    ❌ Backend not responding: {e}")
    exit(1)

# Test 2: Test admin login
print("\n[2] Testing admin login...")
login_data = {
    "username": "admin@vantage.ai",  # OAuth2 uses 'username' field
    "password": "password123"
}

try:
    r = requests.post(
        f"{BASE_URL}/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=5
    )
    
    if r.status_code == 200:
        token_data = r.json()
        print(f"    ✅ Login successful!")
        print(f"    Token: {token_data['access_token'][:50]}...")
        
        # Test 3: Get user info with token
        print("\n[3] Fetching user info with token...")
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        r_me = requests.get(f"{BASE_URL}/me", headers=headers, timeout=5)
        
        if r_me.status_code == 200:
            user = r_me.json()
            print(f"    ✅ User info retrieved:")
            print(f"       Name: {user['name']}")
            print(f"       Email: {user['email']}")
            print(f"       Role: {user['role']}")
        else:
            print(f"    ❌ Failed to get user info: {r_me.text}")
    else:
        print(f"    ❌ Login failed: {r.json()}")
        
except Exception as e:
    print(f"    ❌ Error: {e}")

print("\n" + "="*70)
print("FRONTEND LOGIN CREDENTIALS:")
print("="*70)
print("  Email:    admin@vantage.ai")
print("  Password: password123")
print("  URL:      http://localhost:3002")
print("="*70)
