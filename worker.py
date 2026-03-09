import asyncio
import json
import os
import subprocess
from core.config import log, get_soul_content
from core.queue import queue
from core.cdp import send_to_antigravity
from services.briefing import get_briefing
from services.ai_engine import get_ai_response_async
import requests
from services.shield import redact_sensitive_data, is_safe_command
from services.task_trace import TaskTraceService
import uuid

# ECC Harness Performance System - Hook Runtime Controls
ECC_HOOK_PROFILE = os.getenv("ECC_HOOK_PROFILE", "standard") # minimal|standard|strict
ECC_DISABLED_HOOKS = os.getenv("ECC_DISABLED_HOOKS", "").split(",")

import time
from services.metrics import log_metrics

def run_hook(hook_type, context=None):
    """Executes ECC-style hooks and handle metrics logging."""
    if hook_type in ECC_DISABLED_HOOKS:
        return
    
    if context is None: context = {}
    
    if hook_type == "SessionStart":
        context["start_time"] = time.time()
        log(f"🔗 [Hook:{ECC_HOOK_PROFILE}] Session Started.")
        
    elif hook_type == "SessionEnd":
        start_time = context.get("start_time")
        latency = int((time.time() - start_time) * 1000) if start_time else 0
        task_type = context.get("task_type", "unknown")
        tokens = context.get("tokens", 0)
        status = context.get("status", "success")
        
        # 非同步環境下需注意 log_metrics 是 async
        # 這裡在 handle_task 末尾直接調用 async version，或者在這裡處理
        pass 

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
    payload = {"content": redact_sensitive_data(content)}
    log(f"📡 Worker 正在發送訊息至頻道 {channel_id} (URL: {url})")
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code >= 200 and resp.status_code < 300:
        log(f"✅ Worker 發送 Discord 訊息成功! (Status: {resp.status_code})")
    else:
        log(f"❌ Worker 發送 Discord 訊息失敗: {resp.status_code} - {resp.text}")

from services.memory_engine import get_memory_context, save_session_memory
from services.toonify import optimize_text
from services.maintenance import run_self_audit
from services.presentation import generate_presentation


