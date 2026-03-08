"""
定義任務執行紀錄模型 (History)。
對應原本的 scheduler_history.sqlite 內容。
"""
import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from core.database import Base

class TaskHistory(Base):
    __tablename__ = "task_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_name = Column(String(100), nullable=False)
    execution_time = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(20), nullable=False) # e.g. "SUCCESS", "FAILED"
    message = Column(Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "task_name": self.task_name,
            "execution_time": self.execution_time.isoformat(),
            "status": self.status,
            "message": self.message
        }
