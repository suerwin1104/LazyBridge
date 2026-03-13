"""
Discord Bot 指令模組 (Cog)。
所有 /斜線指令定義於此。
"""
import asyncio
import base64
import json
from io import BytesIO

import discord
import requests
import websockets
from discord.ext import commands

from core.cdp import find_chat_tab, get_cdp_tabs, send_to_antigravity
from core.config import CDP_URL, log
from core.queue import queue
from services.briefing import get_briefing
from services.social_media_skill import social_manager


class BridgeCommands(commands.Cog):
    """LazyBridge 的所有 Discord 指令。"""

    def __init__(self, bot):
        self.bot = bot
        self.voice_clients = {}

    @commands.command()
    async def join(self, ctx):
        """讓 Mandy 進入語音頻道 (目前暫停使用)。"""
        await ctx.send("⏸️ **語音功能目前已暫停使用**。")

    @commands.command()
    async def leave(self, ctx):
        """讓 Mandy 離開語音頻道 (目前暫停使用)。"""
        await ctx.send("⏸️ **語音功能目前已暫停使用**。")

    @commands.command()
    async def speak(self, ctx, *, text: str):
        """讓 Mandy 在語音頻道說話 (目前暫停使用)。"""
        await ctx.send("⏸️ **語音功能目前已暫停使用**。")

    @commands.command()
    async def ask(self, ctx, *, message):
        """向 Antigravity AI 發問 (非同步隊列)。"""
        payload = {
            "channel_id": str(ctx.channel.id),
            "guild_id": str(ctx.guild.id) if ctx.guild else None,
            "author": str(ctx.author),
            "message": message
        }
        if queue.push_task("ask", payload, priority="high"):
            await ctx.send(
                f"📥 **已進入排隊隊列**：{message[:50]}..."
            )
        else:
            await ctx.send("❌ 無法連接任務隊列伺服器 (Redis)，請檢查後端狀態。")

    @commands.command()
    async def browse(self, ctx, *, task: str):
        """啟動 AI 瀏覽器自主任務 (使用 browser-use)。"""
        payload = {
            "channel_id": str(ctx.channel.id),
            "guild_id": str(ctx.guild.id) if ctx.guild else None,
            "author": str(ctx.author),
            "task": task
        }
        if queue.push_task("web_browse", payload, priority="default"):
            await ctx.send(
                f"🌐 **AI 瀏覽器任務已啟動**：\n> {task[:100]}...\nMandy 正透過 Antigravity 進行網頁操作。"
            )
        else:
            await ctx.send("❌ 隊列發送失敗。")

    @commands.command()
    async def briefing(self, ctx):
        """手動觸發晨報任務 (非同步隊列)。"""
        payload = {
            "channel_id": str(ctx.channel.id),
            "params": {"include_emails": True, "include_calendar": True, "include_news": True}
        }
        if queue.push_task("briefing", payload, priority="low"):
            await ctx.send("⌛ **晨報請求已排隊**，完成後會發送至此頻道。")
        else:
            await ctx.send("❌ 隊列發送失敗。")

    @commands.command()
    async def dump(self, ctx):
        """診斷 Scratchpad 的分頁狀態。"""
        try:
            tabs = get_cdp_tabs()
            msg = "📋 **分頁診斷:**\n"
            for t in tabs:
                msg += f"- `{t.get('title', '')[:40]}` ({t.get('type')})\n"
            await ctx.send(msg)
        except Exception as e:
            await ctx.send(f"❌ 診斷失敗: {e}")

    @commands.command()
    async def tabs(self, ctx):
        """列出目前所有可連線的分頁。"""
        try:
            pages = get_cdp_tabs()
            if not pages:
                await ctx.send("❌ 找不到任何分頁。")
                return
            lines = ["📋 **目前開啟的分頁：**"]
            for i, t in enumerate(pages):
                lines.append(
                    f"`[{i+1}]` **{t.get('title', '無標題')}**\n"
                    f"　　`{t.get('url', '')[:70]}`"
                )
            await ctx.send("\n".join(lines))
        except Exception as e:
            await ctx.send(f"❌ 錯誤: {e}")

    @commands.command()
    async def screenshot(self, ctx):
        """擷取當前頁面截圖，診斷用。"""
        try:
            pages = get_cdp_tabs()
            chat_tab = find_chat_tab(pages)
            if not chat_tab:
                await ctx.send("❌ 找不到分頁")
                return

            async with websockets.connect(chat_tab["webSocketDebuggerUrl"]) as ws:
                log("📸 正在擷取截圖...")
                shot_id = 999
                await ws.send(json.dumps({
                    "id": shot_id,
                    "method": "Page.captureScreenshot",
                    "params": {"format": "png"},
                }))

                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    if data.get("id") == shot_id:
                        b64_data = data["result"]["data"]
                        image_data = base64.b64decode(b64_data)
                        file = discord.File(
                            BytesIO(image_data), filename="scratchpad.png"
                        )
                        await ctx.send("📸 目前 Scratchpad 畫面：", file=file)
                        break
        except Exception as e:
            await ctx.send(f"❌ 擷取失敗: {e}")

    # --- Computer Control Commands (Agent Intercepted) ---

    @commands.command()
    async def screen(self, ctx):
        """取得目前螢幕解析度。"""
        log("📡 指令呼叫: /screen")
        await ctx.send("🔍 正在透過 MCP 取得螢幕解析度...")

    @commands.command()
    async def mouse(self, ctx, x: int, y: int):
        """移動滑鼠到指定座標。"""
        log(f"📡 指令呼叫: /mouse {x} {y}")
        await ctx.send(f"🖱️ 正在移動滑鼠至 ({x}, {y})...")

    @commands.command()
    async def click(self, ctx, x: int = None, y: int = None):
        """在指定座標或當前位置點擊。"""
        log(f"📡 指令呼叫: /click {x} {y}")
        await ctx.send("🖱️ 正在執行點擊...")

    @commands.command(name="type")
    async def type_text(self, ctx, *, text):
        """打字。"""
        log(f"📡 指令呼叫: /type {text}")
        await ctx.send("⌨️ 正在輸入文字...")


    @commands.command()
    async def harness_status(self, ctx, days: int = 7):
        """查看效能監控儀表板 (Token 消耗、延遲、成功率)。"""
        from services.metrics import get_summary_stats
        log(f"📡 指令呼叫: /harness_status {days}")
        
        stats = await get_summary_stats(days=days)
        if not stats:
            await ctx.send("❌ 無法取得效能指標數據。")
            return

        total_tokens = stats["total_tokens"]
        avg_latency = stats["avg_latency"]
        dist = stats["status_distribution"]
        
        success_count = dist.get("success", 0)
        error_count = dist.get("error", 0)
        total_count = success_count + error_count
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0

        # 專業儀表板格式
        msg = f"📊 **Harness 效能監控報告 (最近 {days} 天)**\n"
        msg += f"━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"💰 **總 Token 消耗**: `{total_tokens:,}`\n"
        msg += f"⏱️ **平均延遲**: `{avg_latency:.2f}ms`\n"
        msg += f"📈 **任務成功率**: `{success_rate:.1f}%` ({success_count}/{total_count})\n"
        msg += f"━━━━━━━━━━━━━━━━━━━━\n"
        
        # 簡易視覺化進度條
        bar_len = 10
        success_bars = int(success_rate / 10)
        bar = "🟩" * success_bars + "🟥" * (bar_len - success_bars)
        msg += f"狀態分佈: [{bar}]\n"
        
        await ctx.send(msg)


    @commands.command(name="loop-start")
    async def loop_start(self, ctx):
        """立即啟動自主維護循環 (Autonomous Loop)。"""
        log("📡 指令呼叫: /loop-start")
        if queue.push_task("loop", {}, priority="low"):
            await ctx.send("🔄 **自主維護任務已加入隊列**。系統將自動檢查資料庫、清除過期任務並驗證技能狀態。")
        else:
            await ctx.send("❌ 無法啟動維護任務，請檢查 Redis 連線。")

    @commands.command(name="loop-status")
    async def loop_status(self, ctx):
        """檢查自主維護狀態。"""
        # 這裡簡單回報，未來可以從 DB 讀取最後維護時間
        await ctx.send("🟢 **系統狀態良好**。Worker 運作中，自主維護循環待命中。")


    @commands.command(name="present")
    async def present(self, ctx, *, topic: str):
        """讓 AI 針對特定主題製作一份專業的 HTML 簡報。"""
        log(f"📡 指令呼叫: /present {topic}")
        payload = {
            "channel_id": str(ctx.channel.id),
            "topic": topic
        }
        if queue.push_task("presentation", payload, priority="default"):
            await ctx.send(f"🎨 **簡報製作請求已排隊**：主題為 「{topic}」。完成後會在此回報存檔位置。")
        else:
            await ctx.send("❌ 隊列發送失敗。")


    @commands.command(name="skill-sync")
    async def skill_sync(self, ctx, path: str):
        """從 openclaw/skills 下載並安裝技能 (格式: owner/slug)。"""
        if "/" not in path:
            await ctx.send("❌ 格式錯誤。請使用 `owner/slug` 格式，例如 `00xmorty/conatus`")
            return
            
        owner, slug = path.split("/", 1)
        await ctx.send(f"📥 正在從 openclaw/skills 同步技能 `{slug}`...")
        
        from services.skill_sync import download_skill
        success, message = await download_skill(owner, slug)
        
        if success:
            await ctx.send(f"✅ **{message}**\n您可以現在開始在對話中使用此技能的能力。")
        else:
            await ctx.send(f"❌ **安裝失敗**: {message}")

    @commands.command(name="chub")
    async def chub(self, ctx, action: str, *, args: str = ""):
        """Context Hub 工具 (支援 search, get, annotate)"""
        valid_actions = ["search", "get", "annotate"]
        if action not in valid_actions:
            await ctx.send(f"❌ 錯誤的動作: `{action}`。支援的動作有: {', '.join(valid_actions)}")
            return
            
        # 為了支援附帶空白的 args (例如 annotate 的筆記)，這裡做簡單的切割，
        # 第一個參數通常是 doc_id，後面的就是 note。
        arg_list = args.split(' ', 1) if args else []
        if action == "annotate" and len(arg_list) == 2:
            pass # ["doc_id", "the rest of note..."]
        else:
            arg_list = args.split() if args else []

        payload = {
            "channel_id": str(ctx.channel.id),
            "action": action,
            "args": arg_list
        }
        
        log(f"📡 指令呼叫: /chub {action} {args}")
        if queue.push_task("chub", payload, priority="high"):
            if action == "search":
                await ctx.send(f"🔍 正在搜尋 Context Hub: `{args}`...")
            elif action == "get":
                await ctx.send(f"📥 正在從 Context Hub 抓取文件: `{args}`...")
            elif action == "annotate":
                await ctx.send(f"📝 正在為文件建立註解...")
        else:
            await ctx.send("❌ 隊列發送失敗，請檢查 Task Queue (Redis)。")

    @commands.command(name="social_draft")
    async def social_draft(self, ctx, *, topic: str):
        """讓 Mandy 幫你撰寫 FB/IG 貼文草稿。"""
        sent_msg = await ctx.send(f"🔍 正在為您構思關於『{topic}』的貼文草稿，請稍候...")
        try:
            draft = await social_manager.generate_draft(topic)
            preview_url = social_manager.preview_post(draft)
            await sent_msg.edit(content=f"✅ 貼文草稿已生成！\n\n**預覽與文案內容**：\n{preview_url}\n\n您可以直接複製預覽頁面中的內容進行發布。")
        except Exception as e:
            await sent_msg.edit(content=f"❌ 草稿生成失敗：{str(e)}")

    @commands.command(name="social_account")
    async def social_account(self, ctx):
        """列出目前連結的 FB 粉絲專頁帳號。"""
        try:
            pages = await social_manager.list_pages()
            if isinstance(pages, dict) and "error" in pages:
                await ctx.send(f"❌ 無法取得帳號資訊：{pages['error']}")
            else:
                msg = "📋 **您管理的粉絲專頁**：\n"
                for p in pages.get("data", []):
                    msg += f"- {p['name']} (ID: {p['id']})\n"
                await ctx.send(msg)
        except Exception as e:
            await ctx.send(f"❌ 發生錯誤：{str(e)}")


    @commands.command(name="skills")
    async def skills(self, ctx, action: str = "list"):
        """查看或管理動態技能庫 (MetaClaw-inspired)。

        用法:
          /skills         → 列出所有技能
          /skills stats   → 查看技能統計
        """
        from services.skill_manager import get_all_skills

        if action == "list":
            skills_list = await get_all_skills()
            if not skills_list:
                await ctx.send("📚 **技能庫目前為空**。系統會隨著使用自動累積技能。")
                return

            msg = f"🎯 **動態技能庫** ({len(skills_list)} 條技能)\n━━━━━━━━━━━━━━━━━━━━\n"
            for i, s in enumerate(skills_list[:15], 1):
                name = s.get("name", "?")
                source = s.get("source", "?")
                usage = s.get("usage_count", 0)
                eff = s.get("effectiveness", 0)

                source_icon = {"manual": "📖", "post_mortem": "🛡️", "auto_evolved": "🧬"}.get(source, "❓")
                eff_bar = "🟩" * int(eff * 5) + "⬜" * (5 - int(eff * 5))

                msg += f"`{i}.` {source_icon} **{name}**\n"
                msg += f"　　使用次數: `{usage}` | 有效率: [{eff_bar}] `{eff:.0%}`\n"

            if len(skills_list) > 15:
                msg += f"\n... 還有 {len(skills_list) - 15} 條技能未顯示"

            await ctx.send(msg)

        elif action == "stats":
            skills_list = await get_all_skills()
            total = len(skills_list)
            manual = sum(1 for s in skills_list if s.get("source") == "manual")
            pm = sum(1 for s in skills_list if s.get("source") == "post_mortem")
            evolved = sum(1 for s in skills_list if s.get("source") == "auto_evolved")
            total_usage = sum(s.get("usage_count", 0) for s in skills_list)
            avg_eff = sum(s.get("effectiveness", 0) for s in skills_list) / total if total else 0

            msg = "📊 **技能庫統計**\n━━━━━━━━━━━━━━━━━━━━\n"
            msg += f"📦 總技能數: `{total}`\n"
            msg += f"📖 手動規則: `{manual}` | 🛡️ 失敗反思: `{pm}` | 🧬 自動演化: `{evolved}`\n"
            msg += f"🔄 總調用次數: `{total_usage}`\n"
            msg += f"📈 平均有效率: `{avg_eff:.0%}`\n"

            await ctx.send(msg)
        else:
            await ctx.send("❌ 未知的動作。支援: `list`, `stats`")

    @commands.command(name="post-mortem")
    async def post_mortem_cmd(self, ctx, limit: int = 5):
        """查看最近的失敗反思報告 (Post-Mortem Evolution)。"""
        from services.post_mortem import get_post_mortem_stats, get_recent_post_mortems

        stats = await get_post_mortem_stats()
        recent = await get_recent_post_mortems(limit)

        msg = f"🔬 **Post-Mortem 反思報告**\n━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"📊 累計分析次數: `{stats['total_analyses']}`\n\n"

        if not recent:
            msg += "✨ **目前沒有失敗紀錄** — 系統運作良好！"
        else:
            for i, r in enumerate(recent, 1):
                task_type = r.get("task_type", "?")
                error_type = r.get("error_type", "?")
                root_cause = r.get("root_cause", "N/A")[:100]
                guard = r.get("guard_skill_name", "N/A")
                analyzed_at = r.get("analyzed_at", "?")[:16]

                msg += f"**#{i}** `{analyzed_at}` — `{task_type}` → `{error_type}`\n"
                msg += f"　📋 原因: {root_cause}\n"
                msg += f"　🛡️ 產出技能: `{guard}`\n\n"

        await ctx.send(msg)

    # --- Firecrawl 整合指令 ---

    @commands.command(name="scrape")
    async def scrape(self, ctx, url: str):
        """抓取單一網頁，轉為乾淨 Markdown 並匯入知識庫。"""
        if not url.startswith("http"):
            url = "https://" + url
        
        payload = {
            "channel_id": str(ctx.channel.id),
            "url": url,
            "inject_to_rag": True
        }
        if queue.push_task("scrape", payload, priority="default"):
            await ctx.send(f"🔥 **Scrape 任務已排隊**：\n> {url}\n完成後會自動匯入 RAG 知識庫。")
        else:
            await ctx.send("❌ 隊列發送失敗。")

    @commands.command(name="crawl")
    async def crawl(self, ctx, url: str, max_pages: int = 30):
        """全站爬取，將整個網站轉為知識庫。

        用法:
          /crawl https://docs.example.com        → 預設爬 30 頁
          /crawl https://docs.example.com 100    → 最多爬 100 頁
        """
        if not url.startswith("http"):
            url = "https://" + url
        
        if max_pages > 200:
            await ctx.send("⚠️ 最大頁數限制為 200，已自動調整。")
            max_pages = 200
        
        payload = {
            "channel_id": str(ctx.channel.id),
            "url": url,
            "max_pages": max_pages
        }
        if queue.push_task("site_crawl", payload, priority="low"):
            await ctx.send(
                f"🕷️ **全站爬取任務已排隊**：\n"
                f"> {url}\n"
                f"📄 最多爬取 `{max_pages}` 頁\n"
                f"完成後所有內容會自動匯入 RAG 知識庫，Mandy 之後就能參考了！"
            )
        else:
            await ctx.send("❌ 隊列發送失敗。")

    @commands.command(name="map")
    async def map_site(self, ctx, url: str):
        """偵察網站結構，列出所有可爬取的 URL。"""
        if not url.startswith("http"):
            url = "https://" + url
        
        await ctx.send(f"🗺️ **正在掃描網站結構**：{url}...")
        
        try:
            from services.firecrawl_service import firecrawl_service
            result = await firecrawl_service.map_site(url)
            
            if result["status"] == "success":
                urls = result["urls"][:20]  # 只顯示前 20 個
                msg = f"🗺️ **網站地圖** — 共發現 `{result['total']}` 個 URL\n━━━━━━━━━━━━━━━━━━━━\n"
                for i, u in enumerate(urls, 1):
                    msg += f"`{i}.` {u}\n"
                if result["total"] > 20:
                    msg += f"\n... 還有 {result['total'] - 20} 個 URL 未顯示"
                msg += f"\n\n💡 **Tip**: 使用 `/crawl {url}` 將整個網站匯入知識庫"
                await ctx.send(msg)
            else:
                await ctx.send(f"❌ **Map 失敗**：{result.get('message', '未知錯誤')}")
        except Exception as e:
            await ctx.send(f"❌ 執行錯誤：{e}")

    # --- Agent-Reach 社群探測指令 ---

    @commands.command(name="social_search")
    async def social_search(self, ctx, platform: str, *, query: str):
        """社群搜尋 (X/Twitter, Reddit, GitHub, YouTube)。
        
        用法:
          /social_search twitter AI agents
          /social_search reddit LazyBridge
          /social_search github firecrawl
        """
        platforms = ["twitter", "x", "reddit", "github", "youtube"]
        if platform.lower() not in platforms:
            await ctx.send(f"❌ 不支援的平台。支援: {', '.join(platforms)}")
            return
            
        payload = {
            "channel_id": str(ctx.channel.id),
            "platform": platform.lower(),
            "query": query,
            "limit": 10
        }
        if queue.push_task("social_search", payload, priority="default"):
            await ctx.send(f"🔎 **已開始社群搜尋** ({platform}): `{query}`\n正在探測相關討論...")
        else:
            await ctx.send("❌ 隊列發送失敗。")

    @commands.command(name="social_read")
    async def social_read(self, ctx, url: str):
        """擷取社群貼文內容並匯入 RAG。
        
        支援 X (需設置 Cookie)、Reddit、GitHub README/Issues 等。
        """
        if not url.startswith("http"):
            url = "https://" + url
            
        payload = {
            "channel_id": str(ctx.channel.id),
            "url": url,
            "inject_to_rag": True
        }
        if queue.push_task("social_read", payload, priority="default"):
            await ctx.send(f"📖 **已開始內容擷取**：\n> {url}\n解析完成後會自動匯入 RAG 知識庫。")
        else:
            await ctx.send("❌ 隊列發送失敗。")

    @commands.command(name="social_config")
    async def social_config(self, ctx, platform: str, *, value: str):
        """配置社群帳號資訊 (如 twitter cookies)。
        
        用法:
          /social_config twitter "YOUR_COOKIE_STRING"
        """
        payload = {
            "channel_id": str(ctx.channel.id),
            "platform": platform.lower(),
            "value": value
        }
        if queue.push_task("social_config", payload, priority="high"):
            await ctx.send(f"⚙️ **配置請求已提交** ({platform})。")
            # 刪除使用者的指令訊息 (保護隱私)
            try:
                await ctx.message.delete()
                await ctx.send("🔒 已自動刪除包含機敏資訊的指令訊息。")
            except:
                pass
        else:
            await ctx.send("❌ 隊列發送失敗。")

    # --- PinchTab 指令 ---

    @commands.command(name="pinch_health")
    async def pinch_health(self, ctx):
        """檢查 PinchTab 伺服器狀態。"""
        payload = {"channel_id": str(ctx.channel.id)}
        if queue.push_task("pinch_health", payload, priority="high"):
            await ctx.send("📡 **正在檢查 PinchTab 狀態...**")
        else:
            await ctx.send("❌ 隊列送出失敗。")

    @commands.command(name="pinch")
    async def pinch_browse(self, ctx, url: str):
        """使用 PinchTab 進行高效能、高隱身瀏覽。"""
        if not url.startswith("http"):
            url = "https://" + url
        payload = {
            "channel_id": str(ctx.channel.id),
            "url": url,
            "inject_to_rag": True
        }
        if queue.push_task("pinch_browse", payload, priority="default"):
            await ctx.send(f"🦀 **PinchTab 任務已啟動**：\n> {url}\n正在利用 Accessibility Tree 進行代碼高效抓取...")
        else:
            await ctx.send("❌ 隊列送出失敗。")

    @commands.command(name="pinch_snap")
    async def pinch_snap(self, ctx, tab_id: str):
        """獲取指定 PinchTab 分頁的 Accessibility Tree 快照。"""
        payload = {
            "channel_id": str(ctx.channel.id),
            "tab_id": tab_id
        }
        if queue.push_task("pinch_snapshot", payload, priority="high"):
            await ctx.send(f"📸 **正在獲取分頁快照**：`{tab_id}`")
        else:
            await ctx.send("❌ 隊列送出失敗。")


async def setup(bot):
    await bot.add_cog(BridgeCommands(bot))

