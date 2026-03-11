"""
核心設定模組：載入 config.json、初始化日誌、管理常數。
"""
import json
import logging
import os

# --- 環境變數 ---
def load_env():
    """從 .env 檔案載入環境變數（簡易實作，不依賴 python-dotenv）。"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    try:
                        key, val = line.split("=", 1)
                        if key not in os.environ:
                            os.environ[key] = val.strip(' "\'')
                    except Exception:
                        pass

# 模組載入時立刻讀取 env，確保後續變數正確
load_env()

# --- 常數 ---
CDP_PORT = 9222
CDP_URL = f"http://127.0.0.1:{CDP_PORT}/json"
DEFAULT_GUILD_ID = "1209429528632361000"
BRIEFING_CHANNEL_ID = 1209429529140142104
BRIEFING_TIME = "10:30"
SCHEDULER_TASKS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scheduler_tasks.json")
SCHEDULER_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scheduler_history.sqlite")

# Redis & Queue Config
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
TASK_QUEUE = os.getenv("TASK_QUEUE", "lazybridge_tasks")

# Database Config (Phase 3)
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///scheduler_history.sqlite")

# LLM 憑證 (Phase 2)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Toonify Config (Phase 4)
TOONIFY_ENABLED = os.environ.get("TOONIFY_ENABLED", "true").lower() == "true"

# Reports Server Config
REPORTS_BASE_URL = os.getenv("REPORTS_BASE_URL", "http://localhost:8080")


# --- 設定載入 ---
_config = None


def load_config(path="config.json"):
    """載入 config.json 並快取結果。"""
    global _config
    if _config is None:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), path)
        with open(config_path, "r", encoding="utf-8") as f:
            _config = json.load(f)
    return _config


def get_bot_token():
    load_env()
    # 優先從環境變數讀取，若無則從 config.json 讀取 (相容性)
    return os.environ.get("DISCORD_BOT_TOKEN") or load_config()["bot_token"]


def get_owner_id():
    load_env()
    return os.environ.get("OWNER_ID") or str(load_config().get("owner_id", ""))


# --- 環境變數 ---
def load_env():
    """從 .env 檔案載入環境變數（簡易實作，不依賴 python-dotenv）。"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())


def get_apify_token():
    load_env()
    return os.environ.get("APIFY_TOKEN")


# --- 日誌 ---
LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bot.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def log(msg):
    """同時輸出至 console 與日誌檔。"""
    print(msg)
    logging.info(msg)


def get_soul_content():
    """從根目錄載入 SOUL.md 作為 AI 的核心人格與原則設定。"""
    soul_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "SOUL.md")
    if os.path.exists(soul_path):
        try:
            with open(soul_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            log(f"⚠️ 載入 SOUL.md 失敗: {e}")
    return "You are a helpful AI assistant."
