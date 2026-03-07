"""
LazyBridge — Antigravity AI 橋接器
入口點：載入設定 → 建立 Bot → 註冊模組 → 啟動。
"""
import asyncio

import discord
from discord.ext import commands

from core.config import get_bot_token, log


async def main():
    bot = commands.Bot(command_prefix="/", intents=discord.Intents.all())

    # 載入所有 Cog 模組
    await bot.load_extension("bot.commands")
    await bot.load_extension("bot.events")
    await bot.load_extension("bot.scheduler")

    log("🚀 正在啟動 LazyBridge...")
    await bot.start(get_bot_token())


if __name__ == "__main__":
    asyncio.run(main())
