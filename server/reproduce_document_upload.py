import asyncio
from sqlalchemy import text, select
from database import engine
from models import Claim, Document, DocumentType, User, Policy, UserRole, PolicyCategory
import logging
from datetime import datetime
import sys

# Force suppress logging
logging.getLogger('sqlalchemy').setLevel(logging.WARNING)

async def reproduce():
    print("Trying to reproduce document insertion...")
    async with engine.begin() as conn:
        # 1. Create a dummy user/policy/claim if not exists
        # Actually, let's just find one.
        result = await conn.execute(text("SELECT id FROM claims LIMIT 1"))
        claim_id = result.scalar()
        
        if not claim_id:
            print("No claims found to attach document to. Creating dummy data.")
            # If no claims, I'd need to create User -> Policy -> Claim.
            # This is complex. Let's assume there is at least one claim, or just skip if empty.
            return

        print(f"Found claim: {claim_id}")
        
        # 2. Mock upload logic
        # We need to fetch the claim with policy to get user_id/policy_number
        # Using raw SQL for simplicity in this script
        result = await conn.execute(text(f"SELECT policy_number FROM claims WHERE id = '{claim_id}'"))
        policy_numer = result.scalar()
        
        result = await conn.execute(text(f"SELECT user_id FROM policies WHERE policy_number = '{policy_numer}'"))
        user_id = result.scalar()
        
        print(f"Policy: {policy_numer}, User: {user_id}")
        
        # 3. Insert document
        doc_id = f"test-doc-{datetime.now().timestamp()}"
        print(f"Inserting document {doc_id}...")
        
        await conn.execute(text(f"""
            INSERT INTO documents (
                id, claim_id, name, type, url, size, file_size_bytes, 
                date, user_id, policy_number, created_at, updated_at
            ) VALUES (
                '{doc_id}', '{claim_id}', 'test.pdf', 'PDF', '', '1 KB', 1024, 
                '{datetime.utcnow()}', '{user_id}', '{policy_numer}', 
                '{datetime.utcnow()}', '{datetime.utcnow()}'
            )
        """))
        
        print("Document inserted.")
        
        # 4. Verify
        result = await conn.execute(text(f"SELECT user_id, policy_number FROM documents WHERE id = '{doc_id}'"))
        row = result.fetchone()
        print(f"Verification: User={row.user_id}, Policy={row.policy_number}")

if __name__ == "__main__":
    asyncio.run(reproduce())
