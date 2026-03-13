import redis
import json
import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from core.config import REDIS_URL, TASK_QUEUE

def diag():
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
        print(f"Connected to Redis: {REDIS_URL}")
        
        queues = [f"{TASK_QUEUE}:high", TASK_QUEUE, f"{TASK_QUEUE}:low"]
        for q in queues:
            count = r.llen(q)
            print(f"Queue {q}: {count} tasks")
            if count > 0:
                # Peek at the first task
                first_task = r.lindex(q, -1)
                print(f"  - First task: {first_task[:100]}...")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    diag()
