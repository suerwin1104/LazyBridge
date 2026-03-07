"""
核心設定模組：載入 config.json、初始化日誌、管理常數。
"""
import json
import logging
import os

# --- 常數 ---
CDP_PORT = 9222
CDP_URL = f"http://127.0.0.1:{CDP_PORT}/json"
DEFAULT_GUILD_ID = "1209429528632361000"
BRIEFING_CHANNEL_ID = 1209429529140142104
BRIEFING_TIME = "10:30"

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
    return load_config()["bot_token"]


def get_owner_id():
    return load_config().get("owner_id")


# --- 環境變數 ---
def load_env():
    """從 .env 檔案載入環境變數（簡易實作，不依賴 python-dotenv）。"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
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
