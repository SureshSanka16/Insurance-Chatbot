import requests
import sys

# Test user credentials
EMAIL = "test_notifications@example.com"
PASSWORD = "password123"
BASE_URL = "http://localhost:8000"

def test_notifications_api():
    print(f"Testing API at {BASE_URL}...")
    
    # 1. Register or Login
    session = requests.Session()
    
    # Register
    try:
        resp = session.post(f"{BASE_URL}/auth/register", json={
            "name": "Test User",
            "email": EMAIL,
            "password": PASSWORD,
            "role": "User"
        })
        if resp.status_code == 201:
            print("✅ User registered")
        elif resp.status_code == 400 and "registered" in resp.text:
            print("✅ User already exists (or registration failed with 400)")
        else:
            print(f"❌ Registration failed: {resp.status_code} {resp.text}")
            # Continue to login attempt anyway
    except requests.exceptions.ConnectionError:
        print("❌ Server not running or connection refused.")
        return

    # Login to get token
    resp = session.post(f"{BASE_URL}/auth/login", data={
        "username": EMAIL,
        "password": PASSWORD
    })
    
    if resp.status_code != 200:
        print(f"❌ Login failed: {resp.status_code} {resp.text}")
        return
    
    token = resp.json().get("access_token")
    if not token:
        print("❌ No access token returned")
        return
        
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. GET /me -> check default notifications_enabled
    resp = session.get(f"{BASE_URL}/me", headers=headers)
    if resp.status_code != 200:
        print(f"❌ GET /me failed: {resp.status_code}")
        return

    data = resp.json()
    print(f"Initial State: {data.get('notifications_enabled')}")
    
    # Depending on previous runs, it might be True or False.
    # We will force set it to False to verify change.

    # 3. PATCH /me -> disable notifications
    print("➡️ Disabling notifications...")
    resp = session.patch(f"{BASE_URL}/me", json={"notifications_enabled": False}, headers=headers)
    if resp.status_code != 200:
        print(f"❌ PATCH /me failed: {resp.status_code} {resp.text}")
        return
        
    data = resp.json()
    print(f"Updated State (False): {data.get('notifications_enabled')}")
    
    if data.get('notifications_enabled') is False:
        print("✅ Successfully disabled notifications")
    else:
         print(f"❌ Failed to disable notifications: {data}")

    # 4. PATCH /me -> enable notifications
    print("➡️ Enabling notifications...")
    resp = session.patch(f"{BASE_URL}/me", json={"notifications_enabled": True}, headers=headers)
    data = resp.json()
    print(f"Updated State (True): {data.get('notifications_enabled')}")

    if data.get('notifications_enabled') is True:
        print("✅ Successfully enabled notifications")
    else:
        print(f"❌ Failed to enable notifications: {data}")

if __name__ == "__main__":
    test_notifications_api()
