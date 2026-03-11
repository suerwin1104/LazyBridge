import asyncio
from services.maintenance import run_self_audit
from core.database import init_db

async def test_loop():
    print("🚀 Initializing DB...")
    await init_db()
    
    print("🔄 Running Self-Audit Loop...")
    success = await run_self_audit()
    if success:
        print("✅ Self-Audit completed successfully in test.")
    else:
        print("❌ Self-Audit failed in test.")

if __name__ == "__main__":
    asyncio.run(test_loop())