async def handle_task(task):
    task_type = task.get("type")
    payload = task.get("payload", {})
    
    # 產生任務 ID 用於追蹤 (Layer 2)
    task_id = str(uuid.uuid4())
    await TaskTraceService.create_trace(task_id, task_type, payload)
    
    log(f"👷 正在處理任務: {task_type} (ID: {task_id})")
    context = {
        "task_id": task_id,
        "task_type": task_type, 
        "start_time": time.time(), 
        "tokens": 0,
        "status": "pending"
    }
    
    await TaskTraceService.update_trace(task_id, status="IN_PROGRESS")
    run_hook("SessionStart", context)
    
    try:
        if task_type == "ask":
            # Phase 2: 優先嘗試使用 API 引擎 (無頭模式)
            message = payload.get("message", "")
            channel_id = payload.get("channel_id")
            author = payload.get("author")
            
            # --- Soul & Memory Engine 載入上下文 ---
            soul_content = get_soul_content()
            memory_ctx = await get_memory_context()
            
            from core.config import TOONIFY_ENABLED
            system_prompt = f"{soul_content}\n\n[Memory Context]\n{memory_ctx}"
            
            if TOONIFY_ENABLED:
                system_prompt = optimize_text(system_prompt)
                
            from core.config import ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY
            if ANTHROPIC_API_KEY or OPENAI_API_KEY or GEMINI_API_KEY:
                log(f"🧠 正在使用 API 引擎 (Headless) 處理: {message[:30]}...")
                ai_result = await get_ai_response_async(message, system_prompt=system_prompt)
                response = ai_result["text"]
                context["tokens"] = ai_result["tokens"]
                send_discord_msg(channel_id, f"🤖 **(API Mode)** {response}")
                
                 # --- Memory Engine 儲存 Session 摘要 ---
                await save_session_memory([message], response)
            else:
                # 降級方案: 呼叫 CDP 與 Antigravity 互動
                log(f"🌐 API Key 未設定，降級使用 CDP 注入: {message[:30]}...")
                await send_to_antigravity(prompt_with_memory, channel_id, author)
            
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
            
            if not is_safe_command(command):
                log(f"⛔ 指令已被 AgentShield 攔截: {command}")
                return
            
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
                
        elif task_type == "loop":
            # 執行自主維護循環
            log("🔄 收到自主維護任務 (Autonomous Loop)...")
            success = await run_self_audit()
            if success:
                log("✅ 自主維護任務完成。")
            else:
                log("❌ 自主維護任務部分失敗。")

        elif task_type == "presentation":
            # 建立簡報任務
            import re as _re
            topic = payload.get("topic", "LazyBridge Report")
            channel_id = payload.get("channel_id")
            author = payload.get("author", "System")
            log(f"🎨 正在為主題生成簡報: {topic}")
            
            from core.config import ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY
            has_api_key = ANTHROPIC_API_KEY or OPENAI_API_KEY or GEMINI_API_KEY
            
            if not has_api_key:
                # 無外部 API Key → 優先透過 CDP 注入 Antigravity
                log("🌐 API Key 未設定，嘗試透過 CDP 注入 Antigravity 生成簡報...")
                cdp_prompt = (
                    f"請為主題「{topic}」製作一份專業簡報。\n\n"
                    f"請產生一個 JSON 物件，格式如下：\n"
                    f'{{"title": "簡報標題", "sections": [{{"title": "投影片標題", "content": "投影片內容"}}]}}\n\n'
                    f"包含 4-6 頁投影片，內容要具體且專業。\n"
                    f"完成後，請使用 discord-sender MCP 工具的 send_message 將結果發送到頻道 {channel_id}。"
                )
                cdp_success = await send_to_antigravity(cdp_prompt, channel_id, author)
                if cdp_success:
                    log("✅ CDP 注入已送出，等待 Antigravity 回覆...")
                else:
                    log("❌ CDP 注入失敗，改用備用模板...")
                    if channel_id:
                        send_discord_msg(channel_id, "⚠️ CDP 連線異常，正在使用備用模板生成簡報...")
                
                # CDP 失敗時使用模板備援
                if not cdp_success:
                    template_sections = [
                        {"title": "📋 專案概述", "content": f"本簡報探討「{topic}」的核心架構、關鍵特色與未來發展方向。"},
                        {"title": "🏗️ 系統架構", "content": "• Discord Bot 前端 (discord.py)\\n• Redis 任務佇列 (異步解耦)\\n• Worker 後端處理引擎\\n• PostgreSQL 持久化儲存\\n• CDP 注入 Antigravity AI"},
                        {"title": "⭐ 核心特色", "content": "• SkyClaw 三層自癒架構 (斷路器 / 任務持久化 / 認知自我修正)\\n• AgentShield 安全防護 (指令攔截 + 資料遮罩)\\n• 模組化技能系統 (Skills)\\n• 每日自動晨報與新聞摘要"},
                        {"title": "🔮 未來展望", "content": "• 多 Agent 協作框架\\n• 向量記憶引擎 (RAG)\\n• 即時儀表板 (Dashboard)\\n• 插件市場 (Plugin Marketplace)\\n• 自動化 CI/CD 與部署"},
                        {"title": "🚀 行動方案", "content": "• Phase 5: 強化記憶引擎與上下文管理\\n• Phase 6: 建立 Agent-to-Agent 通訊協議\\n• Phase 7: 公開 API 與開發者工具包"}
                    ]
                    file_path = await generate_presentation(topic, template_sections)
                    if channel_id:
                        send_discord_msg(channel_id, f"✅ **簡報發布成功（備用模板）**！主題：{topic}\n報告已存檔於系統路徑：`{file_path}`")
            else:
                # 有 API Key → 直接透過 API 生成 JSON 並組裝簡報
                prompt = (
                    f"Create a structured presentation about '{topic}'. "
                    f"You MUST respond with ONLY a valid JSON object (no markdown, no explanation, no extra text). "
                    f"The JSON must follow this exact schema:\n"
                    f'{{"title": "簡報標題", "sections": [{{"title": "投影片標題", "content": "投影片內容"}}]}}\n'
                    f"Include 4-6 sections. Content should be concise bullet points."
                )
                
                # Layer 3: Cognitive Self-Correction (2 Automatic Retries)
                max_retries = 2
                presentation_success = False
                for attempt in range(max_retries + 1):
                    ai_result = await get_ai_response_async(prompt)
                    text = ai_result["text"]
                    log(f"🔍 [Attempt {attempt+1}] AI 回傳長度: {len(text)} chars")
                    
                    try:
                        json_str = None
                        if "```json" in text:
                            match = _re.search(r'```json\s*([\s\S]*?)\s*```', text)
                            if match:
                                json_str = match.group(1).strip()
                        elif "```" in text:
                            match = _re.search(r'```\s*([\s\S]*?)\s*```', text)
                            if match:
                                json_str = match.group(1).strip()
                        
                        if not json_str:
                            first_brace = text.find('{')
                            last_brace = text.rfind('}')
                            if first_brace != -1 and last_brace > first_brace:
                                json_str = text[first_brace:last_brace + 1]
                        
                        if not json_str:
                            raise ValueError("AI 回傳內容中找不到任何 JSON 結構")
                        
                        data = json.loads(json_str)
                        
                        if "title" not in data or "sections" not in data:
                            raise ValueError(f"JSON 缺少必要欄位, 實際欄位: {list(data.keys())}")
                        
                        file_path = await generate_presentation(data["title"], data["sections"])
                        
                        if channel_id:
                            send_discord_msg(channel_id, f"✅ **簡報發布成功**！主題：{data['title']}\n報告已存檔於系統路徑：`{file_path}`")
                        presentation_success = True
                        break
                        
                    except Exception as e:
                        if attempt < max_retries:
                            log(f"🔄 [Self-Correction] JSON 解析失敗 (Attempt {attempt+1}): {e}")
                            prompt = (
                                f"Your previous response was NOT valid JSON. Error: {e}\n\n"
                                f"Please respond with ONLY a raw JSON object, no markdown fences, no explanation.\n"
                                f"Schema: {{\"title\": \"string\", \"sections\": [{{\"title\": \"string\", \"content\": \"string\"}}]}}\n"
                                f"Topic: '{topic}'. Include 4-6 sections."
                            )
                        else:
                            log(f"❌ [Self-Correction] 超過重試次數，使用備用簡報: {e}")
                
                if not presentation_success:
                    fallback_data = {
                        "title": topic,
                        "sections": [
                            {"title": "概述", "content": f"關於 {topic} 的簡報。"},
                            {"title": "核心重點", "content": "AI 自動生成暫時無法完成，請手動補充內容。"},
                            {"title": "下一步", "content": "建議重新嘗試，或手動編輯此簡報。"}
                        ]
                    }
                    file_path = await generate_presentation(fallback_data["title"], fallback_data["sections"])
                    if channel_id:
                        send_discord_msg(channel_id, f"⚠️ AI 解析失敗，已生成備用簡報框架。\n報告已存檔於：`{file_path}`")

        else:
            log(f"⚠️ 未知的任務類型: {task_type}")
            
    except Exception as e:
        log(f"❌ Worker 處理任務出錯: {e}")
        await TaskTraceService.update_trace(task_id, status="FAILED", error_msg=str(e))
        context["status"] = "error"
        latency = int((time.time() - context["start_time"]) * 1000)
        await log_metrics(task_type, context["tokens"], latency, "error")
    else:
        await TaskTraceService.update_trace(task_id, status="COMPLETED")
        context["status"] = "success"
        latency = int((time.time() - context["start_time"]) * 1000)
        await log_metrics(task_type, context["tokens"], latency, "success")


# Concurrency Control
MAX_CONCURRENT_TASKS = int(os.getenv("MAX_CONCURRENT_TASKS", "5"))
semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

async def worker_task_wrapper(task):
    """Wrapper to handle a task within a semaphore and catch errors."""
    async with semaphore:
        try:
            await handle_task(task)
        except Exception as e:
            log(f"💥 Task wrapper caught unhandled error: {e}")

async def main():
    log(f"🚀 Worker 已啟動 (併發上限: {MAX_CONCURRENT_TASKS})，正在監聽 Redis 隊列...")
    while True:
        try:
            task = queue.pop_task(timeout=5)
            if task:
                # 使用 create_task 併發執行，不阻塞主迴圈
                asyncio.create_task(worker_task_wrapper(task))
        except Exception as e:
            log(f"❌ Worker Loop 異常: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
