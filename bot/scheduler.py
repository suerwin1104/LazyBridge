"""
每日排程任務模組 (Phase 3 - DB Upgrade)。
直接從資料庫 (PostgreSQL/SQLite) 非同步讀取排程設定，
並將執行紀錄寫回資料庫。
"""
import asyncio
import datetime
from sqlalchemy.future import select

import discord
from discord import app_commands
from discord.ext import commands, tasks

from core.config import BRIEFING_CHANNEL_ID, log
from core.queue import queue
from core.database import AsyncSessionLocal
from models.task import ScheduledTask
from models.history import TaskHistory


class SchedulerCog(commands.Cog):
    """資料庫驅動的動態排程任務管理器。"""

    def __init__(self, bot):
        self.bot = bot
        self.last_run = {}  # 紀錄每個任務最後執行的日期 (str: YYYY-MM-DD)，避免重複執行

    async def log_task_execution(self, task_name, status, message=""):
        """將任務執行結果寫入資料庫。"""
        try:
            async with AsyncSessionLocal() as session:
                new_history = TaskHistory(
                    task_name=task_name,
                    status=status,
                    message=message
                )
                session.add(new_history)
                await session.commit()
        except Exception as e:
            log(f"❌ 寫入任務紀錄失敗: {e}")

    def cog_unload(self):
        self.dynamic_scheduler_task.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.dynamic_scheduler_task.is_running():
            self.dynamic_scheduler_task.start()
            log("⏰ 資料庫動態排程監聽已啟動！")

    @tasks.loop(minutes=1)
    async def dynamic_scheduler_task(self):
        """每分鐘向資料庫查詢當前應執行的任務。"""
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M")
        today = now.strftime("%Y-%m-%d")

        try:
            async with AsyncSessionLocal() as session:
                # 撈取所有已啟用的排程任務
                result = await session.execute(
                    select(ScheduledTask).where(ScheduledTask.enabled == True)
                )
                tasks_list = result.scalars().all()

                for task in tasks_list:
                    # 檢查時間是否到達，且今天尚未執行
                    if current_time == task.time:
                        last_run_date = self.last_run.get(task.name)
                        if last_run_date != today:
                            log(f"[{now}] ⏰ 正在執行排程任務: {task.name}...")
                            try:
                                await self.execute_task(task)
                                await self.log_task_execution(task.name, "SUCCESS", f"執行時間: {current_time}")
                            except Exception as e:
                                error_msg = f"執行失敗: {e}"
                                log(f"❌ {task.name} {error_msg}")
                                await self.log_task_execution(task.name, "FAILED", error_msg)
                            
                            self.last_run[task.name] = today
        except Exception as e:
            log(f"❌ 查詢排程任務失敗: {e}")

    async def execute_task(self, task):
        """將任務推送到 Redis 隊列，由 Worker 執行。"""
        payload = {
            "task_name": task.name,
            "params": task.params or {},
            "channel_id": str(BRIEFING_CHANNEL_ID) if task.type == "briefing" else None
        }

        if task.type == "command":
             payload["command"] = task.command

        if queue.push_task(task.type, payload):
            log(f"✅ {task.name} ({task.type}) 已成功推送到隊列。")
        else:
            raise Exception("無法推送到 Redis 隊列")

    @dynamic_scheduler_task.before_loop
    async def before_dynamic_scheduler(self):
        await self.bot.wait_until_ready()

    @commands.command(name="reload_tasks")
    @commands.is_owner()
    async def reload_tasks_cmd(self, ctx):
        """Phase 3: 不再需要手動載入 JSON，任務會自動於每分鐘內生效。"""
        await ctx.send("✅ 已升級資料庫引擎，任務將即時套用，無需手動重新載入。")

    # --- Slash Commands for Task Management ---

    @app_commands.command(name="list_tasks", description="列出目前所有的排程任務")
    async def list_tasks(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(ScheduledTask))
                tasks_list = result.scalars().all()

                if not tasks_list:
                    await interaction.followup.send("📭 目前沒有任何排程任務。")
                    return

                embed = discord.Embed(title="⏰ 系統排程任務清單", color=discord.Color.blue())
                for t in tasks_list:
                    status = "🟢 啟用" if t.enabled else "🔴 停用"
                    details = f"類型: `{t.type}`"
                    if t.type == "command":
                        details += f" | 指令: `{t.command}`"
                    embed.add_field(
                        name=f"[{t.id}] {t.name} - {t.time} ({status})",
                        value=details,
                        inline=False
                    )
                await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ 查詢失敗: {e}")

    @app_commands.command(name="add_task", description="新增一個排程任務 (預設為 briefing 類型)")
    @app_commands.describe(
        name="任務名稱",
        time="執行時間 (格式 HH:MM，如 10:30)",
        task_type="任務類型 (briefing 或 command)"
    )
    async def add_task(self, interaction: discord.Interaction, name: str, time: str, task_type: str = "briefing"):
        await interaction.response.defer(ephemeral=False)
        try:
            async with AsyncSessionLocal() as session:
                new_task = ScheduledTask(
                    name=name,
                    time=time,
                    type=task_type,
                    enabled=True
                )
                session.add(new_task)
                await session.commit()
                await interaction.followup.send(f"✅ 成功新增任務 **{name}**！將於每天 `{time}` 執行 `{task_type}`。")
        except Exception as e:
            await interaction.followup.send(f"❌ 新增失敗: {e}")

    @app_commands.command(name="toggle_task", description="切換排程任務的啟用/停用狀態")
    @app_commands.describe(task_id="任務 ID (可透過 /list_tasks 查詢)")
    async def toggle_task(self, interaction: discord.Interaction, task_id: int):
        await interaction.response.defer(ephemeral=False)
        try:
            async with AsyncSessionLocal() as session:
                task = await session.get(ScheduledTask, task_id)
                if not task:
                    await interaction.followup.send(f"❌ 找不到 ID 為 `{task_id}` 的任務。")
                    return
                
                task.enabled = not task.enabled
                await session.commit()
                status_str = "🟢 已啟用" if task.enabled else "🔴 已停用"
                await interaction.followup.send(f"✅ 任務 **{task.name}** 狀態已更改為: {status_str}")
        except Exception as e:
            await interaction.followup.send(f"❌ 切換狀態失敗: {e}")

    @app_commands.command(name="delete_task", description="刪除一個排程任務")
    @app_commands.describe(task_id="任務 ID (可透過 /list_tasks 查詢)")
    async def delete_task(self, interaction: discord.Interaction, task_id: int):
        await interaction.response.defer(ephemeral=False)
        try:
            async with AsyncSessionLocal() as session:
                task = await session.get(ScheduledTask, task_id)
                if not task:
                    await interaction.followup.send(f"❌ 找不到 ID 為 `{task_id}` 的任務。")
                    return
                
                await session.delete(task)
                await session.commit()
                await interaction.followup.send(f"🗑️ 已成功刪除任務 **{task.name}**。")
        except Exception as e:
            await interaction.followup.send(f"❌ 刪除失敗: {e}")

    @app_commands.command(name="edit_task", description="修改現有的排程任務")
    @app_commands.describe(
        task_id="任務 ID (可透過 /list_tasks 查詢)",
        name="新任務名稱 (不填則不修改)",
        time="新時間 (格式 HH:MM，不填則不修改)",
        task_type="新類型 (briefing 或 command，不填則不修改)",
        command="執行指令 (適用於 command 類型)"
    )
    async def edit_task(
        self, 
        interaction: discord.Interaction, 
        task_id: int, 
        name: str = None, 
        time: str = None, 
        task_type: str = None,
        command: str = None
    ):
        await interaction.response.defer(ephemeral=False)
        try:
            async with AsyncSessionLocal() as session:
                task = await session.get(ScheduledTask, task_id)
                if not task:
                    await interaction.followup.send(f"❌ 找不到 ID 為 `{task_id}` 的任務。")
                    return
                
                updates = []
                if name:
                    task.name = name
                    updates.append(f"名稱 -> **{name}**")
                if time:
                    task.time = time
                    updates.append(f"時間 -> `{time}`")
                if task_type:
                    task.type = task_type
                    updates.append(f"類型 -> `{task_type}`")
                if command:
                    task.command = command
                    updates.append(f"指令 -> `{command}`")
                
                if not updates:
                    await interaction.followup.send("⚠️ 未提供任何修改項。")
                    return
                
                await session.commit()
                await interaction.followup.send(f"✅ 任務 **ID {task_id}** 已更新：\n" + "\n".join([f"- {u}" for u in updates]))
        except Exception as e:
            await interaction.followup.send(f"❌ 修改失敗: {e}")


async def setup(bot):
    await bot.add_cog(SchedulerCog(bot))
