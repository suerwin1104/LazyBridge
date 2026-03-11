import redis
import json
try:
    r = redis.from_url('redis://localhost:6379', decode_responses=True)
    length = r.llen('lazybridge_tasks')
    print(f"Queue length: {length}")
    if length > 0:
        tasks = r.lrange('lazybridge_tasks', 0, 0)
        print(f"First task: {tasks[0]}")
except Exception as e:
    print(f"Redis error: {e}")
