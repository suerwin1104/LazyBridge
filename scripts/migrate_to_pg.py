"""
Phase 3 資料遷移腳本。
將舊有的 scheduler_tasks.json (排程任務) 與 scheduler_history.sqlite (執行紀錄)
遷移至 PostgreSQL (或新的 SQLAlchemy 資料庫)。

使用方式:
  python scripts/migrate_to_pg.py
"""
import os
import sys
import json
import sqlite3
import asyncio
from datetime import datetime

# 將專案根目錄加入路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import init_db, AsyncSessionLocal
from models.task import ScheduledTask
from models.history import TaskHistory
from core.config import log

TASKS_JSON_PATH = "scheduler_tasks.json"
HISTORY_DB_PATH = "scheduler_history.sqlite"

async def migrate_tasks(session):
    if not os.path.exists(TASKS_JSON_PATH):
        log(f"⚠️ 找不到舊的任務設定檔 {TASKS_JSON_PATH}，略過任務遷移。")
        return 0

    try:
        with open(TASKS_JSON_PATH, "r", encoding="utf-8") as f:
            tasks_data = json.load(f)
            
        count = 0
        from sqlalchemy import and_
        for task in tasks_data:
            # 檢查是否已存在同名同時間同類型的任務
            stmt = select(ScheduledTask).where(
                and_(
                    ScheduledTask.name == task.get("name"),
                    ScheduledTask.time == task.get("time"),
                    ScheduledTask.type == task.get("type")
                )
            )
            result = await session.execute(stmt)
            if result.scalars().first():
                log(f"⏭️ 任務 {task.get('name')} 已存在，跳過。")
                continue

            new_task = ScheduledTask(
                name=task.get("name"),
                time=task.get("time"),
                type=task.get("type"),
                params=task.get("params", {}),
                command=task.get("command"),
                enabled=task.get("enabled", True)
            )
            session.add(new_task)
            count += 1
            
        await session.commit()
        log(f"✅ 成功遷移 {count} 筆排程任務至新資料庫。")
        return count
    except Exception as e:
        log(f"❌ 遷移任務失敗: {e}")
        await session.rollback()
        return 0

async def migrate_history(session):
    if not os.path.exists(HISTORY_DB_PATH):
        log(f"⚠️ 找不到舊的歷史紀錄檔 {HISTORY_DB_PATH}，略過歷史紀錄遷移。")
        return 0
        
    try:
        conn = sqlite3.connect(HISTORY_DB_PATH)
        cursor = conn.cursor()
        
        # 檢查表格是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='history'")
        if not cursor.fetchone():
            log("⚠️ 歷史紀錄表格不存在，略過遷移。")
            conn.close()
            return 0
            
        cursor.execute("SELECT task_name, execution_time, status, message FROM history")
        rows = cursor.fetchall()
        
        count = 0
        for row in rows:
            exec_time = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S") if isinstance(row[1], str) else row[1]
            new_history = TaskHistory(
                task_name=row[0],
                execution_time=exec_time,
                status=row[2],
                message=row[3]
            )
            session.add(new_history)
            count += 1
            
        await session.commit()
        conn.close()
        log(f"✅ 成功遷移 {count} 筆歷史紀錄至新資料庫。")
        return count
    except Exception as e:
        log(f"❌ 遷移歷史紀錄失敗: {e}")
        await session.rollback()
        return 0

async def perform_migration():
    log("🚀 開始執行 Phase 3 資料遷移程序...")
    
    # 確保新資料庫的表格存在
    await init_db()
    
    async with AsyncSessionLocal() as session:
        tasks_transferred = await migrate_tasks(session)
        history_transferred = await migrate_history(session)
        
    log(f"🎉 遷移完成！共轉移 {tasks_transferred} 個任務與 {history_transferred} 筆紀錄。")
    log("💡 您現在可以刪除舊的 scheduler_tasks.json 與 scheduler_history.sqlite 檔案。")

if __name__ == "__main__":
    asyncio.run(perform_migration())
