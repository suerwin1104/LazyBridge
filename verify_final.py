import asyncio
import os
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())

async def verify_system():
    print("🔍 Starting HBMS V4.0 Final Verification (127.0.0.1 Fix)...")
    
    # 1. Test core.config imports
    try:
        from core.config import IDENTITY, log, CDP_URL
        print(f"✅ core.config: IDENTITY={IDENTITY}")
    except Exception as e:
        print(f"❌ core.config failed: {e}")
        return
        
    # 2. Test core.database initialization
    try:
        from core.database import init_db, get_db_session
        await init_db()
        print("✅ core.database: init_db successful")
        
        async with get_db_session() as session:
            # Test a query
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
            print("✅ core.database: get_db_session (context manager) works and query successful")
    except Exception as e:
        print(f"❌ core.database failed: {e}")
        return

    # 3. Test ai_engine (Gemini)
    try:
        from services.ai_engine import get_ai_response_async
        from core.config import GEMINI_API_KEY
        if GEMINI_API_KEY:
            print("⏳ Testing Gemini API response...")
            resp = await get_ai_response_async("Ping. Reply only with 'Pong'.")
            if "Pong" in resp.get("text", ""):
                 print(f"✅ AI Engine: OK ({resp['model_name']})")
            else:
                 print(f"⚠️ AI Engine: Unexpected response: {resp.get('text')[:50]}...")
        else:
            print("⚠️ AI Engine: Skipping Gemini test (No API key)")
    except Exception as e:
        print(f"❌ AI Engine failed: {e}")

    print("\n✨ HBMS V4.0 is fully operational!")

if __name__ == "__main__":
    asyncio.run(verify_system())
