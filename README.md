# 🚀 LazyBridge - Antigravity AI 橋接器

> [!NOTE]
> 本專案基於其強大的系統韌性，特別感謝原作者提供核心靈感與 CDP 注入技術。

LazyBridge 是一個生產級的連通工具，能將 Discord 與您的開發環境 (Antigravity AI) 進行雙向串接。它具備高度自動化能力。

---

## 🎭 核心靈魂：私人秘書 (SOUL.md)

本系統不再只是冰冷的機器人，而是由專屬 AI 靈魂 **Mandy** 驅動。

- **身份**：您的私人秘書兼品質審查員。
- **特質**：直來直往、行事果決、抱持絕對的支持與忠誠。
- **自動化模式**：具備「自動化開發」習慣，始終使用 `SafeToAutoRun: true` 進行非破壞性指令。
- **真人語調 (Humanizer-zh)**：拒絕機器人官腔，說話有觀點、有節奏，避開 AI 常用詞。
- **動態載入**：系統啟動時自動載入 `SOUL.md`，您隨時可以修改根目錄下的檔案來調整她的性格，無需重啟服務。
- **願景**：嚴格把關品質，與使用者一起奔向目標。

---

## 🏛️ 系統架構 (Architecture)

LazyBridge 採用模組化、異步驅動的架構，確保高可用性與擴展性：

### 1. 核心層 (Core Tier)

- **Unified Message Routing**: 採用「訊息全路由」機制。不論是 Discord 命令還是直接私訊，都會先進入 Redis 隊列，確保任務不漏接且具備 L2 韌性。
- **CDP Bridge**: 透過 Chrome DevTools Protocol 實現無 API 限制的內容生成，支援視覺化操控。
- **Task Queue**: 基於 Redis 的異步隊列，平衡高負載請求。
- **Database**: PostgreSQL 存儲任務狀態、記憶引擎數據與排程資訊。
- **ECC Usage Reporting**: 全自動 Token 消耗與成本監控，支援多模型統計，並整合於每日晨報中。
- **Hybrid RAG (Local Embedding)**: **[New]** 整合了 `BAAI/bge-m3` 本地向量模型與 `FAISS` 資料庫，實現「本地檢索 + 雲端生成」的混合架構，大幅節省 Token 成本並提升回應精確度。
- **Autonomous Evolution (MetaClaw-inspired)**: **[New]** 引入「自我進化」機制。系統會自動從失敗中反思並生成「防禦技能」，並根據任務成功率動態調整技能權重。
- **Firecrawl Data Engine**: **[New]** 整合高效能網頁擷取引擎，支援「全站爬取」與「自動分段入庫」。相比瀏覽器操作，效率提升 10 倍以上，是建立 RAG 知識庫的核心動力。
- **Agent-Reach (Social Discovery)**: **[New]** 支援 X (Twitter)、Reddit、GitHub 零 API 成本搜尋與擷取，讓 Mandy 具備即時社群觀測能力。
- **PinchTab Bridge**: **[New]** 整合高效能瀏覽器自動化橋接器，支援 Accessibility Tree 快照，代幣消耗降低 13 倍，具備強大隱身能力以繞過 Cloudflare/DataDome。
- **Project Aegis (Self-Healing)**: **[V4.0]** 具備 CDP Watchdog 與自動自癒機制。系統會自動偵測瀏覽器 Port 狀態，並在掛掉時自動執行硬重啟。
- **Project Omni-View (Cyber-Aegis Dashboard)**: **[V4.1]** 基於 `aiohttp` 的次世代實時監控系統。提供進階的 Glassmorphism 視覺風格，即時追蹤各節點的神經負載 (CPU)、突觸記憶 (RAM) 與 Token 消耗分佈，並內建「紓壓小遊戲」模組。
- **Project Great Planner (Strategic Mode)**: **[V4.0]** AI 驅動的任務拆解引擎。能將複雜目標自動拆解為多個子任務並進行異步調度。
- **Project Hive Sync (Knowledge Sync)**: **[V4.0]** 跨 Agent 知識同步協議。支援 Master、Edge 與 Local 節點間的 RAG 向量數據交換，實現群體智慧。

### 2. 特色功能 (Feature Highlights) 🚀

- **Universal Document Viewer**: 系統能自動將產出的 Markdown、PDF、DOCX 等文件轉化為具備「毛玻璃 (Glassmorphism)」質感的專業網頁版預覽。
- **Portless Architecture**: 報表與預覽採用去中心化架構。成果會導向獨立的靜態伺服器 (Port 8080)，即便瀏覽器或 AI 引擎崩潰，已生成的報告依然隨時可讀。
- **Arcade Deep Compression**: **[New]** 整合於儀表板中的娛樂模組，協助開發者在等待 AI 生成長文本時進行腦力紓壓。

---

