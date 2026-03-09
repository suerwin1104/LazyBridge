"""
資料庫連線與 Session 管理。
基於 SQLAlchemy (非同步模式) 設計，支援 PostgreSQL 與 SQLite。
"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from core.config import DATABASE_URL, log

# 建立 Base Class 供 Models 繼承
Base = declarative_base()

# 匯入所有 Model，讓 Base.metadata 能註冊到這些表格
from models.task import ScheduledTask
from models.history import TaskHistory
from models.memory import MemoryEntry
from models.metrics import MetricEntry

# 如果尚未設定 PostgreSQL URL，預設會使用 SQLite 記憶體模式來防呆
engine_url = DATABASE_URL
if not engine_url:
    engine_url = "sqlite+aiosqlite:///:memory:"
    log("⚠️ 未偵測到 DATABASE_URL，將使用 SQLite 記憶體模式 (重啟後資料遺失)")

# 建立 Async Engine
engine = create_async_engine(
    engine_url,
    echo=False,  # 設為 True 可在 Console 印出執行的 SQL，方便 Debug
    pool_pre_ping=True, # 連線前驗證，防止斷線
)

# 建立 Async Session 工廠
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False
)

async def init_db():
    """初始化資料庫表格 (如果不存在則建立)。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log("✅ 資料庫表格初始化完成 (SQLAlchemy)")

async def get_db_session():
    """回傳資料庫 session (Dependency Injection)。"""
    async with AsyncSessionLocal() as session:
        yield session
