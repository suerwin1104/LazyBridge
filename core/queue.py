import json
import redis
from core.config import REDIS_URL, TASK_QUEUE, log

class TaskQueue:
    def __init__(self):
        try:
            self.redis = redis.from_url(REDIS_URL, decode_responses=True)
            log(f"Connected to Redis at {REDIS_URL}")
        except Exception as e:
            log(f"Failed to connect to Redis: {e}")
            self.redis = None

    def push_task(self, task_type, payload):
        if not self.redis:
            log("Redis not available, cannot push task.")
            return False
        
        task_data = {
            "type": task_type,
            "payload": payload
        }
        try:
            self.redis.lpush(TASK_QUEUE, json.dumps(task_data))
            log(f"Task pushed to {TASK_QUEUE}: {task_type}")
            return True
        except Exception as e:
            log(f"Error pushing task: {e}")
            return False

    def pop_task(self, timeout=0):
        if not self.redis:
            return None
        
        try:
            # blpop returns (queue_name, data)
            result = self.redis.blpop(TASK_QUEUE, timeout=timeout)
            if result:
                return json.loads(result[1])
        except Exception as e:
            log(f"Error popping task: {e}")
        return None

# Singleton instance
queue = TaskQueue()
