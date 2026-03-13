import json
import redis
from core.config import REDIS_URL, TASK_QUEUE, log

# Weighted Round-Robin Configuration
# Format: (queue_suffix, weight)
# Total weight = 10 → high gets 6/10, default gets 3/10, low gets 1/10
QUEUE_WEIGHTS = [
    ("high", 6),
    ("default", 3),
    ("low", 1),
]

# Build the round-robin schedule from weights
# e.g. [high, high, high, high, high, high, default, default, default, low]
_SCHEDULE = []
for suffix, weight in QUEUE_WEIGHTS:
    _SCHEDULE.extend([suffix] * weight)

SCHEDULE_LEN = len(_SCHEDULE)  # 10


class TaskQueue:
    def __init__(self):
        try:
            self.redis = redis.from_url(REDIS_URL, decode_responses=True)
            log(f"Connected to Redis at {REDIS_URL}")
        except Exception as e:
            log(f"Failed to connect to Redis: {e}")
            self.redis = None

    def _queue_name(self, priority):
        """Return the Redis key for a given priority level."""
        return f"{TASK_QUEUE}:{priority}" if priority != "default" else TASK_QUEUE

    def push_task(self, task_type, payload, priority="default"):
        if not self.redis:
            log("Redis not available, cannot push task.")
            return False

        queue_name = self._queue_name(priority)

        task_data = {
            "type": task_type,
            "payload": payload,
            "priority": priority
        }
        try:
            self.redis.lpush(queue_name, json.dumps(task_data))
            log(f"Task pushed to {queue_name}: {task_type}")
            return True
        except Exception as e:
            log(f"Error pushing task: {e}")
            return False

    def pop_task(self, timeout=0):
        """Weighted Round-Robin pop: ensures all priority levels make progress.

        Schedule (per 10 pops): high×6, default×3, low×1.
        If the scheduled queue is empty, falls back to any non-empty queue
        (still in priority order) so no cycle is wasted.
        """
        if not self.redis:
            return None

        try:
            # Get and increment the round-robin counter atomically
            counter_key = f"{TASK_QUEUE}:_rr_counter"
            idx = self.redis.incr(counter_key) - 1
            slot = idx % SCHEDULE_LEN
            scheduled_priority = _SCHEDULE[slot]

            # 1. Try the scheduled queue first (weighted fairness)
            primary_q = self._queue_name(scheduled_priority)
            result = self.redis.rpop(primary_q)
            if result:
                return json.loads(result)

            # 2. Scheduled queue is empty → fallback to any non-empty queue
            #    (priority order: high → default → low)
            all_queues = [self._queue_name(s) for s, _ in QUEUE_WEIGHTS]
            for q in all_queues:
                if q == primary_q:
                    continue  # Already tried
                result = self.redis.rpop(q)
                if result:
                    return json.loads(result)

        except Exception as e:
            log(f"Error popping task: {e}")
        return None

    def get_queue_stats(self):
        """Return current queue lengths for diagnostics."""
        if not self.redis:
            return {}
        stats = {}
        for suffix, _ in QUEUE_WEIGHTS:
            q = self._queue_name(suffix)
            stats[suffix] = self.redis.llen(q)
        return stats


# Singleton instance
queue = TaskQueue()
