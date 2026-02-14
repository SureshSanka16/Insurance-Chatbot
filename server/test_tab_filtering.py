"""
Test tab-strict filtering and RAG behavior:
- Vehicle tab: only Vehicle claims and Drive Secure base policy
- Cross-tab: asking about a claim from another category returns "does not belong"

Run: python test_tab_filtering.py
Requires: Server running on http://localhost:8000 with latest code (restart server if you just changed ai.py or rag_service.py).
"""
import requests
import sys

BASE = "http://localhost:8000"

def login():
    r = requests.post(f"{BASE}/auth/login",
                      data={"username": "raj@gmail.com", "password": "12345678"},
                      timeout=10)
    if r.status_code != 200:
        raise SystemExit(f"Login failed: {r.status_code}")
    return r.json()["access_token"]

def chat(token, message, active_category=None, claim_id=None):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {"message": message}
    if active_category:
        body["active_category"] = active_category
    if claim_id is not None:
        body["claim_id"] = claim_id
    r = requests.post(f"{BASE}/ai/copilot/chat", headers=headers, json=body, timeout=60)
    if r.status_code != 200:
        raise SystemExit(f"Chat failed: {r.status_code} - {r.text[:200]}")
    return r.json()

def main():
    print("=" * 70)
    print("TAB FILTERING & RAG TESTS")
    print("=" * 70)

    token = login()
    print("\n[OK] Logged in\n")

    # --- Test 1: Vehicle tab, ask about a Vehicle claim (should succeed) ---
    print("1. Vehicle tab + Vehicle claim CLM-2026-024")
    print("   (Should accept and use Drive Secure V-15 + claim docs)")
    data = chat(token, "What is covered under my policy for this claim?", active_category="Vehicle", claim_id="CLM-2026-024")
    resp = data["response"]
    sources = data.get("sources", [])
    rag = data.get("rag_context_used", False)
    if "does not belong" in resp.lower():
        print("   [FAIL] Got 'does not belong' for a Vehicle claim in Vehicle tab")
    else:
        print("   [OK] No cross-tab rejection")
    if sources:
        names = [s.get("source", "?") for s in sources]
        vehicle_ok = any("Drive_Secure" in n or "V-15" in n for n in names)
        print(f"   Sources: {names}")
        if vehicle_ok or not names:
            print("   [OK] Sources look tab-scoped or no docs yet")
        else:
            print("   [WARN] Expected Drive_Secure among sources in Vehicle tab")
    else:
        print("   Sources: (none)")
    print(f"   RAG used: {rag}")
    print()

    # --- Test 2: Vehicle tab, ask about a Property claim (should reject) ---
    print("2. Vehicle tab + Property claim CLM-2026-026")
    print("   (Should reply: does not belong, switch to Home tab)")
    data = chat(token, "Tell me about claim CLM-2026-026", active_category="Vehicle", claim_id="CLM-2026-026")
    resp = data["response"]
    if "does not belong" in resp.lower() and ("home" in resp.lower() or "property" in resp.lower()):
        print("   [OK] Cross-tab rejection with correct tab suggestion")
    else:
        print("   [FAIL] Expected 'does not belong' and suggestion to switch to Home/Property tab")
    print(f"   Response (first 200 chars): {resp[:200]}...")
    print()

    # --- Test 3: Home tab, ask about Vehicle claim (should reject) ---
    print("3. Home tab + Vehicle claim CLM-2026-024")
    print("   (Should reply: does not belong, switch to Vehicle tab)")
    data = chat(token, "What is the status of CLM-2026-024?", active_category="Home", claim_id="CLM-2026-024")
    resp = data["response"]
    if "does not belong" in resp.lower() and "vehicle" in resp.lower():
        print("   [OK] Cross-tab rejection with Vehicle tab suggestion")
    else:
        print("   [FAIL] Expected 'does not belong' and Vehicle tab suggestion")
    print(f"   Response (first 200 chars): {resp[:200]}...")
    print()

    # --- Test 4: Vehicle tab, no claim (should list Vehicle claims, not run RAG) ---
    print("4. Vehicle tab, no claim selected - ask general question")
    print("   (Should list Vehicle claims, ask which claim)")
    data = chat(token, "What does my policy cover?", active_category="Vehicle")
    resp = data["response"]
    rag = data.get("rag_context_used", False)
    if "CLM-" in resp and ("which claim" in resp.lower() or "select" in resp.lower()):
        print("   [OK] Asks user to select a claim")
    else:
        print("   [INFO] Response may list claims or ask for selection")
    print(f"   RAG used: {rag} (expected False when no claim selected)")
    print()

    print("=" * 70)
    print("TESTS COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
    sys.exit(0)