## 🎨 Cyber-Aegis Dashboard (專案監控與娛樂中心)

LazyBridge V4.1 引入了全新的視覺化監控系統，您可以透過瀏覽器即時掌握 Agent 的運作狀態。

### 1. 存取與啟動

- 儀表板隨 `worker.py` 自動啟動。
- **預設網址**：`http://localhost:8088`

### 2. 監控功能

- **Neural Load (CPU)**：即時顯示 Worker 節點的處理器負載。
- **Synaptic RAM (RAM)**：顯示系統記憶體佔用狀態。
- **Token Monitor**：
  - **7-Day Trend**：過去 7 天的 Token 消耗統計。
  - **Model Breakdown**：各模型（GPT-4o, Claude, Gemini, CDP）的消耗比例分析。
- **System Trace**：即時滾動顯示系統底層日誌。

### 3. Arcade Module (旗艦小遊戲機)

專為開發者設計的內建小遊戲，所有遊戲均套用 Cyber-Aegis 霓虹風格：

- **🕹️ Tetris (俄羅斯方塊)**：
  - **操作**：方向鍵控制。
  - **功能**：具備等級增長與分數統計。
- **🐍 Snake (貪食蛇)**：
  - **操作**：鍵盤方向鍵控制。
  - **特性**：具備「防自殺性轉向」保護邏輯，流暢的霓虹軌跡效果。
- **♟️ Gomoku (五子棋 AI)**：
  - **對手**：內建「啟發式評分」AI，會主動計算攻防價值。
  - **操作**：滑鼠點擊網格即可落子，AI 具備擬人化思考延遲 (0.4s)。

### 3. 韌性與安全層 (Resilience & Security)

- **參考 SkyClaw 自癒架構**：
  - **L1: Runtime Resilience**: 具備斷路器 (Circuit Breaker) 保護，防範 API 崩潰。
  - **L2: Task Continuity**: 任務狀態持久化，支援 Worker 重啟後的進度恢復。
  - **L3: Cognitive Correction**: 自動檢測並修正 AI 格式錯誤。
- **AgentShield**: 攔截危險指令、遮蔽機敏數據。

### 4. 自主處理層 (Autonomous Tier)

- **Concurrent Worker**: 高階任務調度器，透過 **多重併發管道 (Multi-Pipeline)** 切分 UI、瀏覽器與背景任務。
- **Unified Message Routing**: 所有的 Discord 訊息皆透過 Redis 隊列統一路由，確保任務不遺漏且處理有序。
- **Automatic Failover**: 當 Antigravity UI 忙碌時，系統具備自動降級機制，可切換至 API 引擎模式直接回覆，提升回應率。
- **Memory Engine**: 基於語意壓縮的長短期記憶系統，讓 AI 具備跨對話的記憶能力。
- **Skill Engine**: 支援從 `openclaw/skills` 動態同步並掛載 AI 技能。
- **Local RAG Service**: 使用 `BAAI/bge-m3` (8192 context) 在本地 CPU 生成向量。系統會自動索引 Session 摘要、Custom 筆記及 Context Hub 文件。
- **Firecrawl Data Hub**: 整合 Scrape / Crawl / Map 三大能力，支援將整個文檔網站一鍵轉化為 Markdown 並自動匯入 RAG。
- **Evolution Engine (Post-Mortem)**: 當任務失敗或 API 降級時，系統自動啟動「死後驗屍」分析，萃取失敗原因並產出預防性的「護衛技能 (Guard Skills)」。
- **Dynamic Skill Injection**: 根據任務類型自動從技能庫選取最相關的 3 條「動態技能」注入 System Prompt，讓 Mandy 隨著專案進展變得越來越聰明。
- **AI Browser Automation (browser-use)**:
  整合了 `browser-use` 框架，使 AI 能夠透過視覺意識自動操作瀏覽器執行複雜研究任務。
- **SOUL Driven Autonomy**: AI (Mandy) 會根據 `SOUL.md` 的指引，在判斷資訊不足時主動發起 `BRAVO_BROWSE` 自主瀏覽請求。
- **The Hive Mind (V4.0 Architecture)**:
  - **Self-Healing Heartbeat**: 背景每 15 分鐘執行一次系統自審 (`run_self_audit`)。
  - **Strategic Sub-tasking**: 支援複雜任務的自動鏈式處理。
  - **Distributed Knowledge**: 透過 API 端點實現點對點的向量索引同步。

---

## 🌐 AI 瀏覽器自動化 (AI Browser Automation)

本專案深度整合了 `browser-use` 框架，讓 Agent 具備「自動導航與網頁操控」能力：

### 核心特性

