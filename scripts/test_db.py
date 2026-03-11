import asyncio
import os
import sys

sys.path.append(os.getcwd())

from sqlalchemy.ext.asyncio import create_async_engine
from core.config import DATABASE_URL, load_env

async def test_db():
    load_env()
    print(f"Testing DB URL: {DATABASE_URL}")
    try:
        engine = create_async_engine(DATABASE_URL, pool_timeout=5, connect_args={"timeout": 5})
        async with engine.connect() as conn:
            print("Connected successfully!")
            
        print("Now executing test query...")
        async with engine.connect() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
            print("Query successful!")
            
        print("Now testing task_trace table...")
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT count(*) FROM task_trace"))
            print(f"task_trace has {result.scalar()} rows")
            
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_db())
