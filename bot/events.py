"""
Discord Bot 事件處理模組 (Cog)。
處理 on_ready、on_message、on_command_error 等事件。
"""
import discord
from discord.ext import commands

from core.cdp import send_to_antigravity
from core.config import log


class BotEvents(commands.Cog):
    """Bot 生命週期事件與自動轉傳邏輯。"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        log("✅ 橋樑啟動成功！（雙向模式）")
        log(f"機器人帳號: {self.bot.user}")
        log(f"Message Content Intent: {self.bot.intents.message_content}")
        
        # 註冊 Slash Commands
        try:
            from core.config import DEFAULT_GUILD_ID
            guild = discord.Object(id=int(DEFAULT_GUILD_ID))
            
            # 將 Cog 中的 command 複製一份到 guild tree (為了立即生效)
            self.bot.tree.copy_global_to(guild=guild)
            synced = await self.bot.tree.sync(guild=guild)
            
            log(f"🔄 成功同步 {len(synced)} 個 Slash Commands 到伺服器 {DEFAULT_GUILD_ID}")
            
            # 同時也進行一次全域同步
            await self.bot.tree.sync()
        except Exception as e:
            log(f"❌ 同步 Slash Commands 失敗: {e}")

        log("指令: /ask <訊息> | /dump | /tabs | /screen | /click | /type | /mouse")
        log("等待 Discord 指令中...")

    @commands.Cog.listener()
    async def on_message(self, message):
        import re

        # 如果訊息來自機器人自己，檢查是否帶有 BRAVO_BROWSE 觸發標籤
        if message.author == self.bot.user:
            if "BRAVO_BROWSE:" in message.content:
                browse_match = re.search(r'BRAVO_BROWSE:\s*["\']?(.*?)["\']?(?:\n|$)', message.content, re.MULTILINE)
                if browse_match:
                    browse_task_desc = browse_match.group(1).strip().strip('"').strip("'")
                    log(f"🤖 核心攔截: 偵測到 Autonomous Browse 觸發指令 '{browse_task_desc}'")
                    
                    # 1. 編輯原訊息，移除醜醜的 BRAVO_BROWSE 標籤給使用者看
                    clean_content = re.sub(r'BRAVO_BROWSE:\s*["\']?.*?["\']?(?:\n|$)', '', message.content, flags=re.MULTILINE).strip()
                    try:
                        await message.edit(content=clean_content)
                    except Exception as e:
                        log(f"⚠️ 無法編輯機器人原訊息: {e}")
                    
                    # 2. 推送任務至 Redis Queue
                    from core.queue import queue
                    if queue.push_task("web_browse", {
                        "task": browse_task_desc,
                        "channel_id": str(message.channel.id)
                    }, priority="default"):
                        log(f"✅ Web Browse 任務已經成功排隊！")
                    else:
                        log(f"❌ 任務排隊失敗！")
            return

        preview = message.content[:20].replace("\n", " ")
        log(f"📨 收到訊息自 {message.author}: {preview}...")

        # 非 / 開頭的訊息自動轉傳給 Antigravity
        if not message.content.startswith("/"):
            log(f"📡 自動轉傳為 cdp_ask 任務: {preview}...")
            await message.channel.send(
                f"📡 接收並排隊中："
                f"**{message.content[:50]}{'...' if len(message.content) > 50 else ''}**"
            )
            from core.queue import queue
            if queue.push_task("cdp_ask", {
                "message": message.content,
                "channel_id": str(message.channel.id),
                "author": str(message.author)
            }, priority="high"):
                log("✅ cdp_ask 任務已經成功排隊！")
            else:
                log("❌ 任務排隊失敗！")
            return

        # process_commands 由 Bot 內建 on_message 自動呼叫，此處不需重複呼叫

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        log(f"❌ 指令錯誤 ({ctx.command}): {error}")
        await ctx.send(f"❌ 執行指令時出錯: `{error}`")


async def setup(bot):
    await bot.add_cog(BotEvents(bot))
