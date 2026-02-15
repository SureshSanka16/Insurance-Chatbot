"""Test login endpoint"""
import requests
import json

BASE_URL = "http://localhost:8000"

# Test login
print("=" * 60)
print("Testing Login Endpoint")
print("=" * 60)

# Prepare login data (OAuth2 format)
login_data = {
    "username": "admin@vantage.ai",
    "password": "password123"
}

try:
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data=login_data,  # Form data, not JSON
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("\n✅ Login successful!")
        token = response.json()["access_token"]
        
        # Test /me endpoint with token
        print("\nTesting /me endpoint with token...")
        me_response = requests.get(
            f"{BASE_URL}/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"User Info: {json.dumps(me_response.json(), indent=2)}")
    else:
        print(f"\n❌ Login failed: {response.json().get('detail', 'Unknown error')}")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
