"""Check existing users in database"""
import asyncio
from database import async_session_maker
from models import User
from sqlalchemy import select

async def check_users():
    async with async_session_maker() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()
        
        print('\n' + '='*60)
        print('📋 EXISTING USERS IN DATABASE')
        print('='*60)
        
        for user in users:
            print(f'\n  👤 {user.role.value.upper()}')
            print(f'     Email: {user.email}')
            print(f'     Name: {user.name}')
        
        print(f'\n{"="*60}')
        print(f'Total users: {len(users)}')
        print('='*60 + '\n')

if __name__ == "__main__":
    asyncio.run(check_users())
