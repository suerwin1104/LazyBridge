import asyncio
from services.presentation import generate_presentation

async def test_presentation():
    print("🎨 Testing Presentation Builder...")
    
    title = "LazyBridge Project Overview"
    sections = [
        {"title": "Introduction", "content": "LazyBridge is an autonomous agent harness powered by ECC logic.\\nIt integrates Discord, AI models, and local tools."},
        {"title": "Core Features", "content": "- Harness Metrics (Observability)\\n- Autonomous Loop (Self-Audit)\\n- NanoClaw Compaction (Long-term Memory)"},
        {"title": "AgentShield", "content": "Security layer providing command sanitization and data protection."},
        {"title": "Future Roadmap", "content": "Expanding into multi-agent collaboration and advanced UI reporting."}
    ]
    
    file_path = await generate_presentation(title, sections)
    print(f"✅ Presentation generated successfully at: {file_path}")

if __name__ == "__main__":
    asyncio.run(test_presentation())
