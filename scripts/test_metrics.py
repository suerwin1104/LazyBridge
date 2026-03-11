import asyncio
from services.metrics import log_metrics, get_summary_stats
from core.database import init_db

async def test_metrics():
    print("🚀 Initializing DB...")
    await init_db()
    
    print("📝 Logging mock metrics...")
    await log_metrics("ask", 1500, 450, "success")
    await log_metrics("briefing", 800, 1200, "success")
    await log_metrics("command", 0, 150, "error")
    
    print("📊 Retrieving summary statistics...")
    stats = await get_summary_stats(days=1)
    if stats:
        print(f"Total Tokens: {stats['total_tokens']}")
        print(f"Avg Latency: {stats['avg_latency']:.2f}ms")
        print(f"Status Distribution: {stats['status_distribution']}")
    else:
        print("❌ Failed to retrieve stats.")

if __name__ == "__main__":
    asyncio.run(test_metrics())
