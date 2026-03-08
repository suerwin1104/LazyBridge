"""
定義任務模型 (Task)。
對應原本的 scheduler_tasks.json 內容。
"""
from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime
from core.database import Base

class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    time = Column(String(10), nullable=False) # e.g. "10:30"
    type = Column(String(50), nullable=False) # e.g. "briefing", "command"
    
    # 用於 briefing 的參數設定 (使用 JSON 格式儲存)
    params = Column(JSON, nullable=True, default={})
    
    # 用於 command 類型的指令字串
    command = Column(String(500), nullable=True)
    
    # 任務開關
    enabled = Column(Boolean, default=True)

    def to_dict(self):
        """將 SQLAlchemy 物件轉換為字典，方便後續與舊有程式碼相容。"""
        return {
            "id": self.id,
            "name": self.name,
            "time": self.time,
            "type": self.type,
            "params": self.params,
            "command": self.command,
            "enabled": self.enabled
        }
