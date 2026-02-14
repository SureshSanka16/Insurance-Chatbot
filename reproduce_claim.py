import requests
import json
import random
import string

BASE_URL = "http://127.0.0.1:8000"

def generate_random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

def register_user():
    email = f"test_{generate_random_string()}@example.com"
    password = "password123"
    name = "Test User"
    
    print(f"Registering user {email}...")
    response = requests.post(f"{BASE_URL}/auth/register", json={
        "email": email,
        "password": password,
        "name": name,
        "role": "User"
    })
    
    if response.status_code == 201 or response.status_code == 200:
        print("Registration successful.")
        return email, password
    else:
        print(f"Registration failed: {response.text}")
        return None, None

def login(email, password):
    print(f"Logging in as {email}...")
    # OAuth2 specifies form data
    response = requests.post(f"{BASE_URL}/auth/login", data={"username": email, "password": password})
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("Login successful.")
        return token
    else:
        print(f"Login failed: {response.text}")
        return None

def create_policy(token):
    print("Creating a test policy...")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    policy_data = {
        "category": "Health",
        "title": "Test Health Policy",
        "coverage_amount": 100000.0,
        "premium": 500.0,
        "features": ["Test Feature 1", "Test Feature 2"]
    }
    
    response = requests.post(f"{BASE_URL}/policies/", data=json.dumps(policy_data), headers=headers)
    if response.status_code == 201:
        policy = response.json()
        print(f"Policy created: {policy['policy_number']}")
        return policy
    else:
        print(f"Failed to create policy: {response.status_code} - {response.text}")
        return None

def create_claim(token, policy):
    print(f"Creating claim for policy {policy['policy_number']}...")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    claim_data = {
        "policy_number": policy["policy_number"],
        "claimant_name": "Test User",
        "type": policy["category"],
        "amount": 5000.0,
        "description": "Test claim for reproduction script",
        "itemized_loss": [{"item": "Test Item", "cost": 5000.0}]
    }
    
    response = requests.post(f"{BASE_URL}/claims/", data=json.dumps(claim_data), headers=headers)
    if response.status_code == 201:
        print(f"Claim created successfully: {response.json()['id']}")
        return response.json()
    else:
        print(f"Failed to create claim: {response.status_code} - {response.text}")
        return None

def main():
    email, password = register_user()
    if not email:
        return

    token = login(email, password)
    if not token:
        return

    policy = create_policy(token)
    if not policy:
        return
    
    print("\n--- Attempt 1 ---")
    claim1 = create_claim(token, policy)
    
    print("\n--- Attempt 2 (Duplicate) ---")
    claim2 = create_claim(token, policy)

    if claim1 and claim2:
        print("\n[RESULT] Backend ALLOWS multiple claims for the same policy.")
    elif claim1 and not claim2:
        print("\n[RESULT] Backend BLOCKED the second claim.")
    else:
        print("\n[RESULT] Test failed to create initial claim.")

if __name__ == "__main__":
    main()
