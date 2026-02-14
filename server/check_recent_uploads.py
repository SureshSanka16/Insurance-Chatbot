import asyncio
from sqlalchemy import text
from database import engine
import logging

# Suppress SQLAlchemy logs
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

async def check():
    print("Checking for recent document uploads...")
    async with engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT name, claim_id, user_id, user_email, policy_number, created_at 
            FROM documents 
            ORDER BY created_at DESC 
            LIMIT 5
        """))
        rows = result.fetchall()
        
        if not rows:
            print("No documents found.")
        else:
            print(f"Found {len(rows)} recent documents:")
            for row in rows:
                print(f" - File: {row.name}")
                print(f"   Claim: {row.claim_id}")
                print(f"   User: {row.user_id}")
                print(f"   Email: {row.user_email}")
                print(f"   Policy: {row.policy_number}")
                print(f"   Time: {row.created_at}")
                print("---")

if __name__ == "__main__":
    asyncio.run(check())
