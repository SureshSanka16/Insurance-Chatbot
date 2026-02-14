"""
Upload Base Policy Documents
=============================
Upload and process the 4 base insurance policy PDFs into the system.

Base Policies:
1. Platinum Life L-100
2. Health Shield H-500
3. Drive Secure V-15
4. Home Protect P-50
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from database import async_session_maker
from models import Document, DocumentType, DocumentCategory
from services.knowledge_bridge import process_document
import uuid
from datetime import datetime


# Base policy configurations
BASE_POLICIES = [
    {
        "name": "Platinum_Life_L-100.pdf",
        "policy_number": "POL-BASE-L100",
        "category": DocumentCategory.LEGAL,
        "description": "Platinum Life L-100 - Base Life Insurance Policy",
    },
    {
        "name": "Health_Shield_H-500.pdf",
        "policy_number": "POL-BASE-H500",
        "category": DocumentCategory.MEDICAL,
        "description": "Health Shield H-500 - Base Health Insurance Policy",
    },
    {
        "name": "Drive_Secure_V-15.pdf",
        "policy_number": "POL-BASE-V15",
        "category": DocumentCategory.LEGAL,
        "description": "Drive Secure V-15 - Base Vehicle Insurance Policy",
    },
    {
        "name": "Home_Protect_P-50.pdf",
        "policy_number": "POL-BASE-P50",
        "category": DocumentCategory.LEGAL,
        "description": "Home Protect P-50 - Base Home Insurance Policy",
    },
]


async def upload_policy(pdf_path: str, policy_config: dict) -> str:
    """
    Upload a policy PDF to the database.
    
    Args:
        pdf_path: Path to the PDF file
        policy_config: Policy configuration dict
        
    Returns:
        Document ID
    """
    # Read PDF file
    with open(pdf_path, 'rb') as f:
        file_data = f.read()
    
    file_size_bytes = len(file_data)
    
    # Format file size
    if file_size_bytes < 1024:
        size_str = f"{file_size_bytes} B"
    elif file_size_bytes < 1024 * 1024:
        size_str = f"{file_size_bytes / 1024:.1f} KB"
    else:
        size_str = f"{file_size_bytes / (1024 * 1024):.1f} MB"
    
    # Create document record
    document = Document(
        id=str(uuid.uuid4()),
        claim_id=None,  # Base policies are not tied to specific claims
        name=policy_config["name"],
        type=DocumentType.PDF,
        url="",
        size=size_str,
        file_size_bytes=file_size_bytes,
        file_data=file_data,
        content_type="application/pdf",
        category=policy_config["category"],
        date=datetime.utcnow(),
        user_id=None,  # Base policies are global (accessible to all users)
        user_email=None,
        policy_number=policy_config["policy_number"],
    )
    
    async with async_session_maker() as session:
        session.add(document)
        await session.commit()
        await session.refresh(document)
    
    print(f"[OK] Uploaded: {policy_config['name']} (ID: {document.id})")
    return document.id


async def main():
    """Main function to upload and process all base policies."""
    print("=" * 60)
    print("Base Policy Upload & Processing")
    print("=" * 60)
    print()
    
    # Get PDF directory from user
    pdf_dir = input("Enter the directory path containing the policy PDFs: ").strip()
    
    if not os.path.exists(pdf_dir):
        print(f"[ERROR] Directory not found: {pdf_dir}")
        return
    
    print()
    print(f"Looking for PDFs in: {pdf_dir}")
    print()
    
    uploaded_ids = []
    
    # Upload each policy
    for policy_config in BASE_POLICIES:
        pdf_path = os.path.join(pdf_dir, policy_config["name"])
        
        if not os.path.exists(pdf_path):
            print(f"[WARN] File not found: {policy_config['name']}")
            print(f"  Expected at: {pdf_path}")
            print(f"  Skipping...")
            print()
            continue
        
        try:
            doc_id = await upload_policy(pdf_path, policy_config)
            uploaded_ids.append((doc_id, policy_config["name"]))
        except Exception as e:
            print(f"[ERROR] Error uploading {policy_config['name']}: {e}")
            print()
    
    if not uploaded_ids:
        print("[ERROR] No policies were uploaded successfully.")
        return
    
    print()
    print("=" * 60)
    print("Processing Documents into FAISS Vector Store")
    print("=" * 60)
    print()
    
    # Process each uploaded document
    for doc_id, doc_name in uploaded_ids:
        try:
            print(f"Processing: {doc_name}...")
            result = await process_document(doc_id)
            print(f"  [OK] Extracted {result['sections_extracted']} sections")
            print(f"  [OK] Stored {result['chunks_stored']} chunks")
            print(f"  [OK] Total in store: {result['collection_total']}")
            print()
        except Exception as e:
            print(f"  [ERROR] Error: {e}")
            print()
    
    print("=" * 60)
    print("[OK] Base Policy Setup Complete!")
    print("=" * 60)
    print()
    print("The chatbot can now answer questions about:")
    for policy in BASE_POLICIES:
        print(f"  - {policy['description']}")


if __name__ == "__main__":
    asyncio.run(main())
