# 🚀 LazyBridge - Antigravity AI 橋接器

> [!NOTE]
> 本專案修改自 GitHub 上的 [LazyGravity](https://github.com/tokyoweb3/LazyGravity) 專案。特別感謝原作者提供核心靈感與 CDP 注入技術。

LazyBridge 是一個強大的連通工具，能夠將 Discord 訊息與 VS Code 中的 Antigravity AI (或 Chrome 中的網頁版) 進行雙向串接。您可以直接從 Discord 發送需求，讓 AI 在您的開發環境中執行任務，並將結果回傳至 Discord。

---

## 📁 專案結構

```
LazyBridge/
├── main.py                    # 入口點（載入 → 註冊模組 → 啟動）
├── config.json                # Bot Token 等設定
├── config.example.json        # 設定範本
├── .env                       # 環境變數（APIFY_TOKEN 等）
├── requirements.txt           # Python 依賴
├── .gitignore
├── README.md
│
├── core/                      # 核心基礎設施
│   ├── config.py              #   設定載入、日誌、常數管理
│   ├── cdp.py                 #   CDP 連線、分頁掃描、JS 注入
│   └── queue.py               #   Redis 任務隊列封裝 (新增)
│
├── bot/                       # Discord Bot 模組
│   ├── commands.py            #   所有斜線指令（Cog）
│   ├── events.py              #   事件處理：on_ready、自動轉傳
│   └── scheduler.py           #   動態排程任務管理器（Cog）
│
├── services/                  # 外部服務整合
│   ├── google_workspace.py    #   Gmail / Calendar CLI 封裝
│   ├── apify_news.py          #   Apify 趨勢新聞抓取
│   └── briefing.py            #   參數化晨報組裝（GWS + Apify）
│
├── worker.py                  # 任務執行器 (Consumer) (新增)
├── scheduler_tasks.json       # 自訂排程設定檔
├── scheduler_history.sqlite   # 任務執行紀錄數據庫 (新增)
└── scripts/                   # 獨立工具腳本
    ├── diagnose.py            #   環境診斷工具
    └── test_scheduler.py      #   排程驗證工具 (新增)
```

---

## 🛠️ 事前準備

### 1. Python 環境

- 安裝 Python 3.8 或更高版本。

### ⚙️ 環境設定 (Environmental Variables)

本專案使用 `.env` 檔案管理敏感資訊。請參考以下步驟進行設定：

1. 複製範本檔案：

    ```bash
    cp .env.example .env
    ```

2. 編輯 `.env` 並填入您的憑證：
    - `DISCORD_BOT_TOKEN`: 您的 Discord Bot Token。
    - `OWNER_ID`: 您的 Discord 使用者 ID。
    - `APIFY_TOKEN`: 使用新聞功能所需的 Apify Token。
    - `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`: 無頭模式所需的 AI API Key。

> [!IMPORTANT]
> 請務必不要將 `.env` 或 `config.json` 上傳至 GitHub。專案已具備 `.gitignore` 預防此類情況。

---

### 📦 安裝依賴 (Installation)

  ```bash
  pip install -r requirements.txt
  ```

### 2. Google Workspace CLI (gws)

本專案整合了 Google 官方的 `gws` 工具來操作 Gmail 與 Google Calendar。

1. **安裝 gws：**

   ```bash
   npm install -g @googleworkspace/cli
   ```

2. **設定憑證：**

   - 執行 `gws auth setup` 並依照指示在 Google Cloud 建立專案。
   - 執行 `gws auth login` 完成帳號授權。
   - 執行 `gws drive files list` 確保連線正常。

### 3. 環境變數設定 (.env)

本專案所有的機密資訊（API Tokens, 憑證）現在統一管理於根目錄的 `.env` 檔案中。請參考 `.env.example` 建立您的環境設定：

```env
# --- Core Discord Configuration ---
DISCORD_BOT_TOKEN=您的_BOT_TOKEN
OWNER_ID=您的_DISCORD_USER_ID

# --- External Services ---
APIFY_TOKEN=您的_APIFY_TOKEN

# --- LLM API Keys (Phase 2 無頭模式) ---
# 填寫其中一個即可脫離瀏覽器運行
ANTHROPIC_API_KEY=您的_CLAUDE_KEY
OPENAI_API_KEY=您的_OPENAI_KEY
GEMINI_API_KEY=您的_GEMINI_KEY
```

### 4. Discord Bot 配置

1. 前往 [Discord Developer Portal](https://discord.com/developers/applications)。
2. 建立 Application，在 **Bot** 選項中取得 `bot_token`。
3. **重要**：開啟所有 **Privileged Gateway Intents**：
   - `PRESENCE INTENT`
   - `SERVER MEMBERS INTENT`
   - `MESSAGE CONTENT INTENT`
4. 將機器人邀請至伺服器（需「發送訊息」、「嵌入連結」等權限）。

### 5. 開啟遠端除錯 (Remote Debugging)

橋樑透過 Chrome DevTools Protocol (CDP) 與 AI 介面溝通：

- **VS Code 使用者**：確保以 `--remote-debugging-port=9222` 啟動。
- **網頁版使用者**：

  ```bash
  chrome.exe --remote-debugging-port=9222
  ```

### 6. MCP Server 設定 (Antigravity AI)

在 Antigravity 的 MCP 設定中加入 `discord-sender`：

```json
{
  "mcpServers": {
    "discord-sender": {
      "command": "npx",
      "args": ["-y", "@erwin6660/mcp-discord-sender"],
      "env": {
        "DISCORD_BOT_TOKEN": "您的_BOT_TOKEN"
      }
    }
  }
}
```

> [!IMPORTANT]
> 請在 Antigravity 設定中將 `discord-sender` 工具加入 **Auto-run 白名單**，讓 AI 能直接回覆而不需每次詢問。

---

## ⚙️ 設定管理

本專案支援雙重設定模式，**優先讀取 `.env`**：

1. **建議方式**：將所有 Token 填入 `.env`（如上所述）。本專案已支援以 **UTF-8** 編碼讀取 `.env`，可安全使用中文備註或特殊字元。
2. **舊版相容**：若無 `.env` 設定，仍會讀取 `config.json` 的 `bot_token` 與 `owner_id`。

---

## 🤖 Antigravity 技能系統 (Skills)

本專案包含預設的 AI 技能定義，讓 Antigravity 能更聰明地執行任務。

### 🖥️ 電腦控制技能 (Computer Control)

位於 `.antigravity/skills/computer-control/`。此技能賦予 AI 操作您電腦 UI 的能力。

**核心功能：**

- **視覺觀測**：截圖並分析目前畫面內容。
- **滑鼠操作**：精確點擊按鈕、拖曳檔案。
- **鍵盤操作**：在任何視窗輸入文字或按下組合鍵。

**設定方式：**

1. 確保已安裝 `computer-control` MCP 伺服器。
2. 在 Antigravity 的 MCP 設定中加入：

```json
{
  "mcpServers": {
    "computer-control": {
      "command": "npx",
      "args": ["-y", "@erwin6660/mcp-computer-control"]
    }
  }
}
```

**使用範例：**

- 「幫我打開 Chrome 並搜尋今天的科技新聞。」
- 「幫我把目前的程式碼執行結果截圖發送到 Discord。」

### 🏰 專業生產級技能 (Production-Grade Skills)

除了電腦控制外，我還幫您從 `claude-code-production-grade-plugin` 匯入了 **14 個專業 Agent 技能**。

**包含的專業角色：**

- **Orchestrator**: 路由與閘道管理。
- **Software/Frontend Engineer**: 進階程式碼編寫與 UI 實作。
- **Solution Architect**: 系統架構設計。
- **QA / Security Engineer**: 自動化測試與安全審查。
- **DevOps / SRE**: 部署與系統穩定性維護。
- **Product Manager**: 產品定義與需求管理。

這些技能現在都位於您的 `.antigravity/skills/` 目錄中。

## 🏗️ 生產級解耦與無頭架構 (Phase 1 & 2)

本專案已進化為**分散式、非阻塞架構**。透過 API 化 (Headless)，您可以不需要開啟 VS Code 視窗也能 24 小時執行 AI 任務。

### 1. 啟動資料庫與隊列 (Redis)

請確保 Docker 已開啟，並執行：

```powershell
docker run --name lazy-redis -p 6379:6379 -d redis
```

### 2. 啟動任務執行器 (Worker)

在第一個終端機執行：

```powershell
python worker.py
```

*Worker 會偵測 `.env`：*

- **有 API Key**：啟動 **API Mode (Headless)**，直接運算並回傳。
- **無 API Key**：自動回退至 **CDP Mode**，尋找本地瀏覽器注入。

### 3. 啟動機器人 (Bot)

在第二個終端機執行：

```powershell
python main.py
```

---

## 🚀 啟動方式

1. 確保 Antigravity 面板或 VS Code 已開啟。
2. 執行：

   ```bash
   python main.py
   ```

3. 看到 `✅ 橋樑啟動成功！（雙向模式）` 即代表已進入監聽狀態。

---

## 🎮 使用方式

### 🔹 自動轉傳 (Auto-Relay)

在 Discord 輸入**非 `/` 開頭**的文字，機器人會自動轉傳給 Antigravity AI。

### 🔹 斜線指令

| 指令 | 說明 |
|------|------|
| `/ask <內容>` | 明確向 AI 發問 |
| `/briefing` | 手動觸發晨報（Gmail + 日曆 + 趨勢新聞） |
| `/list_tasks` | 列出目前所有的排程任務 |
| `/add_task` | 新增一個排程任務 |
| `/edit_task` | 修改現有的排程任務 |
| `/toggle_task` | 切換排程任務的啟用/停用狀態 |
| `/delete_task` | 刪除一個排程任務 |
| `/tabs` | 列出瀏覽器/IDE 中所有可連線分頁 |
| `/dump` | 診斷分頁狀態 |
| `/screenshot` | 擷取 AI 介面截圖 |
| `/screen` | 取得螢幕解析度 |
| `/type <文字>` | 模仿鍵盤輸入 |
| `!reload_tasks` | (Owner) 已升級為資料庫模式，僅留作相容性提示 |

### 🔹 動態排程任務 (Dynamic Scheduler)

本專案支援**無需修改程式碼**即可自訂的排程系統。

#### 1. 資料庫驅動管理

現在您可以直接在 Discord 使用 `/add_task`、`/toggle_task` 等指令來動態管理排程，所有變更將即時儲存至 `scheduler_history.sqlite` 並於下一分鐘生效，無需觸碰 JSON 檔案。

#### 2. 執行紀錄

所有任務的執行狀態（成功/失敗、時間、錯誤訊息）皆會儲存於資料庫中，可透過 Discord 查詢歷史狀態。

#### 3. 手動觸發

- 管理員仍可使用 `!reload_tasks`，但系統現在已具備自動偵測資料庫變更的能力。

### 🔹 每日晨報排程

- **觸發時間**：每天上午 **10:30** 自動執行。
- **報告內容**：
  - 📧 最新 3 封未讀 Gmail 郵件
  - ⏰ 今日 Google Calendar 行程
  - 📌 Apify AI 爬蟲趨勢新聞（3 則）
- 自動發布至指定 Discord 頻道。

---

## 🔧 診斷工具

若遇到連線問題，可執行環境診斷：

```bash
python scripts/diagnose.py
```

將依序檢查：CDP 端口連線 → 分頁列表 → Antigravity 面板 → 輸入框偵測。

---

## 📐 架構說明

```
Discord 使用者
     │
     ▼
[Discord Bot]  ──(bot/events.py)──  自動轉傳 / 指令解析
     │
     ▼
[CDP 注入層]   ──(core/cdp.py)───  WebSocket → JS 注入
     │
     ▼
[Antigravity AI]
     │
     ▼
[MCP discord-sender]  ──────────  AI 直接回覆至 Discord
```

---

## ⚠️ 常見問答

**Q: 出現「❌ 找不到輸入框」？**

- 請確認 VS Code 中的 Antigravity 面板已開啟且未被最小化。

**Q: 出現「❌ 取得分頁失敗 (Port 9222)」？**

- 請確認瀏覽器或 VS Code 已以 `--remote-debugging-port=9222` 啟動。可訪問 `http://127.0.0.1:9222/json` 確認。

**Q: 訊息傳送成功但 AI 沒有回覆？**

- 請確認 AI 端已配置 `discord-sender` MCP 工具，或檢查 AI 是否正在進行其他處理。
