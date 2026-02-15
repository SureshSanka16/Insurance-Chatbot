import requests

print("Testing backend on port 8001...")
try:
    r = requests.get("http://localhost:8001/health", timeout=3)
    print(f"✅ Health check: {r.json()}")
    
    # Test login
    r2 = requests.post(
        "http://localhost:8001/auth/login",
        data={"username": "admin@vantage.ai", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=3
    )
    print(f"✅ Login status: {r2.status_code}")
    if r2.status_code == 200:
        print(f"✅ Token received!")
except Exception as e:
    print(f"❌ Error: {e}")
