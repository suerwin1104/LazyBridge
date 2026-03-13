import psutil
import os
import time
import asyncio
from core.config import log, IDENTITY
from services.metrics import get_summary_stats
from services.maintenance import check_browser_health

class SystemMonitor:
    def __init__(self):
        self.start_time = time.time()

    async def get_stats(self):
        """蒐集系統實時指標。"""
        # 1. CPU & RAM
        cpu_usage = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        ram_usage = memory.percent
        
        # 2. Browser Health (Aegis)
        browser_active = await check_browser_health()
        
        # 3. Uptime
        uptime = int(time.time() - self.start_time)
        
        # 4. Redis Queue (Simplified check)
        # In a real setup, we would query redis length
        queue_len = 0 
        try:
            from core.queue import queue
            # if redis is connected, we could get len
            pass
        except:
            pass
            
        # 5. Usage Metrics
        usage = await get_summary_stats(days=7)
            
        return {
            "identity": IDENTITY or "Unknown-Agent",
            "status": "Online",
            "cpu": cpu_usage,
            "ram": ram_usage,
            "browser_active": browser_active,
            "uptime": uptime,
            "usage": usage,
            "timestamp": time.time()
        }

monitor = SystemMonitor()
