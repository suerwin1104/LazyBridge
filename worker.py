import asyncio
import json
import os
import subprocess
from core.config import log, get_soul_content, REPORTS_BASE_URL
from core.queue import queue
from core.cdp import send_to_antigravity
from services.briefing import get_briefing_data, generate_briefing_html, format_briefing_text
from services.document_viewer import get_web_link
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
from services.local_rag import local_rag
from services.skill_manager import inject_skills, record_skill_outcome, seed_skills_from_rules
from services.post_mortem import analyze_failure, quick_reflect
from services.firecrawl_service import firecrawl_service
from services.social_service import SocialService
from services.pinchtab_service import get_pinchtab_service

social_service = SocialService(rag_service=local_rag)
pinchtab_service = get_pinchtab_service()


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
            
            # --- Local RAG Search ---
            log(f"🔍 執行本地 RAG 檢索: {message[:30]}...")
            rag_hits = await local_rag.search(message, top_k=3)
            rag_context = ""
            if rag_hits:
                rag_context = "\n[Local Knowledge Search Results]\n"
                for hit in rag_hits:
                    rag_context += f"- {hit['metadata'].get('text', '')}\n"
            
            # --- Dynamic Skill Injection (MetaClaw-inspired) ---
            skill_context = await inject_skills(message, task_type="ask")
            
            system_prompt = f"{soul_content}\n\n[Memory Context]\n{memory_ctx}{rag_context}{skill_context}"
            
            if TOONIFY_ENABLED:
                system_prompt = optimize_text(system_prompt)
                
                from core.config import ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY
                if ANTHROPIC_API_KEY or OPENAI_API_KEY or GEMINI_API_KEY:
                    log(f"🧠 正在使用 API 引擎 (Headless) 處理: {message[:30]}...")
                    ai_result = await get_ai_response_async(message, system_prompt=system_prompt)
                    response = ai_result["text"]
                    tokens = ai_result.get("tokens", 0)
                model_name = ai_result.get("model_name", "unknown")
                
                # --- 記錄效能指標 ---
                latency = int((time.time() - context["start_time"]) * 1000)
                await log_metrics("ask", tokens, latency, "success", model_name)
                
                send_discord_msg(channel_id, f"🤖 **(API Mode)** {response}")

                # --- Voice Output Integration ---
                # Check if the bot is in a voice channel for this guild
                # Note: Worker doesn't have direct access to bot.voice_clients, 
                # but we can check if voice is requested in payload or handle it simpler for now.
                voice_guild_id = payload.get("guild_id")
                if voice_guild_id:
                    # In a real scenario, we'd need a way to tell the bot to play.
                    # Since Worker and Bot are separate processes, we'll use the queue to send a 'speak' task back.
                    queue.push_task("command", {
                        "command": f"python -c \"import discord; from discord.ext import commands; # simplified trigger\"",
                        "task_name": "Voice Playback",
                        "channel_id": channel_id,
                    }, priority="high")
                    # BETTER: For now, let's just make sure the 'ask' command in commands.py 
                    # can trigger voice if the bot is in a VC.
                
                 # --- Memory Engine 儲存 Session 摘要 ---
                await save_session_memory([message], response)

                # --- Autonomous Routing: Detect BRAVO_BROWSE trigger ---
                if "BRAVO_BROWSE:" in response:
                    import re as _re
                    # 更加強健的正則表達式，支援選擇性引號與 Markdown 代碼塊
                    browse_match = _re.search(r'BRAVO_BROWSE:\s*["\']?(.*?)["\']?$', response, _re.MULTILINE)
                    if not browse_match:
                         # 嘗試非結尾匹配
                         browse_match = _re.search(r'BRAVO_BROWSE:\s*["\']?(.*?)["\']?(?:\n|$)', response)
                    
                    if browse_match:
                        browse_task_desc = browse_match.group(1).strip().strip('"').strip("'")
                        log(f"🤖 Mandy 啟動自主瀏覽任務: {browse_task_desc}")
                        queue.push_task("web_browse", {
                            "task": browse_task_desc,
                            "channel_id": channel_id
                        }, priority="high")
            else:
                # 降級方案: 呼叫 CDP 與 Antigravity 互動
                log(f"🌐 API Key 未設定，降級使用 CDP 注入: {message[:30]}...")
                # 這裡需要 prompt_with_memory
                prompt_with_memory = f"{system_prompt}\n\nUser: {message}"
                cdp_res = await send_to_antigravity(prompt_with_memory, channel_id, author)
                
                # 記錄 CDP 指標 (ask 任務下的 CDP 降級)
                if cdp_res is True:
                     est_tokens = len(prompt_with_memory) // 4
                     lat = int((time.time() - context["start_time"]) * 1000)
                     await log_metrics("ask", est_tokens, lat, "success", "Antigravity (CDP)")
            
        elif task_type == "cdp_ask":
            # 處理來自 Discord 的直接訊息
            # 優先嘗試 CDP 注入；若 UI 忙碌則自動降級為 API 引擎回覆
            message = payload.get("message", "")
            channel_id = payload.get("channel_id")
            author = payload.get("author", "User")
            
            log(f"🌐 準備透過 CDP 注入訊息: {message[:30]}...")
            
            # Phase 1: 嘗試 CDP 注入 (最多 3 次，共 15 秒)
            CDP_MAX_RETRIES = 3
            retry_count = 0
            cdp_success = False
            
            # --- Local RAG Search (CDP) ---
            log(f"🔍 執行本地 RAG 檢索 (CDP): {message[:30]}...")
            rag_hits = await local_rag.search(message, top_k=3)
            if rag_hits:
                rag_context = "\n[參考資料]\n"
                for hit in rag_hits:
                    rag_context += f"- {hit['metadata'].get('text', '')}\n"
                message_with_rag = f"{rag_context}\n請根據以上資料回答：{message}"
            else:
                message_with_rag = message

            while retry_count < CDP_MAX_RETRIES:
                result = await send_to_antigravity(message_with_rag, channel_id, author)
                
                if result is True:
                    cdp_success = True
                    break
                elif result == "__BUSY__":
                    retry_count += 1
                    log(f"⏳ Antigravity UI 忙碌，等待 5 秒後重試... ({retry_count}/{CDP_MAX_RETRIES})")
                    await asyncio.sleep(5)
                else:
                    # 連線錯誤等嚴重問題，直接跳到降級
                    break
            
            if cdp_success:
                log("✅ CDP 注入成功")
                # 估算 Token (輸入 + 系統提示)
                estimated_tokens = (len(message_with_rag) + 2000) // 4
                latency = int((time.time() - context["start_time"]) * 1000)
                await log_metrics("cdp_ask", estimated_tokens, latency, "success", "Antigravity (CDP)")
            else:
                # Phase 2: 自動降級為 API 引擎 (Headless Mode)
                log(f"🔀 [Self-Downgrade] CDP 忙碌/失敗，自動降級為 API 引擎回覆")
                if channel_id:
                    send_discord_msg(channel_id, "⏳ Antigravity 忙碌中，改用 API 引擎直接回覆...")
                
                try:
                    from core.config import ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY
                    has_api_key = ANTHROPIC_API_KEY or OPENAI_API_KEY or GEMINI_API_KEY
                    
                    if has_api_key:
                        soul_content = get_soul_content()
                        memory_ctx = await get_memory_context()
                        # --- Dynamic Skill Injection (Failover path) ---
                        skill_context = await inject_skills(message, task_type="cdp_ask")
                        system_prompt = f"{soul_content}\n\n[Memory Context]\n{memory_ctx}{skill_context}"
                        
                        ai_result = await get_ai_response_async(message, system_prompt=system_prompt)
                        response = ai_result["text"]
                        tokens = ai_result.get("tokens", 0)
                        model_name = ai_result.get("model_name", "unknown")
                        
                        latency = int((time.time() - context["start_time"]) * 1000)
                        await log_metrics("cdp_ask", tokens, latency, "success", f"{model_name} (Failover)")
                        
                        if channel_id:
                            send_discord_msg(channel_id, f"🤖 **(API Failover)** {response}")
                        await save_session_memory([message], response)
                    else:
                        log("❌ 無 API Key 可用，無法降級")
                        if channel_id:
                            send_discord_msg(channel_id, "❌ Antigravity 忙碌中且無 API Key 可降級，請稍後再試。")
                except Exception as api_err:
                    log(f"❌ API 降級處理失敗: {api_err}")
                    if channel_id:
                        send_discord_msg(channel_id, f"❌ API 降級失敗: `{api_err}`")

        elif task_type == "briefing":
            # 執行晨報生成
            channel_id = payload.get("channel_id")
            params = payload.get("params", {})
            log(f"📰 正在生成網頁版晨報...")
            # 1. 獲取結構化數據
            data = await get_briefing_data(**params)
            
            # 2. 生成 HTML 檔案
            html_path = await generate_briefing_html(data)
            report_url = f"{REPORTS_BASE_URL}/{os.path.basename(html_path)}"
            
            if channel_id:
                # 發送極簡版與網頁連結
                summary = f"**📅 {data['date']} 每日晨報已生成**\n\n🔗 **[點此查看完整網頁版晨報]({report_url})**"
                send_discord_msg(channel_id, summary)
                log(f"✅ 網頁版晨報已發送至頻道 {channel_id}: {report_url}")
                
        elif task_type == "command":
            # 執行系統指令
            channel_id = payload.get("channel_id")
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
                output_str = stdout.decode().strip()
                # 檢查指令輸出是否包含生成的檔案路徑
                import re
                file_match = re.search(r'(?:Generated|Saved|Output):?\s*([a-zA-Z0-9_\-\./\\]+\.[a-zA-Z0-9]+)', output_str)
                web_link_msg = ""
                if file_match:
                    file_path = file_match.group(1).split()[-1] # 取得最後路徑部分
                    if os.path.exists(file_path):
                        web_url = get_web_link(file_path)
                        if web_url:
                            web_link_msg = f"\n🌐 **[點此在網頁中檢視產出文件]({web_url})**"

                if channel_id:
                    send_discord_msg(channel_id, f"✅ **{task_name}** 執行成功！{web_link_msg}\n```\n{output_str[:1500]}\n```")
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
                    latency = int((time.time() - context["start_time"]) * 1000)
                    await log_metrics("presentation", 0, latency, "success", "Antigravity (CDP)")
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
                            send_discord_msg(channel_id, f"✅ **簡報發布成功**！主題：{data['title']}\n線上閱覽連結：{file_path}")
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
                        send_discord_msg(channel_id, f"⚠️ AI 解析失敗，已生成備用簡報框架。\n線上閱覽連結：{file_path}")

        elif task_type == "chub":
            # 處理 Context Hub 指令
            action = payload.get("action")
            args = payload.get("args", [])
            channel_id = payload.get("channel_id")
            log(f"📚 收到 Context Hub 請求: {action} {args}")
            
            from services.context_hub import search_chub, get_chub, annotate_chub
            
            if action == "search":
                query = args[0] if args else ""
                msg = await search_chub(query)
                if channel_id:
                    send_discord_msg(channel_id, msg)
            elif action == "get":
                doc_id = args[0] if args else ""
                lang = args[1] if len(args) > 1 else "py"
                success, msg = await get_chub(doc_id, lang)
                if channel_id:
                    send_discord_msg(channel_id, msg)
            elif action == "annotate":
                doc_id = args[0] if args else ""
                note = " ".join(args[1:]) if len(args) > 1 else ""
                msg = await annotate_chub(doc_id, note)
                if channel_id:
                    send_discord_msg(channel_id, msg)
                if channel_id:
                    send_discord_msg(channel_id, f"❌ 未知的 Context Hub 動作: {action}")

        elif task_type == "scrape":
            # Firecrawl 單頁抓取
            url = payload.get("url", "")
            channel_id = payload.get("channel_id")
            inject = payload.get("inject_to_rag", True)
            log(f"🔥 Firecrawl Scrape 任務: {url}")
            
            result = await firecrawl_service.scrape(url, inject_to_rag=inject)
            
            if result["status"] == "success":
                preview = result.get("markdown", "")[:500]
                msg = (
                    f"✅ **Scrape 完成**：{result['title']}\n"
                    f"📄 共 {result.get('char_count', 0):,} 字元已轉為 Markdown"
                )
                if inject:
                    msg += " 並匯入 RAG 知識庫"
                msg += f"\n\n> {preview}..." if preview else ""
                if channel_id:
                    send_discord_msg(channel_id, msg)
            else:
                if channel_id:
                    send_discord_msg(channel_id, f"❌ **Scrape 失敗**：{result.get('message', '未知錯誤')}")

        elif task_type == "site_crawl":
            # Firecrawl 全站爬取 + RAG 匯入
            url = payload.get("url", "")
            channel_id = payload.get("channel_id")
            max_pages = payload.get("max_pages", 50)
            include_paths = payload.get("include_paths")
            exclude_paths = payload.get("exclude_paths")
            log(f"🔥 Firecrawl 全站爬取任務: {url} (max: {max_pages})")
            
            if channel_id:
                send_discord_msg(channel_id, f"🕷️ **開始全站爬取**：{url}\n最多抓取 {max_pages} 頁，完成後自動匯入知識庫...")
            
            result = await firecrawl_service.crawl(
                url,
                max_pages=max_pages,
                include_paths=include_paths,
                exclude_paths=exclude_paths
            )
            
            if result["status"] == "success":
                msg = (
                    f"✅ **全站爬取完成**\n"
                    f"🌐 網站: {url}\n"
                    f"📄 爬取頁數: `{result['pages_crawled']}`\n"
                    f"📚 匯入 RAG 片段數: `{result['pages_injected']}`\n"
                    f"\n下次提問時 Mandy 就能參考這些知識了！"
                )
                if channel_id:
                    send_discord_msg(channel_id, msg)
            else:
                if channel_id:
                    send_discord_msg(channel_id, f"❌ **爬取失敗**：{result.get('message', '未知錯誤')}")

        elif task_type == "social_search":
            # Agent-Reach 社群搜尋
            query = payload.get("query", "")
            platform = payload.get("platform", "twitter")
            limit = payload.get("limit", 10)
            channel_id = payload.get("channel_id")
            
            log(f"🔥 Social Search 任務: {platform} - {query}")
            result = await social_service.search(query, platform=platform, limit=limit)
            
            if result["status"] == "success":
                items = result.get("results", [])
                if not items:
                    msg = f"🔎 **{platform.capitalize()} 搜尋結果**: 查無內容 ({query})"
                else:
                    msg = f"🔎 **{platform.capitalize()} 搜尋結果** (關鍵字: {query}):\n"
                    for item in items[:5]:  # 只顯示前 5 筆
                        title = item.get("title", item.get("text", ""))[:100]
                        url = item.get("url", "")
                        msg += f"- {title}\n  <{url}>\n"
                    if len(items) > 5:
                        msg += f"...以及其他 {len(items)-5} 筆結果。"
                
                if channel_id:
                    send_discord_msg(channel_id, msg)
            else:
                if channel_id:
                    send_discord_msg(channel_id, f"❌ **社群搜尋失敗**：{result.get('message', '未知錯誤')}")

        elif task_type == "social_read":
            # Agent-Reach 社群內容擷取 + RAG
            url = payload.get("url", "")
            channel_id = payload.get("channel_id")
            inject = payload.get("inject_to_rag", True)
            
            log(f"🔥 Social Read 任務: {url}")
            result = await social_service.read_and_inject(url, inject_to_rag=inject)
            
            if result["status"] == "success":
                msg = (
                    f"✅ **社群擷取完成**：{result['title']}\n"
                    f"📄 共 {result.get('char_count', 0):,} 字元已解析"
                )
                if inject:
                    msg += " 並匯入 RAG 知識庫"
                
                if channel_id:
                    send_discord_msg(channel_id, msg)
            else:
                if channel_id:
                    send_discord_msg(channel_id, f"❌ **社群擷取失敗**：{result.get('message', '未知錯誤')}")

        elif task_type == "social_config":
            # 配置 Agent-Reach (如 Twitter Cookies)
            platform = payload.get("platform")
            value = payload.get("value")
            channel_id = payload.get("channel_id")
            
            result = await social_service.configure(platform, value)
            if result["status"] == "success":
                if channel_id:
                    send_discord_msg(channel_id, f"✅ **{platform.capitalize()} 配置成功**！")
            else:
                if channel_id:
                    send_discord_msg(channel_id, f"❌ **配置失敗**：{result.get('message', '未知錯誤')}")

        elif task_type == "strategic":
            # 任務：大局拆解 (Project Great Planner)
            log("🎯 [Strategic] 收到大局規劃任務...")
            from services.planner_engine import planner
            big_task = payload.get("task", "")
            channel_id = payload.get("channel_id")
            
            if channel_id:
                from core.discord_utils import send_discord_msg
                send_discord_msg(channel_id, f"🧠 **正在啟動 Strategic Mode**...\n目標：{big_task[:200]}...")
                
            plan = await planner.decompose_task(big_task)
            if plan and "sub_tasks" in plan:
                if channel_id:
                    steps_desc = "\n".join([f"- {s.get('type')}: {s.get('description', '無')}" for s in plan['sub_tasks']])
                    send_discord_msg(channel_id, f"📋 **規劃完成**：{plan.get('plan_title')}\n拆解步驟：\n{steps_desc}\n\n🚀 開始執行子任務隊列...")
                
                for sub in plan["sub_tasks"]:
                    # 將子任務推回隊列，繼承 channel_id
                    sub_payload = sub.get("payload", {})
                    if channel_id and "channel_id" not in sub_payload:
                        sub_payload["channel_id"] = channel_id
                        
                    queue.push_task(sub.get("type"), sub_payload)
                    log(f"➕ [Strategic] 已加入子任務: {sub.get('type')}")
            else:
                if channel_id:
                    send_discord_msg(channel_id, "❌ **任務拆解失敗**，請檢查日誌或 AI 狀態。")

        elif task_type == "web_browse":
            # 處理 AI 瀏覽器自主任務 (browser-use)
            browser_task = payload.get("task")
            channel_id = payload.get("channel_id")
            log(f"🌐 啟動 AI 瀏覽器自主任務: {browser_task}")
            
            from services.browser_agent import browse_and_summarize
            result = await browse_and_summarize(browser_task)
            
            if result["status"] == "success":
                summary = result.get("result", "任務完成，但未產出摘要。")
                if channel_id:
                    send_discord_msg(channel_id, f"✅ **AI 瀏覽器任務完成**！\n🔍 **任務回報**：\n{summary}")
                log("✅ AI 瀏覽器任務成功。")
            else:
                error_msg = result.get("message", "未知錯誤")
                if channel_id:
                    send_discord_msg(channel_id, f"❌ **AI 瀏覽器任務失敗**：\n`{error_msg}`")
                log(f"❌ AI 瀏覽器任務失敗: {error_msg}")

        # --- PinchTab Tasks ---
        elif task_type == "pinch_health":
            channel_id = payload.get("channel_id")
            res = await pinchtab_service.get_health()
            if channel_id:
                status_icon = "🟢" if res.get("status") == "success" else "🔴"
                msg = f"{status_icon} **PinchTab Health**: {json.dumps(res, indent=2)}"
                send_discord_msg(channel_id, msg)

        elif task_type == "pinch_browse":
            url = payload.get("url")
            channel_id = payload.get("channel_id")
            log(f"🦀 [PinchTab] Navigating to: {url}")
            
            # Use quick_browse for one-off tasks
            res = await pinchtab_service.quick_browse(url)
            
            if res["status"] == "success":
                text_preview = res.get("text", "")[:1000]
                msg = (
                    f"✅ **PinchTab 導航成功**！\n"
                    f"🌐 URL: {url}\n"
                    f"🆔 Instance: `{res['instance_id']}` | Tab: `{res['tab_id']}`\n\n"
                    f"📝 **內容摘要**:\n```\n{text_preview}\n```\n"
                    f"💡 *此操作已自動屏蔽廣告與無關 DOM，節省 Token 並提升隱身性。*"
                )
                if channel_id:
                    send_discord_msg(channel_id, msg)
                
                # Optionally inject to RAG
                if payload.get("inject_to_rag", True):
                    await social_service._inject_to_rag(url, f"PinchTab: {url}", res.get("text", ""))
            else:
                if channel_id:
                    send_discord_msg(channel_id, f"❌ **PinchTab 導航失敗**：{res.get('message', '未知錯誤')}")

        elif task_type == "pinch_snapshot":
            tab_id = payload.get("tab_id")
            channel_id = payload.get("channel_id")
            res = await pinchtab_service.get_snapshot(tab_id)
            if channel_id:
                if res.get("status") == "success":
                    snapshot = json.dumps(res.get("snapshot"), indent=2)[:1900]
                    send_discord_msg(channel_id, f"📸 **PinchTab Snapshot (Accessibility Tree)**:\n```json\n{snapshot}\n```")
                else:
                    send_discord_msg(channel_id, f"❌ **快照讀取失敗**: {res.get('message')}")

        else:
            log(f"⚠️ 未知的任務類型: {task_type}")
            
    except Exception as e:
        log(f"❌ Worker 處理任務出錯: {e}")
        await TaskTraceService.update_trace(task_id, status="FAILED", error_msg=str(e))
        context["status"] = "error"
        latency = int((time.time() - context["start_time"]) * 1000)
        await log_metrics(task_type, context["tokens"], latency, "error")
        
        # --- Post-Mortem Evolution (MetaClaw-inspired) ---
        try:
            user_msg = payload.get("message", payload.get("task", ""))
            await analyze_failure(task_type, payload, e, context)
            await record_skill_outcome(task_type, user_msg, success=False)
        except Exception as pm_err:
            log(f"⚠️ [PostMortem] 反思流程異常 (不影響主流程): {pm_err}")
            # 退而求其次：使用不依賴 AI 的快速反思
            try:
                await quick_reflect(task_type, e, payload)
            except Exception:
                pass
        
    else:
        await TaskTraceService.update_trace(task_id, status="COMPLETED")
        context["status"] = "success"
        latency = int((time.time() - context["start_time"]) * 1000)
        await log_metrics(task_type, context["tokens"], latency, "success")
        
        # --- Record Skill Effectiveness on Success ---
        try:
            user_msg = payload.get("message", payload.get("task", ""))
            await record_skill_outcome(task_type, user_msg, success=True)
        except Exception:
            pass


