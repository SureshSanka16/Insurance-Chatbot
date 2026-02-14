"""
Quick script to verify database tables were created.
"""
import asyncio
from sqlalchemy import inspect
from database import engine


async def check_tables():
    async with engine.begin() as conn:
        tables = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_table_names()
        )
        print("✅ Database tables created:")
        for table in tables:
            print(f"  - {table}")
        print(f"\nTotal tables: {len(tables)}")
        return tables


if __name__ == "__main__":
    asyncio.run(check_tables())
