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
│   └── cdp.py                 #   CDP 連線、分頁掃描、JS 注入
│
├── bot/                       # Discord Bot 模組
│   ├── commands.py            #   所有斜線指令（Cog）
│   ├── events.py              #   事件處理：on_ready、自動轉傳
│   └── scheduler.py           #   每日晨報排程（Cog）
│
├── services/                  # 外部服務整合
│   ├── google_workspace.py    #   Gmail / Calendar CLI 封裝
│   ├── apify_news.py          #   Apify 趨勢新聞抓取
│   └── briefing.py            #   晨報組裝（GWS + Apify）
│
└── scripts/                   # 獨立工具腳本
    └── diagnose.py            #   環境診斷工具
```

---

## 🛠️ 事前準備

### 1. Python 環境

- 安裝 Python 3.8 或更高版本。
- 安裝依賴套件：

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

### 3. Apify API (新聞趨勢分析)

本專案使用 Apify 的 `google-search-scraper` 來獲取即時新聞。

- 至 [Apify 官網](https://apify.com/) 註冊並取得 API Token。
- 在 `.env` 中寫入：

  ```env
  APIFY_TOKEN=您的_APIFY_API_TOKEN
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

## ⚙️ 設定檔 (config.json)

```json
{
  "bot_token": "您的_DISCORD_BOT_TOKEN",
  "owner_id": "您的_DISCORD_使用者_ID"
}
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
| `/tabs` | 列出瀏覽器/IDE 中所有可連線分頁 |
| `/dump` | 診斷分頁狀態 |
| `/screenshot` | 擷取 AI 介面截圖 |
| `/screen` | 取得螢幕解析度 |
| `/mouse <x> <y>` | 移動滑鼠 |
| `/click <x> <y>` | 執行點擊 |
| `/type <文字>` | 模仿鍵盤輸入 |

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
