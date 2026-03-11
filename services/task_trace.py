import uuid
import json
from datetime import datetime
from sqlalchemy import Column, String, Integer, JSON, DateTime, MetaData, Table, select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from core.config import DATABASE_URL, log

# Database Setup
engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class TaskTraceService:
    @staticmethod
    async def create_trace(task_id: str, task_type: str, payload: dict, parent_id: str = None):
        """建立初始任務追蹤紀錄"""
        async with async_session() as session:
            try:
                from sqlalchemy import text
                query = text("""
                    INSERT INTO task_trace (task_id, parent_id, task_type, payload, status)
                    VALUES (CAST(:task_id AS UUID), CAST(:parent_id AS UUID), :task_type, CAST(:payload AS JSONB), 'PENDING')
                """)
                await session.execute(query, {
                    "task_id": task_id,
                    "parent_id": parent_id,
                    "task_type": task_type,
                    "payload": json.dumps(payload)
                })
                await session.commit()
                log(f"💾 [Layer 2] 任務追蹤已建立: {task_id} ({task_type})")
            except Exception as e:
                print(f"❌ [Layer 2] 建立任務追蹤失敗: {e}")
                import traceback
                traceback.print_exc()

    @staticmethod
    async def update_trace(task_id: str, status: str = None, step_index: int = None, trace_data: dict = None, error_msg: str = None):
        """更新任務狀態與推理足跡"""
        async with async_session() as session:
            try:
                from sqlalchemy import text
                updates = []
                params = {"task_id": task_id}
                
                if status:
                    updates.append("status = :status")
                    params["status"] = status
                if step_index is not None:
                    updates.append("step_index = :step_index")
                    params["step_index"] = step_index
                if trace_data:
                    # 使用 JSONB_APPEND 或在 Python 中合併
                    updates.append("trace_log = trace_log || :trace_data")
                    params["trace_data"] = json.dumps([trace_data])
                if error_msg:
                    updates.append("error_msg = :error_msg")
                    params["error_msg"] = error_msg
                
                if not updates:
                    return

                query = text(f"UPDATE task_trace SET {', '.join(updates)} WHERE task_id = :task_id")
                await session.execute(query, params)
                await session.commit()
            except Exception as e:
                log(f"❌ [Layer 2] 更新任務追蹤失敗: {task_id}, {e}")

    @staticmethod
    async def get_pending_tasks():
        """獲取待處理或進行中但中斷的任務"""
        async with async_session() as session:
            try:
                from sqlalchemy import text
                query = text("SELECT task_id, task_type, payload, step_index FROM task_trace WHERE status IN ('PENDING', 'IN_PROGRESS') ORDER BY created_at ASC")
                result = await session.execute(query)
                return result.fetchall()
            except Exception as e:
                log(f"❌ [Layer 2] 獲取待處理任務失敗: {e}")
                return []
