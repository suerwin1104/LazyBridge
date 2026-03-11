import asyncio
import os
import sys
sys.path.append(os.getcwd())

from core.database import AsyncSessionLocal
from sqlalchemy import text
import traceback

async def check():
    try:
        async with AsyncSessionLocal() as session:
            res = await session.execute(text("SELECT task_id, task_type, status, error_message FROM task_trace ORDER BY created_at DESC LIMIT 5"))
            rows = res.fetchall()
            for r in rows:
                print(f"Task: {r[0]}, Type: {r[1]}, Status: {r[2]}")
                if r[3]:
                    print(f"  Error: {r[3][:200]}")
    except Exception as e:
        with open("trace2.log", "w", encoding="utf-8") as f:
            f.write(str(e) + "\n\n")
            traceback.print_exc(file=f)

if __name__ == "__main__":
    asyncio.run(check())
