"""
Check and clean up existing claims
"""
import sqlite3
import os

# Get database path
db_path = os.path.join(os.path.dirname(__file__), "vantage.db")

print(f"Connecting to database: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check existing claims
    cursor.execute("SELECT id, policy_number, claimant_name, type, amount, status, fraud_status FROM claims")
    claims = cursor.fetchall()
    
    if claims:
        print(f"\n📋 Found {len(claims)} existing claims:")
        for claim in claims:
            print(f"  - ID: {claim[0]}, Policy: {claim[1]}, Claimant: {claim[2]}, Type: {claim[3]}, Amount: ${claim[4]}, Status: {claim[5]}, Fraud: {claim[6]}")
        
        print("\n🗑️  Clearing all existing claims...")
        cursor.execute("DELETE FROM claims")
        
        # Also clear documents
        cursor.execute("DELETE FROM documents")
        
        conn.commit()
        print("✅ All claims and documents cleared!")
    else:
        print("✅ No existing claims found.")
    
    conn.close()
    print("\n✅ Database cleanup completed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    if conn:
        conn.rollback()
        conn.close()
