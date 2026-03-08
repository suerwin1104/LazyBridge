import asyncio
import os
import subprocess
from core.config import log
from core.queue import queue
from core.cdp import send_to_antigravity
from services.briefing import get_briefing
from services.ai_engine import get_ai_response_async
import requests

# 取得 Discord Webhook URL (用於 Worker 回報結果)
# 這裡簡單起見，我們先假設有一個 Webhook URL 或者透過 DISCORD_BOT_TOKEN 直接發送訊息
# 為了避免複雜度，我們先直接在 Worker 裡建立一個簡單的 Discord 訊息發送邏輯

def send_discord_msg(channel_id, content):
    """Worker 專用的簡單 Discord 訊息發送 (透過 Bot Token)。"""
    from core.config import get_bot_token
    token = get_bot_token()
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }
    payload = {"content": content}
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code != 200:
        log(f"❌ Worker 發送 Discord 訊息失敗: {resp.text}")

async def handle_task(task):
    task_type = task.get("type")
    payload = task.get("payload", {})
    
    log(f"👷 正在處理任務: {task_type}")
    
    try:
        if task_type == "ask":
            # Phase 2: 優先嘗試使用 API 引擎 (無頭模式)
            message = payload.get("message")
            channel_id = payload.get("channel_id")
            author = payload.get("author")
            
            from core.config import ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY
            if ANTHROPIC_API_KEY or OPENAI_API_KEY or GEMINI_API_KEY:
                log(f"🧠 正在使用 API 引擎 (Headless) 處理: {message[:30]}...")
                response = await get_ai_response_async(message)
                send_discord_msg(channel_id, f"🤖 **(API Mode)** {response}")
            else:
                # 降級方案: 呼叫 CDP 與 Antigravity 互動
                log(f"🌐 API Key 未設定，降級使用 CDP 注入: {message[:30]}...")
                await send_to_antigravity(message, channel_id, author)
            
        elif task_type == "briefing":
            # 執行晨報生成
            channel_id = payload.get("channel_id")
            params = payload.get("params", {})
            log(f"📰 正在生成晨報...")
            report = await asyncio.to_thread(get_briefing, **params)
            
            if channel_id:
                send_discord_msg(channel_id, report)
                log(f"✅ 晨報已發送至頻道 {channel_id}")
                
        elif task_type == "command":
            # 執行系統指令
            command = payload.get("command")
            task_name = payload.get("task_name", "Command Task")
            log(f"🚀 執行指令: {command}")
            
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                log(f"✅ 指令執行成功: {task_name}")
            else:
                log(f"❌ 指令執行失敗: {stderr.decode()}")
                
        else:
            log(f"⚠️ 未知的任務類型: {task_type}")
            
    except Exception as e:
        log(f"❌ Worker 處理任務出錯: {e}")

async def main():
    log("🚀 Worker 已啟動，正在監聽 Redis 隊列...")
    while True:
        try:
            task = queue.pop_task(timeout=5)
            if task:
                await handle_task(task)
        except Exception as e:
            log(f"❌ Worker Loop 異常: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