# Concurrency Control Pipelines (Multi-Pipeline Architecture)
UI_CONCURRENCY = 1 # VS Code UI is strictly sequential
BROWSER_CONCURRENCY = 2 # Heavy headless browsers
BG_CONCURRENCY = int(os.getenv("MAX_CONCURRENT_TASKS", "5"))

ui_semaphore = asyncio.Semaphore(UI_CONCURRENCY)
browser_semaphore = asyncio.Semaphore(BROWSER_CONCURRENCY)
bg_semaphore = asyncio.Semaphore(BG_CONCURRENCY)

# 管道降級映射表：主管道忙碌時，任務可以降級到替代管道
# 格式: { task_type: (fallback_task_type, fallback_semaphore, fallback_pipeline_name) }
PIPELINE_FAILOVER = {
    "cdp_ask": ("ask", bg_semaphore, "Background"),      # UI 忙 → 降級為 API 引擎
    "presentation": (None, bg_semaphore, "Background"),   # UI 忙 → 排隊等待 (簡報無法降級)
    "web_browse": (None, bg_semaphore, "Background"),     # Browser 忙 → 排隊等待
}

async def worker_task_wrapper(task):
    """Wrapper with pipeline failover: if primary pipeline is busy, route to alternative."""
    task_type = task.get('type', 'unknown')
    priority = task.get('priority', 'default')
    log(f"🔥 DEBUG: Entered worker_task_wrapper for task {task_type} [Priority: {priority}]")
    
    # 決定任務所屬的主管道 (Primary Pipeline)
    if task_type in ["cdp_ask", "presentation"]:
        primary_semaphore = ui_semaphore
        pipeline_name = "UI"
    elif task_type == "web_browse":
        primary_semaphore = browser_semaphore
        pipeline_name = "Browser"
    else:
        primary_semaphore = bg_semaphore
        pipeline_name = "Background"

    # 嘗試非阻塞地取得主管道
    if primary_semaphore.locked():
        # 主管道忙碌！嘗試降級
        failover = PIPELINE_FAILOVER.get(task_type)
        if failover and failover[0]:
            fallback_type, fallback_sem, fallback_name = failover
            log(f"🔀 [Failover] {pipeline_name} 管道忙碌中！任務 '{task_type}' 降級為 '{fallback_type}'，轉入 {fallback_name} 管道")
            task["type"] = fallback_type
            # 保留原始 payload，handle_task 的 ask 分支會使用 API 引擎處理
            async with fallback_sem:
                log(f"🚦 [Pipeline: {fallback_name} (Failover)] Acquired semaphore for task: {fallback_type}")
                try:
                    await handle_task(task)
                except Exception as e:
                    log(f"💥 Task wrapper caught unhandled error: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                    log(f"🚦 [Pipeline: {fallback_name} (Failover)] Released semaphore")
            return
        else:
            log(f"⏳ [Pipeline: {pipeline_name}] 管道忙碌，此任務無法降級，排隊等待中...")

    # 正常路徑：取得主管道 Semaphore (若忙碌則等待)
    async with primary_semaphore:
        log(f"🚦 [Pipeline: {pipeline_name}] Acquired semaphore for task: {task_type}")
        try:
            await handle_task(task)
        except Exception as e:
            log(f"💥 Task wrapper caught unhandled error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            log(f"🚦 [Pipeline: {pipeline_name}] Released semaphore for task: {task_type}")

async def heartbeat_loop():
    """Background task to run maintenance and report health every 15 minutes."""
    log("💓 [Heartbeat] Aegis Monitoring Started.")
    while True:
        try:
            # 啟動自癒與維護循環
            await run_self_audit()
            await asyncio.sleep(900) # 15 minutes
        except Exception as e:
            log(f"❌ [Heartbeat] Loop error: {e}")
            await asyncio.sleep(60)

async def main():
    log(f"🚀 Worker 已啟動 (管道: UI={UI_CONCURRENCY}, Browser={BROWSER_CONCURRENCY}, BG={BG_CONCURRENCY})，正在監聽 Redis 隊列...")
    
    # --- 資料庫初始化 ---
    from core.database import init_db
    try:
        await init_db()
    except Exception as e:
        log(f"⚠️ 資料庫初始化失敗: {e}")

    # --- 冷啟動：從 rules/ 載入靜態規則作為技能種子 ---
    try:
        await seed_skills_from_rules()
        log("✅ [SkillManager] 技能庫初始化完成")
    except Exception as e:
        log(f"⚠️ [SkillManager] 技能庫初始化失敗 (不阻塞啟動): {e}")
    
    # --- 啟動 Aegis 心跳監控 ---
    asyncio.create_task(heartbeat_loop())

    # --- 啟動 Omni-View API Server & Dashboard ---
    from services.api_server import start_api_server
    try:
        asyncio.create_task(start_api_server(port=8088))
    except Exception as e:
        log(f"⚠️ [Omni-View] API Server 啟動失敗: {e}")

    # --- 啟動 Hive Sync 知識同步服務 ---
    from services.sync_engine import hive_sync_loop
    asyncio.create_task(hive_sync_loop())
    
    while True:
        try:
            task = queue.pop_task()
            if task:
                log(f"🔥 DEBUG: Popped task from queue: {task['type']}")
                # 使用 create_task 併發執行，不阻塞主迴圈
                asyncio.create_task(worker_task_wrapper(task))
            else:
                # 讓出事件迴圈控制權，避免 100% CPU，也讓其他 tasks (如 DB 連線) 有時間執行
                await asyncio.sleep(1)
        except Exception as e:
            log(f"❌ Worker Loop 異常: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
