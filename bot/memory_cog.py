"""
Discord Bot Memory Engine 模組 (Cog)。
負責所有與記憶庫相關的指令轉發。
"""
from discord.ext import commands
from core.queue import queue
from core.config import log

class MemoryCommands(commands.Cog):
    """Memory Engine 指令。"""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="memory", description="Memory Engine 相關指令")
    async def memory(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("請使用子指令：save, reload, diary。")

    @memory.command(name="save", description="儲存目前的重點或對話題要到記憶庫")
    async def memory_save(self, ctx, *, topic: str = "自動重點"):
        prompt = f"請幫我把剛才或目前的重點儲存起來（對應 memory-engine 的 /save）。主題是：{topic}"
        payload = {"channel_id": str(ctx.channel.id), "author": str(ctx.author), "message": prompt}
        if queue.push_task("ask", payload):
            await ctx.send(f"📥 **請求已送出**：要求 AI 儲存重點記憶 ({topic})")
        else:
            await ctx.send("❌ 隊列發送失敗。")

    @memory.command(name="reload", description="重新讀取目前專案的記憶上下文")
    async def memory_reload(self, ctx):
        prompt = "請為我重新讀取並整理目前專案的記憶上下文（呼叫 /reload），告訴我目前的進度和方向。"
        payload = {"channel_id": str(ctx.channel.id), "author": str(ctx.author), "message": prompt}
        if queue.push_task("ask", payload):
            await ctx.send("📥 **請求已送出**：要求 AI 重新載入專案記憶")
        else:
            await ctx.send("❌ 隊列發送失敗。")

    @memory.command(name="diary", description="產出今日工作或溝通的回顧日誌")
    async def memory_diary(self, ctx):
        prompt = "請幫我執行 /diary，回顧並總結我們今天的開發/討論內容。"
        payload = {"channel_id": str(ctx.channel.id), "author": str(ctx.author), "message": prompt}
        if queue.push_task("ask", payload):
            await ctx.send("📥 **請求已送出**：要求 AI 產出今日回顧日誌")
        else:
            await ctx.send("❌ 隊列發送失敗。")

    @memory.command(name="list", description="檢視目前資料庫中儲存的記憶條目")
    async def memory_list(self, ctx, category: str = None):
        """列出資料庫中紀錄的 Memory (可選: session, pitfall, custom)"""
        from services.memory_engine import get_memory_list
        try:
            entries = await get_memory_list(category)
            if not entries:
                await ctx.send("📭 目前記憶資料庫中沒有找到任何紀錄。")
                return
                
            msg = "🧠 **Memory Engine 記憶清單 (最新 20 筆):**\n"
            for e in entries:
                cat = e.get("category", "unknown")
                date_str = e.get("created_at", "")[:10]
                msg += f"🔹 `[{cat}]` **{e.get('title')}** ({date_str})\n"
                
            await ctx.send(msg)
        except Exception as e:
            log(f"❌ memory_list 指令失敗: {e}")
            await ctx.send(f"❌ 查詢記憶時發生錯誤: {e}")

async def setup(bot):
    await bot.add_cog(MemoryCommands(bot))
