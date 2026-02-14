"""
Database Migration: Make claim_id nullable in documents table
"""
import sqlite3

db_path = "vantage.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    print("Starting migration...")
    
    # Disable foreign keys temporarily
    cursor.execute("PRAGMA foreign_keys = OFF")
    
    # Create new table with nullable claim_id
    cursor.execute("""
        CREATE TABLE documents_new (
            id TEXT PRIMARY KEY,
            claim_id TEXT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            url TEXT,
            size TEXT,
            file_size_bytes INTEGER,
            file_data BLOB,
            content_type TEXT,
            date TEXT,
            summary TEXT,
            category TEXT,
            extracted_entities TEXT,
            user_id TEXT,
            user_email TEXT,
            policy_number TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (claim_id) REFERENCES claims(id)
        )
    """)
    
    # Copy all data
    cursor.execute("INSERT INTO documents_new SELECT * FROM documents")
    
    # Drop old table
    cursor.execute("DROP TABLE documents")
    
    # Rename new table
    cursor.execute("ALTER TABLE documents_new RENAME TO documents")
    
    # Re-enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    conn.commit()
    print("[OK] Migration successful: claim_id is now nullable")
    
except Exception as e:
    print(f"[ERROR] Migration failed: {e}")
    conn.rollback()
finally:
    conn.close()
