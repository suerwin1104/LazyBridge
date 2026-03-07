"""
每日排程任務模組 (Cog)。
每天 10:30 自動執行晨報並發送至指定 Discord 頻道。
"""
import asyncio
import datetime

from discord.ext import commands, tasks

from core.config import BRIEFING_CHANNEL_ID, BRIEFING_TIME, log
from services.briefing import get_briefing


class SchedulerCog(commands.Cog):
    """每日晨報排程。"""

    def __init__(self, bot):
        self.bot = bot
        self.already_run_today = False

    def cog_unload(self):
        self.daily_briefing_task.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.daily_briefing_task.is_running():
            self.daily_briefing_task.start()
            log(f"⏰ 每日晨報排程 ({BRIEFING_TIME}) 已啟動在背景待命！")

    @tasks.loop(minutes=1)
    async def daily_briefing_task(self):
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M")

        if current_time == BRIEFING_TIME:
            if not self.already_run_today:
                log(f"[{now}] ⏰ 正在執行 {BRIEFING_TIME} 晨報任務...")
                try:
                    report = await asyncio.to_thread(get_briefing)
                    channel = self.bot.get_channel(BRIEFING_CHANNEL_ID)
                    if channel:
                        await channel.send(report)
                        log(f"✅ {BRIEFING_TIME} 晨報發送成功！")
                    else:
                        log(
                            f"❌ 找不到 Discord 頻道 ID {BRIEFING_CHANNEL_ID} 來發送晨報。"
                        )
                    self.already_run_today = True
                except Exception as e:
                    log(f"❌ 執行晨報任務失敗: {e}")
        else:
            self.already_run_today = False

    @daily_briefing_task.before_loop
    async def before_daily_briefing(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(SchedulerCog(bot))