- **視覺導航**：AI 會自動分析 DOM 結構與頁面截圖，精確執行點擊、輸入、捲動等動作。
- **自主觸發 (BRAVO_BROWSE)**：當 Mandy 認為需要查實時資訊時，會主動在回覆中加入處理標記，Worker 會自動捕捉並轉入瀏覽任務。
- **CDP 連接**：直接接軌專案既有的 Antigravity CDP 會話 (Port 9222)，確保 AI 操作與您的瀏覽器同步。
- **多 LLM 支援**：系統支援 **Anthropic**, **OpenAI**, 與 **Google Gemini**。

---

## 🧠 自我進化與知識獲取 (Evolution & Knowledge)

本專案引入了受 **MetaClaw** 啟發的「動態進化」架構，讓 Mandy 具備學習能力：

### 1. 動態技能庫 (Dynamic Skills)

- **冷啟動 (Skill Seeding)**：啟動時自動掃描 `rules/` 目錄，將靜態 Markdown 規則轉化為向量化的「技能子」。
- **語意匹配**：每次任務處理時，系統會自動搜尋與當前問題最相關的 3 條技能進行精準注入。
- **生存競爭**：使用 **EMA (Exponential Moving Average)** 追蹤技能效能。高成功率技能會被頻繁選用，低效技能則會逐漸邊緣化。

### 2. 失敗反思機制 (Post-Mortem Evolution)

- **雙層分析**：
  - **精簡層**：快速反射，記錄錯誤類型。
  - **深度層**：調用高階 LLM 分析失敗根因，並自動產出「新技能」注入資料庫以防未來重複犯錯。

### 3. Firecrawl 知識擷取管道

- **高效抓取**：相比模擬人類操作，Firecrawl 直接產出 LLM 優化的 Markdown，速度更快且結構更乾淨。
- **全站索引**：`/crawl` 指令可掃描整個網域並自動分段、向量化後匯入本地 RAG 索引。

### 4. Agent-Reach 社群脈絡

- **跨平台探測**：專門處理動態內容（Reddit 貼文、GitHub README、Twitter 討論）。
- **零 API 成本**：無需申請昂貴的開發者帳密即可獲取公開討論數據。

---

## ⚡ 效能與任務調度 (Performance & Scheduling)

### 1. 多重併發管道 (Multi-Pipeline Architecture)

為避免耗時長的瀏覽任務或 UI 操作卡住快速的 API 請求，Worker 實作了專用的併發管道：

| 管道類型 | 併發數 | 任務範例 | 說明 |
| :--- | :--- | :--- | :--- |
| 🖥️ **UI Pipeline** | 1 | `cdp_ask`, `presentation` | 專供 VS Code UI 操作，嚴格順序執行以防衝突。 |
| 🌐 **Browser Pipeline** | 2 | `web_browse` | 處理高資源消耗的無頭瀏覽器自動化。 |
| ⚡ **BG Pipeline** | 5 | `ask`, `briefing`, `chub` | 處理極速 API 呼叫與背景邏輯。 |

### 2. 智慧降級與重試 (Smart Failover & Retry)

- **UI 忙碌偵測**：CDP 注入腳本會即時檢查 Antigravity UI 是否正在「生成中」或「停止按鈕已啟動」。
- **自動降級 (Failover)**：若 UI 管道連續 3 次判定為忙碌，`cdp_ask` 任務會自動降級為 **API Mode (Headless)**，直接調用 LLM 並回覆至 Discord，無需等待 UI 解鎖。
- **Token 優化**：整合 Toonify 技術，自動壓縮上下文，節省運算成本。

### 快速開始

1. **設定 API Key**：在 `.env` 中填寫對應的 Key (詳見下方環境變數章節)。
2. **確保 Chrome 偵錯模式已開啟**：Windows 請運行 `chrome.exe --remote-debugging-port=9222`。
3. **執行指令**：在 Discord 輸入 `/browse [任務描述]`。

### 開發者偵錯 (Troubleshooting)

若遇到執行問題，可使用內建工具進行診斷：

- **連線測試**：執行 `python scripts/test_browser_use.py` (整合測試)。
- **CDP 診斷**：確認 `http://localhost:9222/json` 是否能回傳分頁列表。
- **常見錯誤**：
  - `AttributeError: provider`：請確保已安裝 `langchain-anthropic` 或 `google-genai` 等指定版本（已整合於 `requirements.txt`）。
  - `ImportError: BrowserConfig`：本專案已修正此 API 變動，請確保使用 `Browser(cdp_url=...)` 進行初始化。

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
│   └── imported/              # 從 Awesome-Agent-Skills 導入的專業技能
└── reports/                   # 簡報與文檔存檔
```

---

## 🛠️ 安裝與啟動 (Setup & Installation)

為了確保系統穩定運行，請按照以下步驟進行配置：

### 1. 環境需求 (Prerequisites)

- **Python 3.8+**
- **Node.js 16+** (供 `chub` 及網頁預覽組件使用)
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
# RAG 額外依賴 (已包含在 requirements.txt)
# pip install sentence-transformers faiss-cpu

# 檢查 Python 與 依賴版本
python --version
python -c "import firecrawl; print('Firecrawl SDK version:', firecrawl.__version__)"
```

