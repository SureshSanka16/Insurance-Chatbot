"""
Test script for claims API endpoints.
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def get_auth_token():
    """Get JWT token for authentication."""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "test@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Authentication successful")
        return token
    else:
        print(f"❌ Authentication failed: {response.text}")
        return None

def test_create_claim(token):
    """Test creating a new claim."""
    claim_data = {
        "policy_number": "POL-2026-001",
        "claimant_name": "John Doe",
        "type": "Vehicle",
        "amount": 5000.00,
        "description": "Car accident - rear-end collision on highway",
        "vehicle_info": {
            "makeModel": "Toyota Camry 2022",
            "regNumber": "ABC-1234",
            "vin": "1HGBH41JXMN109186",
            "odometer": "15000",
            "policeReportFiled": True,
            "policeReportNo": "PR-2026-12345",
            "location": "Highway 101, Exit 25",
            "time": "2026-02-11T14:30:00",
            "incidentType": "Rear-end collision"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/claims",
        json=claim_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 201:
        claim = response.json()
        print(f"✅ Claim created successfully")
        print(f"   ID: {claim['id']}")
        print(f"   Status: {claim['status']}")
        print(f"   Risk Score: {claim['risk_score']}")
        print(f"   Risk Level: {claim['risk_level']}")
        return claim['id']
    else:
        print(f"❌ Failed to create claim: {response.status_code}")
        print(f"   {response.text}")
        return None

def test_get_claims(token):
    """Test getting list of claims."""
    response = requests.get(
        f"{BASE_URL}/claims",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        claims = response.json()
        print(f"✅ Retrieved {len(claims)} claim(s)")
        for claim in claims:
            print(f"   - {claim['id']}: {claim['claimant_name']} (${claim['amount']})")
        return claims
    else:
        print(f"❌ Failed to get claims: {response.status_code}")
        print(f"   {response.text}")
        return None

def test_get_claim_by_id(token, claim_id):
    """Test getting a specific claim."""
    response = requests.get(
        f"{BASE_URL}/claims/{claim_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        claim = response.json()
        print(f"✅ Retrieved claim {claim_id}")
        print(f"   Claimant: {claim['claimant_name']}")
        print(f"   Amount: ${claim['amount']}")
        print(f"   Status: {claim['status']}")
        print(f"   Polymorphic Data: {json.dumps(claim.get('polymorphic_data', {}), indent=2)}")
        return claim
    else:
        print(f"❌ Failed to get claim: {response.status_code}")
        print(f"   {response.text}")
        return None

def test_update_claim_status(token, claim_id):
    """Test updating claim status."""
    response = requests.patch(
        f"{BASE_URL}/claims/{claim_id}/status",
        json={"status": "In Review"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        claim = response.json()
        print(f"✅ Updated claim status to: {claim['status']}")
        return claim
    else:
        print(f"❌ Failed to update status: {response.status_code}")
        print(f"   {response.text}")
        return None

def test_filter_claims(token):
    """Test filtering claims by status."""
    response = requests.get(
        f"{BASE_URL}/claims?status=New",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        claims = response.json()
        print(f"✅ Retrieved {len(claims)} claim(s) with status 'New'")
        return claims
    else:
        print(f"❌ Failed to filter claims: {response.status_code}")
        print(f"   {response.text}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Claims API Endpoints")
    print("=" * 60)
    
    # Get authentication token
    print("\n1. Authentication")
    print("-" * 60)
    token = get_auth_token()
    if not token:
        print("Cannot proceed without authentication")
        exit(1)
    
    # Test creating a claim
    print("\n2. Create Claim")
    print("-" * 60)
    claim_id = test_create_claim(token)
    
    # Test getting all claims
    print("\n3. Get All Claims")
    print("-" * 60)
    test_get_claims(token)
    
    # Test getting specific claim
    if claim_id:
        print(f"\n4. Get Claim by ID ({claim_id})")
        print("-" * 60)
        test_get_claim_by_id(token, claim_id)
        
        # Test updating claim status
        print(f"\n5. Update Claim Status ({claim_id})")
        print("-" * 60)
        test_update_claim_status(token, claim_id)
    
    # Test filtering claims
    print("\n6. Filter Claims by Status")
    print("-" * 60)
    test_filter_claims(token)
    
    print("\n" + "=" * 60)
    print("Testing Complete!")
    print("=" * 60)
