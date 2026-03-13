"""
Metrics Service - 處理效能指標的寫入與查詢。
"""
import datetime
from sqlalchemy import select, func
from core.database import AsyncSessionLocal
from models.metrics import MetricEntry
from core.config import log

async def log_metrics(task_type: str, token_usage: int, latency_ms: int, status: str, model_name: str = None):
    """將效能指標寫入資料庫。"""
    try:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                entry = MetricEntry(
                    task_type=task_type,
                    model_name=model_name,
                    token_usage=token_usage,
                    latency_ms=latency_ms,
                    status=status
                )
                session.add(entry)
            log(f"📊 Metrics Logged: {task_type} ({model_name or 'unknown'}) | Tokens: {token_usage} | Latency: {latency_ms}ms | {status}")
    except Exception as e:
        log(f"❌ 無法記錄 Metrics: {e}")

async def get_summary_stats(days: int = 7):
    """取得最近幾天的彙總數據。"""
    import datetime
    since = datetime.datetime.now() - datetime.timedelta(days=days)
    try:
        async with AsyncSessionLocal() as session:
            # 總 Token 消耗
            stmt_token = select(func.sum(MetricEntry.token_usage)).where(MetricEntry.timestamp >= since)
            token_result = await session.execute(stmt_token)
            total_tokens = token_result.scalar() or 0
            
            # 平均延遲
            stmt_latency = select(func.avg(MetricEntry.latency_ms)).where(MetricEntry.timestamp >= since)
            latency_result = await session.execute(stmt_latency)
            avg_latency = float(latency_result.scalar() or 0)
            
            # 依模型統計 Token 消耗
            stmt_model = select(MetricEntry.model_name, func.sum(MetricEntry.token_usage)).where(MetricEntry.timestamp >= since).group_by(MetricEntry.model_name)
            model_usage_result = await session.execute(stmt_model)
            model_usage_data = {row[0]: row[1] for row in model_usage_result.all() if row[0]}
            
            return {
                "total_tokens": total_tokens.scalar() or 0,
                "avg_latency": float(avg_latency.scalar() or 0),
                "status_distribution": {"success": 100}, # Fallback placeholder
                "model_usage": model_usage_data
            }
    except Exception as e:
        import traceback
        log(f"❌ 讀取 Metrics 失敗: {e}")
        log(traceback.format_exc())
        return None