### 3. 配置環境變數 (.env)

請複製 `.env.example` 並重新命名為 `.env`，填寫以下關鍵資訊：

- `DISCORD_BOT_TOKEN`: 您的 Discord Bot Token。
- **Firecrawl 配置** (新增)：
  - `FIRECRAWL_MODE`: `self_hosted` (推薦) 或 `cloud`。
  - `FIRECRAWL_URL`: 若為自架請填 `http://localhost:3002`。
  - `FIRECRAWL_API_KEY`: 自架可填任意值，雲端請填官方 Key。
- **LLM API Keys** (至少填寫一個)：
  - `ANTHROPIC_API_KEY`: Claude 3.5 Sonnet (推薦)
  - `OPENAI_API_KEY`: GPT-4o
  - `GEMINI_API_KEY`: Gemini 1.5 Pro/Flash
- `DATABASE_URL`:
  - PostgreSQL: `postgresql+asyncpg://user:password@localhost:5432/lazybridge`
  - SQLite: `sqlite+aiosqlite:///scheduler_history.sqlite`

### 4.資料庫與 RAG 系統配置 (Database & RAG Setup)

本專案支援 **PostgreSQL** (推薦用於生產) 與 **SQLite** (開發測試用)，並整合了 **Local RAG (本地檢索增強生成)** 系統。

- **依賴項**: 系統使用 `sentence-transformers` 與 `faiss-cpu`。安裝 `requirements.txt` 即包含這些依賴。
- **資料庫設定**: 修改 `.env` 中的 `DATABASE_URL`。
- **資料表初始化**: 執行以下腳本，系統會自動根據模型定義建立所有必要的資料表：

  ```bash
  python scripts/init_postgres.py
  ```

- **Local RAG 首次執行**:
  系統啟動時會自動載入 `BAAI/bge-m3` 模型。如果是首次執行，Worker 會自 Hugging Face 下載模型權重（約 2GB），請確保網路連線正常。載入後，系統會自動產生 `memory/local_rag_index.faiss` 用於存儲向量索引。

> [!IMPORTANT]
> 初始化腳本會自動讀取 `models/` 目錄下的所有定義，確保 `scheduled_tasks`, `task_history`, `memory_entries`, `task_trace` 與 `harness_metrics` 同步建立。

### 5. 安裝 Context Hub (chub) 核心

本專案整合了 Andrew Ng 的 Context Hub，請務必安裝 CLI 工具：

```bash
npm install -g @aisuite/chub
```

### 6. 啟用全自動化模式 (Always Run)

為實現 OpenClaw 般的極速開發，系統預設啟用了「直接執行」權限（免除終端機確認）。
詳細配置請參考相關自動化指南。

### 7. 啟動服務

建議開啟兩個終端機分別執行：

1. **啟動 Bot 監聽**: `python main.py`
2. **啟動任務執行器**: `python worker.py`

### 8. NotebookLM 知識庫同步 (NotebookLM Sync)

本專案整合了 `jackc1111/antigravity-notebooklm-mcp`，支援將本地文檔自動同步至 Google NotebookLM。

- **安裝**:

  ```bash
  cd tools/notebooklm-mcp
  npm install
  npm run build
  ```

- **身份驗證 (修復 Permission Denied)**:
  由於 Google 的 HttpOnly Cookie 限制，建議使用 **"Copy as cURL"** 方式：
  1. 在瀏覽器開啟 NotebookLM 並登錄。
  2. 開啟 DevTools (F12) -> Network。
  3. 找到 `batchexecute` 請求 -> 右鍵 -> Copy as cURL (bash)。
  4. 提取 Cookie 並更新至 `~/.notebooklm-mcp/auth.json`。
- **執行同步**:

  ```bash
  # 在 tools/notebooklm-mcp 執行
  node --loader ts-node/esm sync-hbms.ts
  ```

### 9. Firecrawl Self-Hosted 部署 (推薦)

為了獲得無限制的網頁爬取能力，建議部署自架版 Firecrawl：

1. **Clone Repo**: `git clone https://github.com/mendableai/firecrawl.git <YOUR_FIRECRAWL_PATH>`
2. **配置環境**: 在 `<YOUR_FIRECRAWL_PATH>/.env` 設定 `PORT=3002`。
3. **啟動**:

   ```bash
   cd <YOUR_FIRECRAWL_PATH>
   docker compose build
   docker compose up -d
   ```

4. **LazyBridge 配置**: 在 `.env` 設定 `FIRECRAWL_MODE=self_hosted` 與 `FIRECRAWL_URL=http://localhost:3002`。

---

---

## 🐋 Docker 部署 (Docker Deployment)

