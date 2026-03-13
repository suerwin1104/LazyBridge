import asyncio
import os
import sys

# 將根目錄加入 path 以便匯入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.local_rag import local_rag
from core.config import log

async def verify_rag():
    log("🧪 開始驗證 Local RAG 搜尋功能...")
    
    # 測試搜尋 query
    test_queries = [
        "這是一個關於 RAG 的測試",
        "如何節省 token",
        "Antigravity 的功能是什麼",
        "上次工作摘要"
    ]
    
    for query in test_queries:
        log(f"\n🔍 搜尋 Query: '{query}'")
        hits = await local_rag.search(query, top_k=2)
        
        if hits:
            log(f"✅ 找到 {len(hits)} 個結果:")
            for i, hit in enumerate(hits):
                title = hit['metadata'].get('title', 'Unknown')
                category = hit['metadata'].get('category', 'Unknown')
                text_preview = hit['metadata'].get('text', '')[:100]
                log(f"  {i+1}. [{category}] {title} (Score: {hit['score']:.4f})")
                log(f"     預覽: {text_preview}...")
        else:
            log("❌ 找不到相關結果。")

if __name__ == "__main__":
    asyncio.run(verify_rag())
