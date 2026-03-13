import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test_conn():
    # Try both localhost and 127.0.0.1
    urls = [
        "postgresql+asyncpg://hbms_admin:hbms_password_2026@localhost:5432/hbms_master",
        "postgresql+asyncpg://hbms_admin:hbms_password_2026@127.0.0.1:5432/hbms_master"
    ]
    
    for url in urls:
        print(f"Testing {url}...")
        try:
            engine = create_async_engine(url)
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            print(f"✅ Success with {url}")
        except Exception as e:
            print(f"❌ Failed with {url}: {e}")

if __name__ == "__main__":
    asyncio.run(test_conn())
