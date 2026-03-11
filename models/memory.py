"""
定義記憶引擎的資料庫模型 (MemoryEntry)。
用於儲存對話日誌 (Sessions)、自動踩坑紀錄 (Pitfalls) 與自訂筆記 (Custom)。
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from core.database import Base

class MemoryEntry(Base):
    __tablename__ = "memory_entries"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), index=True, nullable=False) # e.g., "session", "pitfall", "custom"
    title = Column(String(200), nullable=False)               # e.g., "auto-pitfall-20260309", "todo"
    content = Column(Text, nullable=False)                    # Markdown content
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "category": self.category,
            "title": self.title,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