如果您偏好使用 Docker，可以使用專案提供的 `docker-compose.yml` 快速啟動完整環境（包含 Bot, Worker, Redis, PostgreSQL）：

### 1. 啟動所有服務

```bash
docker-compose up -d --build
```

這會自動啟動以下容器：

- `lazybridge_bot`: Discord 指令監聽。
- `lazybridge_worker`: 背景任務執行器。
- `lazybridge_redis`: 任務隊列。
- `lazybridge_db`: PostgreSQL 數據庫。
- `lazybridge_reports`: 靜態報表伺服器 (供 `/present`, `/briefing` 與 **所有文件預覽** 使用，對應 Port `8080`)。

### 2. 查看簡報、晨報與各類文件網頁版

當機器人產出文件（如 Markdown, PDF, DOCX）後，會自動透過 `Universal Document Viewer` 進行轉換，並回傳一個網址：
`http://localhost:8080/filename.html` (或原始格式)

#### 報表伺服器運作機制

- **靜態路徑**: 所有產生的網頁與文件皆儲存於根目錄下的 `reports/` 資料夾。
- **即時轉換**:
  - **Markdown**: 使用 `fenced_code` 與 `tables` 擴充插件轉換為語意化 HTML。
  - **Word (DOCX)**: 透過 `mammoth` 提取乾淨的 HTML 結構。
  - **PDF/圖片**: 直接同步路徑由瀏覽器原生渲染。
- **Premium 視覺**: 統一套用 **Glassmorphism (毛玻璃)** 設計系統，包含 12px 背景模糊、深色漸層背景與 Sky Blue 強調色。

#### Portless 報表架構 (Portless Architecture)

為了提升 L1/L2 韌性並降低對瀏覽器注入的依賴，LazyBridge 實作了 **Portless 去中心化架構**：

- **概念**: 不再強求將所有 HTML 直接「注入」到當前操控的瀏覽器分頁，而是將成果導向獨立的靜態伺服器。
- **優點**:
  - **解耦**: 瀏覽器崩潰不影響已生成的報表。
  - **可靠**: 透過簡單的 HTTP Get 即可讀取，減少 CDP 傳輸大數據時的阻塞。
  - **跨裝置**: 只要在同網域下，其他手機或電腦也能透過 URL 訪問報表伺服器。

#### 報表伺服器技術規格 (Technical Stack)

- **伺服器核心**: Python 3.10 `http.server` (輕量化異步靜態檔案服務)。
- **渲染技術**:
  - **Styles**: Glassmorphism CSS 3 / CSS Variables / Backdrop Filter。
  - **Engines**: `markdown-it` 風格解析器 (Python `markdown` 庫) / `mammoth` (DOCX 結構提取)。
- **部署方式**: Docker 容器化部署 (Port 8080) 或 本地 Python 指令啟動。

#### 📈 ECC Usage Reporting (全模型監控)

為了精確掌控 AI 成本與效能，本專案實作了全自動化報表系統：

- **多模型支援**: 自動區分並追蹤 `gpt-4o`, `claude-3-5-sonnet`, `gemini-1.5-flash` 與 `Antigravity (CDP)`。
- **指標監控**: 即時記錄各模型的 Token 消耗、處理延遲 (Latency) 與 任務成功率。
- **視覺化儀表板**: 生成高質感的 Glassmorphism HTML 報表 (`reports/usage_report.html`)。
- **自動化推播**: 整合於每日晨報，自動在 Discord 頻道發送使用量摘要。

若不使用 Docker，可手動啟動報表伺服器：

1. **安裝轉換依賴**:

   ```bash
   pip install markdown mammoth
   ```

2. **建立報告目錄**: `mkdir reports`
3. **啟動靜態服務**:

   ```bash
   # 在專案根目錄執行
   python -m http.server 8080 --directory reports
   ```

#### 🌐 外網與跨裝置存取配置 (External Access)

預設情況下，報表只允許在執行機器人本機 (`localhost`) 瀏覽。如果您希望在外網 (例如手機 4G) 或其他裝置上觀看，請在 `.env` 中設定 `REPORTS_BASE_URL`：

##### 選項 1：使用 Tailscale (目前採用本方案, 推薦, 高安全性)

如果您與機器人裝置皆登入 Tailscale，可直接使用分配的虛擬 IP：

```env
# .env 檔案設定範例
REPORTS_BASE_URL=http://<YOUR_TAILSCALE_IP>:8080
```

##### 選項 2：區域網路 (LAN) 存取

將 IP 改為您電腦的 IPv4 地址 (確保防火牆開啟 8080 port)：

```env
REPORTS_BASE_URL=http://192.168.1.100:8080
```

##### 選項 3：內網穿透 (localtunnel / ngrok)

```env
REPORTS_BASE_URL=https://lazy-bridge-report.loca.lt
```

