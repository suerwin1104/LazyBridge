# 🚀 LazyBridge - Antigravity AI 橋接器

> [!NOTE]
> 本專案基於其強大的系統韌性，特別感謝原作者提供核心靈感與 CDP 注入技術。

LazyBridge 是一個生產級的連通工具，能將 Discord 與您的開發環境 (Antigravity AI) 進行雙向串接。它具備高度自動化能力。

---

## 🎭 核心靈魂：私人秘書 (SOUL.md)

本系統不再只是冰冷的機器人，而是由專屬 AI 靈魂 **XXX** 驅動。

- **身份**：您的私人秘書。
- **特質**：直來直往、行事果決、抱持絕對的支持與忠誠。
- **動態載入**：系統啟動時自動載入 `SOUL.md`，您隨時可以修改根目錄下的檔案來調整她的性格，無需重啟服務。
- **願景**：嚴格把關品質，與使用者一起奔向目標。

---

## 🏛️ 系統架構 (Architecture)

LazyBridge 採用模組化、異步驅動的架構，確保高可用性與擴展性：

### 1. 核心層 (Core Tier)

- **CDP Bridge**: 透過 Chrome DevTools Protocol 實現無 API 限制的內容生成。
- **Task Queue**: 基於 Redis 的異步隊列，支援任務分發。
- **Database**: PostgreSQL 存儲任務狀態、記憶引擎數據與排程資訊。

### 2. 韌性與安全層 (Resilience & Security)

- **參考 SkyClaw 自癒架構**：
  - **L1: Runtime Resilience**: 具備斷路器 (Circuit Breaker) 保護，防範 API 崩潰。
  - **L2: Task Continuity**: 任務狀態持久化，支援 Worker 重啟後的進度恢復。
  - **L3: Cognitive Correction**: 自動檢測並修正 AI 格式錯誤。
- **AgentShield**: 攔截危險指令、遮蔽機敏數據。

### 3. 自主處理層 (Autonomous Tier)

- **Concurrent Worker**: 非同步並行執行器，支援多任務同時處理。
- **Memory Engine**: 基於語意壓縮的長短期記憶系統。
- **Skill Engine**: 支援從 `openclaw/skills` 動態同步並掛載 AI 技能。

---

## 🚀 性能特性 (Performance)

- **併發執行 (Task Concurrency)**：Worker 採用非同步架構，預設允許 5 個任務並行 (`MAX_CONCURRENT_TASKS`)。
- **Token 優化**：整合 Toonify 技術，自動壓縮上下文，節省運算成本。

---

## 📁 專案結構

```text
LazyBridge/
├── main.py                    # 入口點 (啟動 Bot 監聽)
├── worker.py                  # 任務執行器 (處理 AI 與 背景任務)
├── SOUL.md                    # 祕書的性格與行為準則
├── .env                       # 機敏變數 (Token, API Keys)
├── core/                      # 基礎模組 (Config, Database, Queue, CDP)
├── bot/                       # Discord 介面模組 (Commands, Events)
├── services/                  # 核心邏輯 (AI Engine, Memory, Skill Sync)
├── models/                    # 資料庫結構模型
├── skills/                    # 動態加載的技能模組
└── reports/                   # 簡報與文檔存檔
```

---

## 🛠️ 安裝與啟動 (Setup & Installation)

為了確保系統穩定運行，請按照以下步驟進行配置：

### 1. 環境需求 (Prerequisites)

- **Python 3.8+**
- **Redis Server**: 用於任務隊列 (`brew install redis` 或 Docker 執行)。
- **PostgreSQL** (推薦): 用於生產環境。若無，系統將自動回退至 **SQLite**。
- **Google Chrome**: 需開啟遠端偵錯模式。
  - Windows: `chrome.exe --remote-debugging-port=9222`
  - macOS: `/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222`

### 2. 安裝依賴

```bash
git clone https://github.com/suerwin1104/LazyBridge.git
cd LazyBridge
pip install -r requirements.txt
```

### 3. 配置環境變數 (.env)

請複製 `.env.example` 並重新命名為 `.env`，填寫以下關鍵資訊：

- `DISCORD_BOT_TOKEN`: 您的 Discord Bot Token。
- `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`: 至少填寫一個以啟用 AI 功能。
- `DATABASE_URL`:
  - PostgreSQL: `postgresql+asyncpg://user:password@localhost:5432/lazybridge`
  - SQLite: `sqlite+aiosqlite:///scheduler_history.sqlite`

### 4. 資料庫初始化 (Database Setup)

專案使用 SQLAlchemy (Async) 進行管理。啟動前請執行初始化腳本來建立必要的資料表：

```bash
python scripts/init_postgres.py
```

> [!TIP]
> 此指令會根據 `.env` 中的 `DATABASE_URL` 自動建立 `task_trace`, `scheduled_tasks`, `memory_entries` 等表格。

### 5. 啟動服務

建議開啟兩個終端機分別執行：

1. **啟動 Bot 監聽**: `python main.py`
2. **啟動任務執行器**: `python worker.py`

---

## 🎮 使用指令 (Usage)

| 指令 | 說明 |
| :--- | :--- |
| `/ask [內容]` | 處理您的請求 (非同步模式) |
| `/present [主題]` | 為您製作專業簡報 |
| `/skill-sync [owner/slug]` | 從雲端同步新技能 (例如 `halthelobster/proactive-agent`) |
| `/briefing` | 產出整合簡報 |
| `/memory save` | 記錄重要開發決定或踩坑 |

---

## 📐 系統流圖 (System Flow)

```mermaid
graph TD
    User((Discord User)) -->|Slash Command| Bot[Discord Bot]
    Bot -->|Push Task| Redis[(Redis Queue)]
    Redis -->|Pull Task| Worker[Concurrent Worker]
    Worker -->|Load Identity| Soul[SOUL.md]
    Worker -->|Load Context| Memory[(Memory Engine)]
    Worker -->|API Request| AI[Headless AI Engine]
    Worker -->|CDP Command| Browser[Antigravity Browser]
    AI -->|Response| Worker
    Browser -->|JSON Result| Worker
    Worker -->|Final Reply| User
```
