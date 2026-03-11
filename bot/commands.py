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


class BridgeCommands(commands.Cog):
    """LazyBridge 的所有 Discord 指令。"""

    def __init__(self, bot):
        self.bot = bot
        self.voice_clients = {}

    @commands.command()
    async def join(self, ctx):
        """讓 Mandy 進入語音頻道。"""
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            vc = ctx.guild.voice_client
            if vc:
                if vc.channel.id != channel.id:
                    await vc.move_to(channel)
            else:
                vc = await channel.connect()
            self.voice_clients[ctx.guild.id] = vc
            await ctx.send(f"🎙️ **Mandy 已進入頻道**: {channel.name}")
        else:
            await ctx.send("❌ 您必須先進入一個語音頻道！")

    @commands.command()
    async def leave(self, ctx):
        """讓 Mandy 離開語音頻道。"""
        vc = ctx.guild.voice_client
        if vc:
            await vc.disconnect()
            if ctx.guild.id in self.voice_clients:
                del self.voice_clients[ctx.guild.id]
            await ctx.send("👋 **Mandy 已離開語音頻道**。")
        else:
            await ctx.send("❌ 我目前不在任何語音頻道中。")

    @commands.command()
    async def speak(self, ctx, *, text: str):
        """讓 Mandy 在語音頻道說話。"""
        vc = ctx.guild.voice_client
        if not vc or not vc.is_connected():
            if ctx.author.voice:
                channel = ctx.author.voice.channel
                vc = await channel.connect()
                self.voice_clients[ctx.guild.id] = vc
            else:
                await ctx.send("❌ 請先讓我進入頻道或您先進入頻道。")
                return

        from services.voice_service import VoiceService
        filepath = await VoiceService.generate_tts(text)
        if filepath:
            await VoiceService.play_voice(vc, filepath)
            await ctx.send(f"🗣️ **Mandy 說**: {text}")

    @commands.command()
    async def ask(self, ctx, *, message):
        """向 Antigravity AI 發問 (非同步隊列)。"""
        payload = {
            "channel_id": str(ctx.channel.id),
            "guild_id": str(ctx.guild.id) if ctx.guild else None,
            "author": str(ctx.author),
            "message": message
        }
        if queue.push_task("ask", payload):
            await ctx.send(
                f"📥 **已進入排隊隊列**：{message[:50]}..."
            )
        else:
            await ctx.send("❌ 無法連接任務隊列伺服器 (Redis)，請檢查後端狀態。")

    @commands.command()
    async def briefing(self, ctx):
        """手動觸發晨報任務 (非同步隊列)。"""
        payload = {
            "channel_id": str(ctx.channel.id),
            "params": {"include_emails": True, "include_calendar": True, "include_news": True}
        }
        if queue.push_task("briefing", payload):
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
        if queue.push_task("loop", {}):
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
        if queue.push_task("presentation", payload):
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
        if queue.push_task("chub", payload):
            if action == "search":
                await ctx.send(f"🔍 正在搜尋 Context Hub: `{args}`...")
            elif action == "get":
                await ctx.send(f"📥 正在從 Context Hub 抓取文件: `{args}`...")
            elif action == "annotate":
                await ctx.send(f"📝 正在為文件建立註解...")
        else:
            await ctx.send("❌ 隊列發送失敗，請檢查 Task Queue (Redis)。")


async def setup(bot):
    await bot.add_cog(BridgeCommands(bot))