#### 選項 4：進階動態連結中心 (Dynamic Link Hub - 目前暫停使用)

這是之前使用的進階解決方案，目前專案已暫停 Cloudflare 隧道，改為全面使用 Tailscale (選項 1)。以下資訊僅供備查。

使用 Cloudflare Workers 作為固定入口，並透過同步腳本自動更新隨機網址。即使本地隧道（localtunnel）重啟，對外的網址也永遠固定不變。

##### 1. 單一服務同步模式

適合只需要對外公開「報表伺服器 (8080)」的情境。

- **部署**: 將 `scripts/cf_worker.js` 部署到 Cloudflare Workers 並綁定名為 `LINKS` 的 KV。
- **設定 (.env)**:

    ```env
    REPORTS_BASE_URL=https://您的固定網址.workers.dev
    CF_ACCOUNT_ID=你的ID
    CF_KV_NAMESPACE_ID=你的KV_ID
    CF_API_TOKEN=你的TOKEN
    ```

- **執行**: `python scripts/link_sync.py`

##### 2. 多服務路由模式 (Multi-Service Support) 🚀

適合需要同時公開多個服務（如 8080 報表與 3000 HBMS）的情境。

- **原理**: 透過路徑導向不同服務網址。
- **設定 (.env)**:

    ```env
    MULTI_SERVICE_MAP=report:8080,hbms:3000
    ```

- **部署**: 使用同一個 `scripts/cf_worker.js`（支援路由邏輯）。
- **啟動**:

    ```bash
    python scripts/link_sync_multi.py
    ```

- **存取網址**:
  - `https://您的網域.dev/` -> 導向 8080 報表
  - `https://您的網域.dev/hbms/` -> 導向 3000 系統

設定完成後，機器人推播的「網頁版晨報」與「各類文件預覽連結」將會自動採用這個對外公開的網址！即使您身在戶外，也能隨時隨地安全地存取報表。

### 3. 查看日誌

```bash
docker-compose logs -f bot
docker-compose logs -f worker
```

---

## 📊 核心資料庫結構 (Core Table Schemas)

本專案的核心由四個主要資料表構成，負責任務調度、記憶儲存與效能監控：

### 1. `scheduled_tasks` (自動化排程)

儲存所有週期性或定時執行的任務定義，系統啟動時會由 `scheduler.py` 自動載入並註冊至傳統計時器。

| 欄位 | 類型 | 預設值 | 說明 |
| :--- | :--- | :--- | :--- |
| `id` | Integer (PK) | - | 任務唯一識別碼。 |
| `name` | String(100) | - | 任務名稱 (例如：`daily_briefing`)。 |
| `time` | String(10) | - | 24小時制執行時間 (例如：`09:30`)。 |
| `type` | String(50) | - | 任務類型：`briefing` (晨報) 或 `command` (系統指令)。 |
| `params` | JSON | `{}` | briefing 擴充參數 (例如：篩選信件類別、新聞主題)。 |
| `command` | String(500) | `None` | 當類型為 `command` 時要執行的 Shell 指令。 |
| `enabled` | Boolean | `True` | 是否啟用該排程任務。 |

### 2. `task_history` (執行審計日誌)

追蹤所有任務的執行歷史，是系統穩定性分析的重要指標。

| 欄位 | 類型 | 預設值 | 說明 |
| :--- | :--- | :--- | :--- |
| `id` | Integer (PK) | - | 遞增編號。 |
| `task_name` | String(100) | - | 對應 `scheduled_tasks` 的名稱。 |
| `execution_time` | DateTime | `now()` | 任務啟動的 UTC 精確時間。 |
| `status` | String(20) | - | 狀態标识：`SUCCESS` 或 `FAILED`。 |
| `message` | Text | `None` | 執行結果的完整輸出摘要或詳細錯誤報錯 (Traceback)。 |

### 3. `task_trace` (L2 韌性追蹤 - UUID 架構)

這是實作 **SkyClaw L2 韌性** 的核心表格，採用非線性追蹤架構，支援任務嵌套與狀態恢復。

| 欄位 | 類型 | 說明 |
| :--- | :--- | :--- |
| `task_id` | UUID (PK) | 該次任務的主鍵 UUID，用於在異步環境中精確定位。 |
| `parent_id` | UUID | 關聯的父任務 ID。 |
| `task_type` | String | 任務類別 (例如：`ask`, `briefing`, `skill_sync`)。 |
| `payload` | JSONB | 任務啟動時的所有原始參數快照。 |
| `status` | String | 當前生命週期：`PENDING`, `IN_PROGRESS`, `SUCCESS`, `FAILED`。 |
| `step_index` | Integer | 目前執行到的推理/執行步驟 index (0-indexed)。 |
| `trace_log` | JSONB | 推理日誌足跡，儲存 AI 的思考路徑與中間結果。 |
| `error_msg` | Text | 發生異常時的詳細文字說明，方便重試機制判別。 |
| `created_at` | DateTime | 記錄建立時間。 |

