import requests
import time

print("Testing backend endpoints...")
print("=" * 60)

# Test 1: Health check
print("\n[1] Testing /health endpoint...")
try:
    r = requests.get("http://localhost:8000/health", timeout=5)
    print(f"    ✅ Status: {r.status_code}")
    print(f"    Response: {r.json()}")
except requests.exceptions.Timeout:
    print("    ❌ TIMEOUT after 5 seconds")
except Exception as e:
    print(f"    ❌ Error: {e}")

# Test 2: Login
print("\n[2] Testing /auth/login endpoint...")
try:
    data = {
        "username": "admin@vantage.ai",
        "password": "password123"
    }
    r = requests.post(
        "http://localhost:8000/auth/login",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=5
    )
    print(f"    ✅ Status: {r.status_code}")
    if r.status_code == 200:
        print(f"    Token received: {r.json()['access_token'][:30]}...")
    else:
        print(f"    Response: {r.text}")
except requests.exceptions.Timeout:
    print("    ❌ TIMEOUT after 5 seconds")
except Exception as e:
    print(f"    ❌ Error: {e}")

print("\n" + "=" * 60)
