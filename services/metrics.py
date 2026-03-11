"""
Metrics Service - 處理效能指標的寫入與查詢。
"""
import datetime
from sqlalchemy import select, func
from core.database import AsyncSessionLocal
from models.metrics import MetricEntry
from core.config import log

async def log_metrics(task_type: str, token_usage: int, latency_ms: int, status: str):
    """將效能指標寫入資料庫。"""
    try:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                entry = MetricEntry(
                    task_type=task_type,
                    token_usage=token_usage,
                    latency_ms=latency_ms,
                    status=status
                )
                session.add(entry)
            log(f"📊 Metrics Logged: {task_type} | Tokens: {token_usage} | Latency: {latency_ms}ms | {status}")
    except Exception as e:
        log(f"❌ 無法記錄 Metrics: {e}")

async def get_summary_stats(days: int = 7):
    """取得最近幾天的彙總數據。"""
    since = datetime.datetime.utcnow() - datetime.timedelta(days=days)
    try:
        async with AsyncSessionLocal() as session:
            # 總 Token 消耗
            stmt_token = select(func.sum(MetricEntry.token_usage)).where(MetricEntry.timestamp >= since)
            total_tokens = await session.execute(stmt_token)
            
            # 平均延遲
            stmt_latency = select(func.avg(MetricEntry.latency_ms)).where(MetricEntry.timestamp >= since)
            avg_latency = await session.execute(stmt_latency)
            
            # 成功/失敗計數
            stmt_status = select(MetricEntry.status, func.count(MetricEntry.id)).where(MetricEntry.timestamp >= since).group_by(MetricEntry.status)
            status_counts = await session.execute(stmt_status)
            
            return {
                "total_tokens": total_tokens.scalar() or 0,
                "avg_latency": float(avg_latency.scalar() or 0),
                "status_distribution": dict(status_counts.all())
            }
    except Exception as e:
        log(f"❌ 讀取 Metrics 失敗: {e}")
        return None
