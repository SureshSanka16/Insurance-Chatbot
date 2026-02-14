import sqlite3
import os

DB_PATH = "vantage.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "notifications_enabled" in columns:
            print("✅ Column 'notifications_enabled' already exists in 'users' table")
        else:
            print("🔄 Adding 'notifications_enabled' column to 'users' table...")
            # Add column with default value True (1)
            cursor.execute("ALTER TABLE users ADD COLUMN notifications_enabled BOOLEAN DEFAULT 1")
            conn.commit()
            print("✅ Migration successful")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
