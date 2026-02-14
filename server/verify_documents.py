import asyncio
from sqlalchemy import text
from database import engine
import logging
import sys

# Force suppress logging
logging.basicConfig(level=logging.WARNING, force=True)
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

async def verify():
    print("Verifying documents table...")
    async with engine.begin() as conn:
        # Check if columns exist
        result = await conn.execute(text("PRAGMA table_info(documents)"))
        columns = [row.name for row in result.fetchall()]
        print(f"Columns in documents: {columns}")
        
        # Check row count
        result = await conn.execute(text("SELECT COUNT(*) FROM documents"))
        count = result.scalar()
        print(f"Total documents: {count}")
        
        if count > 0:
            print("\nFirst 5 documents:")
            result = await conn.execute(text("SELECT id, claim_id, user_id, policy_number FROM documents LIMIT 5"))
            for row in result:
                print(f"ID: {row.id}, Claim: {row.claim_id}, User: {row.user_id}, Policy: {row.policy_number}")
        else:
            print("No documents found.")

if __name__ == "__main__":
    asyncio.run(verify())
