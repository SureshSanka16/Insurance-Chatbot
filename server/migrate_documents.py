import asyncio
from sqlalchemy import text
from database import engine

async def migrate():
    print("Starting migration...")
    async with engine.begin() as conn:
        # Check if columns exist
        result = await conn.execute(text("PRAGMA table_info(documents)"))
        columns = [row.name for row in result.fetchall()]
        
        if 'user_id' not in columns:
            print("Adding user_id column...")
            await conn.execute(text("ALTER TABLE documents ADD COLUMN user_id VARCHAR"))
        else:
            print("user_id column already exists.")
            
        if 'policy_number' not in columns:
            print("Adding policy_number column...")
            await conn.execute(text("ALTER TABLE documents ADD COLUMN policy_number VARCHAR"))
        else:
            print("policy_number column already exists.")
            
        print("Schema update complete.")
        
        # Data migration
        print("Migrating data...")
        
        # SQLite subquery updates
        await conn.execute(text("""
            UPDATE documents 
            SET policy_number = (
                SELECT policy_number FROM claims WHERE claims.id = documents.claim_id
            )
            WHERE policy_number IS NULL
        """))
        
        await conn.execute(text("""
            UPDATE documents 
            SET user_id = (
                SELECT policies.user_id 
                FROM policies 
                JOIN claims ON claims.policy_number = policies.policy_number 
                WHERE claims.id = documents.claim_id
            )
            WHERE user_id IS NULL
        """))
        
        print("Data migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate())
