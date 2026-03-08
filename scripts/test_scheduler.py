import sys
import os
import json
import sqlite3
import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.config import SCHEDULER_DB_PATH, SCHEDULER_TASKS_PATH, log

def verify_setup():
    print("--- 驗證排程設定 ---")
    if os.path.exists(SCHEDULER_TASKS_PATH):
        with open(SCHEDULER_TASKS_PATH, "r", encoding="utf-8") as f:
            tasks = json.load(f)
            print(f"成功讀取 {len(tasks)} 個任務:")
            for t in tasks:
                print(f"  - {t.get('name')} ({t.get('time')}) [Enabled: {t.get('enabled')}]")
    else:
        print("❌ 找不到 scheduler_tasks.json")

def verify_db():
    print("\n--- 驗證 SQLite 數據庫 ---")
    if os.path.exists(SCHEDULER_DB_PATH):
        try:
            conn = sqlite3.connect(SCHEDULER_DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='task_history'")
            if cursor.fetchone():
                print("✅ task_history 表格已存在。")
                
                # 插入測試資料
                cursor.execute(
                    "INSERT INTO task_history (task_name, status, message) VALUES (?, ?, ?)",
                    ("Test Task", "SUCCESS", "Verification Script Run")
                )
                conn.commit()
                print("✅ 成功插入測試紀錄。")
                
                # 讀取資料
                cursor.execute("SELECT * FROM task_history ORDER BY id DESC LIMIT 1")
                row = cursor.fetchone()
                print(f"最新紀錄: {row}")
            else:
                print("❌ task_history 表格不存在。")
            conn.close()
        except Exception as e:
            print(f"❌ 數據庫操作失敗: {e}")
    else:
        print("❌ 找不到 scheduler_history.sqlite (可能尚未初始化)")

if __name__ == "__main__":
    verify_setup()
    verify_db()
