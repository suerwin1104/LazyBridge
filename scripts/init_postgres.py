import asyncio
import os
import sys
sys.path.append(os.getcwd())

from core.database import engine, Base
# Import all models to register them with Base.metadata
import models.task
import models.history
import models.memory
import models.metrics

async def init_db():
    print(f"Initializing database at {engine.url}")
    async with engine.begin() as conn:
        # This will create tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database initialization complete.")

if __name__ == "__main__":
    asyncio.run(init_db())
