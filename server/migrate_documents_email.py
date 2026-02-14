import asyncio
from sqlalchemy import text
from database import engine

async def migrate():
    print("Starting migration for user_email...")
    async with engine.begin() as conn:
        # Check if column exists
        result = await conn.execute(text("PRAGMA table_info(documents)"))
        columns = [row.name for row in result.fetchall()]
        
        if 'user_email' not in columns:
            print("Adding user_email column...")
            await conn.execute(text("ALTER TABLE documents ADD COLUMN user_email VARCHAR"))
        else:
            print("user_email column already exists.")
            
        print("Schema update complete.")
        
        # Data migration
        print("Migrating data...")
        
        # Populate using user_id if available, otherwise fallback to full join
        await conn.execute(text("""
            UPDATE documents 
            SET user_email = (
                SELECT email FROM users WHERE users.id = documents.user_id
            )
            WHERE user_email IS NULL AND user_id IS NOT NULL
        """))
        
        print("Data migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate())
