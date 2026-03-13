import sys
import os
sys.path.append(os.getcwd())

from core.queue import queue
from core.config import TASK_QUEUE

def clear_queues():
    if not queue.redis:
        return
    for suffix in ["high", "low"]:
        queue.redis.delete(f"{TASK_QUEUE}:{suffix}")
    queue.redis.delete(TASK_QUEUE)
    queue.redis.delete(f"{TASK_QUEUE}:_rr_counter")
    print("🧹 Queues and counter cleared.\n")

def test_weighted_round_robin():
    """Test that all priority levels make progress even when all queues have tasks."""
    clear_queues()

    # Push 10 tasks to each queue
    for i in range(10):
        queue.push_task(f"h_{i}", {"id": i}, priority="high")
        queue.push_task(f"d_{i}", {"id": i}, priority="default")
        queue.push_task(f"l_{i}", {"id": i}, priority="low")

    print(f"\n📊 Initial queue stats: {queue.get_queue_stats()}")
    print(f"   (high=10, default=10, low=10)\n")

    # Pop 10 tasks and count how many come from each priority
    counts = {"high": 0, "default": 0, "low": 0}
    for i in range(10):
        task = queue.pop_task()
        if task:
            p = task["priority"]
            counts[p] += 1

    print(f"📥 After 10 pops:")
    print(f"   high: {counts['high']} (expected ~6)")
    print(f"   default: {counts['default']} (expected ~3)")
    print(f"   low: {counts['low']} (expected ~1)")
    print(f"\n📊 Remaining: {queue.get_queue_stats()}")

    # Verify no priority was starved
    all_progressed = all(c > 0 for c in counts.values())
    if all_progressed:
        print("\n✅ SUCCESS: All priority levels made progress! No starvation.")
    else:
        starved = [k for k, v in counts.items() if v == 0]
        print(f"\n❌ FAILED: These priorities were starved: {starved}")

    return all_progressed

def test_fallback_when_empty():
    """Test that when a scheduled queue is empty, tasks from other queues are still processed."""
    clear_queues()

    # Only push to low priority
    for i in range(5):
        queue.push_task(f"low_{i}", {"id": i}, priority="low")

    print(f"📊 Only low queue has tasks: {queue.get_queue_stats()}")

    # Pop should still work — fallback kicks in
    popped = 0
    for i in range(5):
        task = queue.pop_task()
        if task:
            popped += 1

    if popped == 5:
        print(f"✅ SUCCESS: All 5 low-priority tasks popped via fallback!")
    else:
        print(f"❌ FAILED: Only popped {popped}/5 tasks.")

    print(f"📊 Final: {queue.get_queue_stats()}\n")

if __name__ == "__main__":
    print("=" * 50)
    print("TEST 1: Weighted Round-Robin Distribution")
    print("=" * 50)
    test_weighted_round_robin()

    print("\n" + "=" * 50)
    print("TEST 2: Fallback When Scheduled Queue is Empty")
    print("=" * 50)
    test_fallback_when_empty()
