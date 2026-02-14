
import asyncio
from database import async_session_maker
from models import User, UserRole
from auth_utils import Hash

async def seed_admin():
    async with async_session_maker() as session:
        # Check if admin exists
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.email == "admin@vantage.ai"))
        admin = result.scalar_one_or_none()
        
        if admin:
            print("Admin user already exists.")
            return

        # Create admin
        print("Creating admin user...")
        hashed_password = Hash.hash_password("password123")
        new_admin = User(
            name="Admin User",
            email="admin@vantage.ai",
            password_hash=hashed_password,
            role=UserRole.ADMIN,
            avatar="https://ui-avatars.com/api/?name=Admin+User&background=0D8ABC&color=fff"
        )
        session.add(new_admin)
        await session.commit()
        print("✅ Admin user created successfully: admin@vantage.ai / password123")

if __name__ == "__main__":
    asyncio.run(seed_admin())
