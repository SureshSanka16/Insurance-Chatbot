"""
Manually apply fraud_status migration to database
"""
import sqlite3
import os

# Get database path
db_path = os.path.join(os.path.dirname(__file__), "vantage.db")

print(f"Connecting to database: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if fraud_status column already exists
    cursor.execute("PRAGMA table_info(claims)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'fraud_status' in columns:
        print("✅ fraud_status column already exists!")
    else:
        print("Adding fraud_status column...")
        
        # Add fraud_status column (SQLite stores enums as TEXT with CHECK constraint)
        cursor.execute("""
            ALTER TABLE claims 
            ADD COLUMN fraud_status TEXT DEFAULT 'PENDING' 
            CHECK(fraud_status IN ('PENDING', 'ANALYZING', 'COMPLETED', 'FAILED'))
        """)
        
        # Update existing claims
        cursor.execute("UPDATE claims SET fraud_status = 'PENDING' WHERE fraud_status IS NULL")
        
        conn.commit()
        print("✅ fraud_status column added successfully!")
    
    # Verify the column exists now
    cursor.execute("PRAGMA table_info(claims)")
    columns = [column[1] for column in cursor.fetchall()]
    print(f"\nCurrent claims table columns: {', '.join(columns)}")
    
    conn.close()
    print("\n✅ Migration completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    if conn:
        conn.rollback()
        conn.close()
