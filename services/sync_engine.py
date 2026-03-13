import asyncio
import os
import aiohttp
from core.config import log, IDENTITY
from services.local_rag import local_rag

# 從環境變數讀取 Hive 節點清單 (例如: 100.64.0.1,100.64.0.2)
HIVE_NODES = [n.strip() for n in os.getenv("HIVE_NODES", "").split(",") if n.strip()]

async def sync_with_hive():
    """與 Hive 網路的其他節點進行知識同步。"""
    if not HIVE_NODES:
        log("🐝 [Hive Sync] 沒有偵測到其他 Hive 節點，跳過同步。")
        return
    
    log(f"🐝 [Hive Sync] 正在與 {len(HIVE_NODES)} 個節點同步知識...")
    
    async with aiohttp.ClientSession() as session:
        # 1. 匯出本地知識庫，準備推送給他人 (選擇性)
        local_data = local_rag.export_knowledge()
        
        for node in HIVE_NODES:
            # 2. 從遠端拉取 (Pull)
            try:
                url_pull = f"http://{node}:8080/api/knowledge/export"
                async with session.get(url_pull, timeout=30) as resp:
                    if resp.status == 200:
                        content = await resp.read()
                        local_rag.import_knowledge(content)
                        log(f"✅ [Hive Sync] 已從 {node} 拉取更新。")
            except Exception as e:
                log(f"⚠️ [Hive Sync] 無法從節點 {node} 拉取: {e}")
                
            # 3. 推送至遠端 (Push)
            if local_data:
                try:
                    url_push = f"http://{node}:8080/api/knowledge/import"
                    async with session.post(url_push, data=local_data, timeout=30) as resp:
                        if resp.status == 200:
                            log(f"✅ [Hive Sync] 已推送知識至 {node}。")
                except Exception as e:
                    log(f"⚠️ [Hive Sync] 無法推送至節點 {node}: {e}")

async def hive_sync_loop():
    """背景同步循環，預設每小時執行一次。"""
    log("🐝 [Hive Sync] 背景同步服務已啟動。")
    # 啟動後延遲一下再首同步，避免啟動時太壅塞
    await asyncio.sleep(60)
    while True:
        try:
            await sync_with_hive()
        except Exception as e:
            log(f"❌ [Hive Sync] 循環異常: {e}")
        await asyncio.sleep(3600) # 1 hour
