import asyncio
import os
import sys

sys.path.append(os.getcwd())

from services.task_trace import TaskTraceService
from core.config import load_env

async def main():
    load_env()
    print("Starting trace test...")
    await TaskTraceService.create_trace("123e4567-e89b-12d3-a456-426614174000", "test", {"foo": "bar"})
    print("Trace executed!")

if __name__ == "__main__":
    asyncio.run(main())
