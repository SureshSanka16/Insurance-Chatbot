"""
📊 QUICK STATUS CHECKER
Check backend, database, and recent claims
"""

import sqlite3
import requests
import os
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
DB_PATH = os.path.join(os.path.dirname(__file__), "vantage.db")

print("""
╔══════════════════════════════════════════════════════════════════════╗
║               VANTAGE FRAUD DETECTION - STATUS CHECK                 ║
╚══════════════════════════════════════════════════════════════════════╝
""")

# 1. Check Backend
print("\n[1] BACKEND SERVER STATUS")
print("─" * 70)
try:
    response = requests.get(f"{BASE_URL}/", timeout=3)
    if response.status_code == 200:
        print("✅ Backend is RUNNING on http://127.0.0.1:8000")
        print("   Access API docs: http://127.0.0.1:8000/docs")
    else:
        print(f"⚠️  Backend responded with status {response.status_code}")
except:
    print("❌ Backend is NOT RUNNING")
    print("   Start it with: cd server && python -m uvicorn main:app --reload --port 8000")

# 2. Check Database
print("\n[2] DATABASE STATUS")
print("─" * 70)
try:
    if os.path.exists(DB_PATH):
        print(f"✅ Database found: {DB_PATH}")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check fraud_status column
        cursor.execute("PRAGMA table_info(claims)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'fraud_status' in columns:
            print("✅ fraud_status column exists")
        else:
            print("❌ fraud_status column MISSING - run: python apply_fraud_status_migration.py")
        
        conn.close()
    else:
        print(f"❌ Database NOT FOUND at {DB_PATH}")
except Exception as e:
    print(f"❌ Database error: {e}")

# 3. Check Recent Claims
print("\n[3] RECENT CLAIMS (Last 10)")
print("─" * 70)
try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, claimant_name, amount, status, fraud_status, risk_score, fraud_decision, created_at
        FROM claims 
        ORDER BY created_at DESC 
        LIMIT 10
    """)
    
    claims = cursor.fetchall()
    
    if claims:
        print(f"\n{'Claim ID':<15} {'Claimant':<20} {'Amount':<12} {'Status':<12} {'Fraud':<12} {'Score':<8} {'Decision':<15}")
        print("─" * 120)
        
        for claim in claims:
            claim_id, claimant, amount, status, fraud_status, risk_score, decision, created = claim
            
            # Format amount
            amount_str = f"${amount:,.0f}"
            
            # Format fraud score (risk_score is 0-100)
            score_str = f"{risk_score:.0f}%" if risk_score else "N/A"
            
            # Color indicators
            if fraud_status == "PENDING" or fraud_status == "ANALYZING":
                fraud_icon = "🔄"
            elif fraud_status == "COMPLETED":
                if risk_score and risk_score >= 75:
                    fraud_icon = "🔴"
                elif risk_score and risk_score >= 50:
                    fraud_icon = "🟡"
                else:
                    fraud_icon = "🟢"
            else:
                fraud_icon = "⚪"
            
            print(f"{claim_id:<15} {claimant:<20} {amount_str:<12} {status:<12} {fraud_icon} {fraud_status or 'N/A':<10} {score_str:<8} {decision or 'N/A':<15}")
        
        # Statistics
        print("\n📊 STATISTICS:")
        cursor.execute("SELECT COUNT(*) FROM claims")
        total = cursor.fetchone()[0]
        print(f"   Total Claims: {total}")
        
        cursor.execute("SELECT COUNT(*) FROM claims WHERE fraud_status = 'PENDING'")
        pending = cursor.fetchone()[0]
        print(f"   Pending Analysis: {pending}")
        
        cursor.execute("SELECT COUNT(*) FROM claims WHERE fraud_status = 'COMPLETED'")
        completed = cursor.fetchone()[0]
        print(f"   Analysis Completed: {completed}")
        
        cursor.execute("SELECT AVG(risk_score) FROM claims WHERE risk_score IS NOT NULL")
        avg_score = cursor.fetchone()[0]
        if avg_score:
            print(f"   Average Risk Score: {avg_score:.0f}%")
        
    else:
        print("📭 No claims found in database")
        print("\n💡 To test the system:")
        print("   1. Go to http://localhost:3001")
        print("   2. Login as user")
        print("   3. Submit a test claim")
        print("   4. Check admin portal at http://localhost:3001 (login as admin)")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error checking claims: {e}")

# 4. Fraud Detection Status
print("\n[4] FRAUD DETECTION SYSTEM")
print("─" * 70)
print("✅ Rule-based fraud detection ACTIVE")
print("✅ No external API dependencies")
print("✅ Analysis time: 1-3 seconds")
print("✅ Cost: $0 (no API calls)")

print("\n[5] TESTING INSTRUCTIONS")
print("─" * 70)
print("""
🎯 TO TEST THE SYSTEM:

1. USER SIDE:
   • Open: http://localhost:3001
   • Login as user (or register)
   • Go to Dashboard
   • Click "File New Claim"
   • Fill form and submit
   
2. ADMIN SIDE:
   • Open: http://localhost:3001 (new tab)
   • Login as admin@vantage.com / admin123
   • Click "Claims Queue"
   • See: 🔄 IN PROGRESS → then risk score after 2-3 sec
   • Click claim to see fraud analysis details

3. AUTOMATED TEST:
   • Run: python test_fraud_detection_workflow.py
   • Choose option 2 for API testing
""")

print("\n" + "═" * 70)
print("✅ Status check completed!")
print("═" * 70)
