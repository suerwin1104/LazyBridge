import redis
import json
import uuid

r = redis.from_url("redis://localhost:6379")
task = {
    "id": str(uuid.uuid4()),
    "type": "presentation",
    "payload": {
        "topic": "DEBUG TEST",
        "channel_id": "1209429528632361000",
        "author": "System"
    }
}
r.lpush("lazybridge_tasks", json.dumps(task))
print("Pushed debug task.")
