import json
import asyncio
import os
import sys
sys.path.append(os.getcwd())

from core.database import AsyncSessionLocal
from models.task import ScheduledTask

async def import_tasks():
    if not os.path.exists("scheduler_tasks.json"):
        print("❌ scheduler_tasks.json not found")
        return

    with open("scheduler_tasks.json", "r", encoding="utf-8") as f:
        tasks_data = json.load(f)

    async with AsyncSessionLocal() as session:
        for data in tasks_data:
            new_task = ScheduledTask(
                name=data["name"],
                time=data["time"],
                type=data["type"],
                enabled=data["enabled"],
                params=data.get("params", {}),
                command=data.get("command")
            )
            session.add(new_task)
        
        await session.commit()
    print(f"✅ Imported {len(tasks_data)} tasks to PostgreSQL")

if __name__ == "__main__":
    asyncio.run(import_tasks())