### 4. `memory_entries` (Agent 長短期記憶庫)

支援語意壓縮與脈絡過濾的核心記憶存儲。

| 欄位 | 類型 | 索引 | 說明 |
| :--- | :--- | :--- | :--- |
| `id` | Integer (PK) | ✅ | 遞增索引。 |
| `category` | String(50) | ✅ | 分類：`session` (對話日誌), `pitfall` (錯誤經驗), `custom` (用戶筆記)。 |
| `title` | String(200) | - | 記憶主題 (例如：開發進度、特定 Bug 的解決方案)。 |
| `content` | Text | - | Markdown 格式的完整記憶內容。 |
| `created_at` | DateTime | - | 記憶存入時間。 |

### 5. `harness_metrics` (系統效能控管)

記錄 ECC (Engine Control Center) 系統的資源消耗與回應效能。

| 欄位 | 類型 | 說明 |
| :--- | :--- | :--- |
| `id` | Integer (PK) | 效能紀錄編號。 |
| `timestamp` | DateTime | 取樣時間點 (UTC)。 |
| `task_type` | String(50) | 任務類型 (ask, briefing, presentation)。 |
| `model_name` | String(50) | **具體模型名稱 (gpt-4o, claude-3-5-sonnet, gemini-1.5-flash, Antigravity (CDP))**。 |
| `token_usage` | BigInteger | 累計 Token 消耗。 |
| `latency_ms` | Integer | 處理延遲 (ms)。 |
| `status` | String(20) | 結果：`success` 或 `error`。 |

---

---

## 🎮 使用指令 (Usage)

### 1. 核心與 AI 指令 (Core & AI)

| 指令 / 行為 | 說明 |
| :--- | :--- |
| **直接傳訊 (Direct Message)** | **Unified Routing**: 所有的私訊皆會轉入 `cdp_ask` 隊列，依序注入 Antigravity 執行。若 UI 忙碌則自動降級至 API 回覆。 |
| `/ask [內容]` | 向 AI 發問 (優先調用 **Local RAG** 檢索相關記憶後，再送往 API 引擎) |
| `/browse [任務]` | **AI 瀏覽器自動化**：用自然語言操控網頁 (如：搜尋、資料收集)，支援 `BRAVO_BROWSE` 自動觸發。 |
| `/present [主題]` | 讓 AI 為您製作一份專業的 HTML 簡報 |
| `/briefing` | 立即產出晨報 (整合郵件、行事曆與新聞，並包含 **Token 使用量總覽**) |
| `/skill-sync [owner/slug]` | 從雲端同步新技能 (例如 `halthelobster/proactive-agent`) |
| `/skills [list\|seed]` | **[New]** 查看目前動態技能庫的效能統計與權重 |
| `/post-mortem [limit]` | **[New]** 查看系統近期的「失敗反思報告」與自動產出的保護技能 |
| `/scrape <url>` | **[New]** 強力抓取單一網頁並轉為 Markdown 匯入 RAG |
| `/crawl <url> [max]` | **[New]** 全站爬取整個網站 (預設 30 頁) 並自動匯入知識庫 |
| `/map <url>` | **[New]** 偵察網站 URL 結構，列出可爬取的路徑 |
| `/social_search <platform> <query>` | **[New]** 社群搜尋 (twitter, reddit, github, youtube) |
| `/social_read <url>` | **[New]** 擷取社群貼文內容並匯入 RAG |
| `/pinch <url>` | **[New]** **PinchTab 高效瀏覽**：使用無障礙樹快照，省代幣且防偵測。 |
| `/pinch_health` | **[New]** 檢查 PinchTab 服務狀態。 |
| `/pinch_snap <tab_id>` | **[New]** 獲取 PinchTab 分頁的細節快照。 |
| `/task type:strategic task:"內容"` | **[V4.0]** **Strategic Mode**：啟動大局規劃模式，自動拆解並執行複合任務。 |
| `/harness_status` | **查看性能報表儀表板 (視覺化呈現各模型 Token 消耗與 RAG 效益)** |

### 2. 語音功能 (Voice Features - 🔴 目前暫停)

| 指令 | 說明 |
| :--- | :--- |
| `/join` | 讓 Mandy 進入語音頻道 (暫停中) |
| `/leave` | 讓 Mandy 離開語音頻道 (暫停中) |
| `/speak [文字]` | 讓 Mandy 在頻道說話 (暫停中) |

### 2. Context Hub (上下文與學習庫)

整合了 `@aisuite/chub`，大幅降低 AI 幻覺並允許 Agent 進行本地除錯與學習。

