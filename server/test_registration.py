"""
Test script to debug registration issue.
"""
import asyncio
from sqlalchemy import select
from database import get_db, async_session_maker
from models import User
from auth_utils import Hash

async def test_registration():
    """Test user registration flow."""
    # Test data
    name = "Test User"
    email = "test@example.com"
    password = "password123"
    
    print(f"Testing registration for: {email}")
    print(f"Password length: {len(password)} characters")
    
    # Hash password
    try:
        hashed = Hash.hash_password(password)
        print(f"✅ Password hashed successfully")
        print(f"Hash length: {len(hashed)}")
    except Exception as e:
        print(f"❌ Error hashing password: {e}")
        return
    
    # Create user
    async with async_session_maker() as db:
        try:
            # Check if user exists
            result = await db.execute(select(User).where(User.email == email))
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"⚠️  User already exists, deleting...")
                await db.delete(existing)
                await db.commit()
            
            # Create new user
            new_user = User(
                name=name,
                email=email,
                password_hash=hashed,
            )
            
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            
            print(f"✅ User created successfully!")
            print(f"User ID: {new_user.id}")
            print(f"User email: {new_user.email}")
            print(f"User role: {new_user.role}")
            
        except Exception as e:
            print(f"❌ Error creating user: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_registration())
