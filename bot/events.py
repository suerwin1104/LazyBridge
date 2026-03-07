"""
Discord Bot 事件處理模組 (Cog)。
處理 on_ready、on_message、on_command_error 等事件。
"""
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
        log("指令: /ask <訊息> | /dump | /tabs | /screen | /click | /type | /mouse")
        log("等待 Discord 指令中...")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        preview = message.content[:20].replace("\n", " ")
        log(f"📨 收到訊息自 {message.author}: {preview}...")

        # 非 / 開頭的訊息自動轉傳給 Antigravity
        if not message.content.startswith("/"):
            log(f"📡 自動轉傳為 /ask: {preview}...")
            await message.channel.send(
                f"📡 接收並傳送中："
                f"**{message.content[:50]}{'...' if len(message.content) > 50 else ''}**"
            )
            await send_to_antigravity(
                message.content,
                str(message.channel.id),
                str(message.author),
                ctx=message.channel,
            )
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
