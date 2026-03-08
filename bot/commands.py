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

    @commands.command()
    async def ask(self, ctx, *, message):
        """向 Antigravity AI 發問 (非同步隊列)。"""
        payload = {
            "channel_id": str(ctx.channel.id),
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


async def setup(bot):
    await bot.add_cog(BridgeCommands(bot))
