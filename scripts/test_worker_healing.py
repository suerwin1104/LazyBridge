import asyncio
import sys
import os
import uuid
sys.path.append(os.getcwd())

from core.config import load_env, log
load_env()
from worker import handle_task
from services.task_trace import TaskTraceService
from core.config import log

async def test_worker_healing():
    print("🤖 Testing Worker Self-Healing Pipeline...")
    
    # 1. 模擬錯誤格式的 JSON 以觸發 Cognitive Self-Correction
    test_task = {
        "type": "presentation",
        "payload": {
            "topic": "Test Healing Topic",
            # deliberately skipping channel_id to avoid spamming actual discord
        }
    }
    
    print("\n--- Triggering handle_task (Presentation with malformed JSON expected from AI) ---")
    print("Note: If the AI returns perfect JSON on the first try, self-correction won't trigger.")
    print("Calling handle_task...")
    await handle_task(test_task)
    
    # 2. 檢查 PostgreSQL 裡的 Task Trace
    print("\n--- Checking Task Trace Persistence ---")
    try:
        pending_tasks = await TaskTraceService.get_pending_tasks()
        print(f"Pending/In-Progress Tasks count: {len(pending_tasks)}")
        # 由於 handle_task 執行完會變為 COMPLETED 或 FAILED，這裡印出是為了確認連線成功
    except Exception as e:
        print(f"Failed to query DB: {e}")

if __name__ == "__main__":
    asyncio.run(test_worker_healing())
