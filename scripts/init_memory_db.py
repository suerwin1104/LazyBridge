import asyncio
from core.database import init_db
from models.memory import MemoryEntry

async def test():
    print("初始化資料庫...")
    await init_db()
    print("完成")

if __name__ == "__main__":
    asyncio.run(test())
