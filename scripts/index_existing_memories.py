import asyncio
import os
import sys

# 將根目錄加入 path 以便匯入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import AsyncSessionLocal
from models.memory import MemoryEntry
from services.local_rag import local_rag
from sqlalchemy import select
from core.config import log

async def index_all():
    log("🚀 開始索引現有記憶...")
    
    async with AsyncSessionLocal() as session:
        stmt = select(MemoryEntry)
        result = await session.execute(stmt)
        entries = result.scalars().all()
        
        if not entries:
            log("📭 沒有找到任何記憶紀錄。")
            return
            
        log(f"📋 找到 {len(entries)} 筆紀錄，正在準備索引...")
        
        texts = []
        metadatas = []
        
        for entry in entries:
            texts.append(entry.content)
            metadatas.append({
                "id": entry.id,
                "category": entry.category,
                "title": entry.title,
                "text": entry.content[:1000] # FAISS metadata 通常不存太大，但在這裡我們需要原始文本進行檢索回顯
            })
            
        # 進行批次索引
        await local_rag.add_documents(texts, metadatas)
        log("✅ 所有現有紀錄已成功索引到本地 RAG 系統。")

if __name__ == "__main__":
    asyncio.run(index_all())
