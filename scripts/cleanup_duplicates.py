import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import AsyncSessionLocal
from models.task import ScheduledTask
from sqlalchemy.future import select

async def cleanup():
    print("🚀 正在清理重複的排程任務...")
    async with AsyncSessionLocal() as session:
        # 取得所有任務
        result = await session.execute(select(ScheduledTask))
        tasks = result.scalars().all()
        
        seen = set()
        duplicates_ids = []
        
        for task in tasks:
            # 以名稱、時間、類型作為唯一識別
            identifier = (task.name, task.time, task.type)
            if identifier in seen:
                duplicates_ids.append(task.id)
            else:
                seen.add(identifier)
        
        if not duplicates_ids:
            print("✨ 未發現重複任務。")
            return
            
        print(f"🔍 發現 {len(duplicates_ids)} 個重複任務，正在刪除...")
        for task_id in duplicates_ids:
            task_to_delete = await session.get(ScheduledTask, task_id)
            if task_to_delete:
                await session.delete(task_to_delete)
        
        await session.commit()
        print(f"✅ 清理完成！已刪除 ID: {duplicates_ids}")

if __name__ == "__main__":
    asyncio.run(cleanup())