| 指令 | 說明 |
| :--- | :--- |
| `/chub search [關鍵字]` | 搜尋最新的 API 官方文件。 |
| `/chub get [ID] [語言]` | 抓取文件並自動寫入 `Memory Engine` 的長期記憶中，供後續發問使用。 |
| `/chub annotate [ID] [筆記]` | 為已載入的文件加入除錯筆記 (Annotations)，下次載入時會自動生效。 |

### 4. NotebookLM 知識管理 (Knowledge Management)

| 指令 | 說明 |
| :--- | :--- |
| `/notebook sync` | 將專案知識庫同步至 NotebookLM |
| `/research [主題]` | 啟動 NotebookLM Deep Research 並導入結果 |

### 3. 記憶引擎 (Memory Engine)

| 指令 | 說明 |
| :--- | :--- |
| `/memory save [主題]` | 記錄重要開發決定或對話重點到資料庫 |
| `/memory reload` | 讓 AI 重新讀取並整理目前專案的記憶與進度 |
| `/memory diary` | 產出今日工作或溝通的自動回顧日誌 |
| `/memory list` | 檢視記憶資料庫中的歷史紀錄 |

### 3. 系統排程管理 (Task Scheduling - Slash Commands)

| 指令 | 說明 |
| :--- | :--- |
| `/list_tasks` | 列出目前所有的排程任務與狀態 |
| `/add_task [名稱] [時間] [類型]` | 新增一個自動化排程任務 (如每日報時、定期數據抓取) |
| `/edit_task [ID] ...` | 修改現有的排程任務設定 |
| `/toggle_task [ID]` | 切換任務的啟用/停用狀態 |
| `/delete_task [ID]` | 刪除指定的排程任務 |

### 4. 控制與診斷 (Control & Debug)

| 指令 | 說明 |
| :--- | :--- |
| `/screenshot` | 擷取當前 AI 瀏覽器分頁畫面，診斷生成過程 |
| `/tabs` | 列出目前 AI 引擎所有開啟的分頁 |
| `/harness_status` | 查看效能監控儀表板 (Token 消耗、成功率) |
| `/loop-start` | 立即啟動系統自主維護循環 |
| `/screen` \| `/mouse` \| `/click` | 顯示解析度、控制滑鼠座標 (自動化測試用) |
| `/dump` | 診斷 Scratchpad 分頁底層狀態 |

---

## 🛠️ 實用工具 (Utility Scripts)

專案 `scripts/` 目錄下提供多項維護工具，可協助管理系統：

- **資料庫管理**:
  - `python scripts/init_postgres.py`: 初始化 PostgreSQL/SQLite 資料表。
  - `python scripts/migrate_to_pg.py`: 將 SQLite 數據遷移至 PostgreSQL。
- **系統診斷**:
  - `python scripts/diagnose.py`: 全面檢查 Redis、DB 與 CDP 連線狀態。
  - `python scripts/tail_log.py`: 即時監控系統日誌。
- **任務測試**:
  - `python scripts/push_debug_task.py`: 手動派發一個測試任務至 Worker。
  - `python scripts/check_tasks.py`: 檢視資料庫中所有追蹤中的任務狀態。
- **技能開發**:
  - `python scripts/eval_skills.py`: 評估與測試已安裝技能的效能。
  - `skills/imported/prompt-engineering.md`: 提升 AI 回覆邏輯的專業技能。
  - `skills/imported/systematic-debugging.md`: 系統化除錯方法論。
  - `skills/imported/memory-systems.md`: 高階背景記憶管理。

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

---

## 🛡️ 維護與相容性政策 (Maintenance & Safety)

為了確保 LazyBridge 的穩定運行，本專案遵循「穩定優先」的更新原則：

- **影響分析**：所有套件（pip, npm）或技能（Skills）更新前，必須進行功能影響分析。
- **拒絕破壞性更新**：若更新可能導致既有功能（如 CDP 注入、語音頻道、資料庫連線）失效，系統將自動跳過更新並告知老闆。
- **版本鎖定**：核心依賴庫若無重大安全性漏洞，優先保持在當前測試通過的版本。
- **變更紀錄**：任何因相容性考量而未執行的更新，都會在此章節記錄備查。

### 📋 延期更新紀錄 (Skipped Updates)

- *目前無延期更新，所有組件均處於穩定版本。*

### 📱 社群平台整合 (Mandy)

Mandy 現在支援 FB/IG 貼文研究與草稿產生：

- `/social_draft [主題]` - 讓 Mandy 撰寫一篇社群貼文文案並提供 AI 配圖提示詞。
- `/social_account` - 查看目前連結的 Meta 粉絲專頁與帳號狀態。

> [!TIP]
> 目前專注於 **草稿生成** 與 **預覽**。如需開啟 API 直接發布功能，請在 `.env` 中設定 `FB_PAGE_ACCESS_TOKEN` 並將 `ENABLE_AUTO_POST` 設為 `true`。
