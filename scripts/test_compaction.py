import asyncio
from datetime import datetime, timedelta
from core.database import init_db, AsyncSessionLocal
from models.memory import MemoryEntry
from services.memory_engine import compact_sessions, get_memory_context

async def test_compaction():
    print("🚀 Initializing DB...")
    await init_db()
    
    print("📝 Injecting mock old session data...")
    try:
        async with AsyncSessionLocal() as session:
            # Create a mock session that is 2 days old, with a large content
            mock_content = (
                "User: Please configure the timezone to Taipei.\n"
                "AI: Setting timezone to Asia/Taipei.\n"
                "User: Remember that I prefer Python with async over threaded.\n"
                "AI: Got it. I will use async for I/O operations from now on.\n"
                "User: Build a login system.\n"
                "AI: Here is the login system...\n"
                * 50 # Duplicate to make it verbose
            )
            old_time = datetime.utcnow() - timedelta(days=2)
            entry = MemoryEntry(
                category="session",
                title="Lesson Test Session",
                content=mock_content,
                created_at=old_time
            )
            session.add(entry)
            await session.commit()
    except Exception as e:
         print(f"Error injecting: {e}")

    # Check length BEFORE compaction
    # We must explicitly query since get_memory_context gets recent only
    # But wait, get_memory_context gets session within 7 days.
    ctx_before = await get_memory_context()
    print(f"📊 Length of context BEFORE compaction: {len(ctx_before)} chars")
    
    print("🗜️ Running Compaction...")
    await compact_sessions(days_old=1)
    
    # Check length AFTER compaction
    ctx_after = await get_memory_context()
    print(f"📊 Length of context AFTER compaction: {len(ctx_after)} chars")
    
    print("\n--- Semantic Lesson Extracted ---")
    print(ctx_after)
    print("---------------------------------")

if __name__ == "__main__":
    asyncio.run(test_compaction())
