"""
定義效能指標模型 (Metrics)。
用於追蹤 Token 消耗、執行延遲與成功率。
"""
import datetime
from sqlalchemy import Column, Integer, String, DateTime, BigInteger
from core.database import Base

class MetricEntry(Base):
    __tablename__ = "harness_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None))
    task_type = Column(String(50), nullable=False) # e.g. "ask", "briefing"
    model_name = Column(String(50), nullable=True) # e.g. "gpt-4o", "claude-3-5-sonnet"
    token_usage = Column(BigInteger, default=0)
    latency_ms = Column(Integer, default=0)
    status = Column(String(20), nullable=False) # e.g. "success", "error"

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "task_type": self.task_type,
            "model_name": self.model_name,
            "token_usage": self.token_usage,
            "latency_ms": self.latency_ms,
            "status": self.status
        }
