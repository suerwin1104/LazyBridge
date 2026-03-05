# 🚀 LazyBridge - Antigravity AI 橋接器

> [!NOTE]
> 本專案修改自 GitHub 上的 [LazyGravity](https://github.com/tokyoweb3/LazyGravity) 專案。特別感謝原作者提供核心靈感與 CDP 注入技術。

LazyBridge 是一個強大的連通工具，能夠將 Discord 訊息與 VS Code 中的 Antigravity AI (或 Chrome 中的網頁版) 進行雙向串接。您可以直接從 Discord 發送需求，讓 AI 在您的開發環境中執行任務，並將結果回傳至 Discord。

---

## 🛠️ 事前準備

在開始之前，請確保您的環境已具備以下條件：

### 1. Python 環境

- 安裝 Python 3.8 或更高版本。
- 安裝必要的依賴套件：

  ```bash
  pip install discord.py requests websockets
  ```

### 2. Discord Bot 配置

1. 前往 [Discord Developer Portal](https://discord.com/developers/applications)。
2. 建立一個新的 Application，並在 **Bot** 選項中取得您的 `bot_token`。
3. **重要**：在 **Privileged Gateway Intents** 區域，開啟以下項目：
   - `PRESENCE INTENT`
   - `SERVER MEMBERS INTENT`
   - `MESSAGE CONTENT INTENT` (必須開啟，否則無法讀取詳細訊息)
4. 將機器人邀請至您的伺服器（需具備「發送訊息」、「嵌入連結」、「使用斜線指令」等權限）。

### 3. 開啟遠端除錯 (Remote Debugging)

橋樑需要透過 Chrome DevTools Protocol (CDP) 與 AI 介面溝通：

- **VS Code 使用者**：確保您的 VS Code 或是 Antigravity 擴充功能是以開啟 `--remote-debugging-port=9222` 的模式執行。
- **網頁版使用者**：啟動 Chrome 時加入參數：

  ```bash
  chrome.exe --remote-debugging-port=9222
  ```

### 4. MCP Server 設定 (給 Antigravity AI)

為了讓 AI 能夠回覆訊息，您必須在 Antigravity 的 MCP 設定中加入 `discord-sender`：

1. 開啟 Antigravity 的 **MCP 設定** (通常在側邊欄齒輪圖示)。
2. 新增一個 MCP Server 並填入以下資訊 (範例)：

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

3. **重要：開啟自動執行 (Auto-run/SafeToAutoRun)**：
   - 為了讓流程全自動化而不需 AI 每次詢問「我是否可以發送訊息？」，請在 Antigravity 的設定中尋找 **Safe to auto-run** 或 **Auto-approve tools**。
   - 將 `discord-sender` 的相關工具 (如 `send_message`) 加入**白名單**，或在提示詞中強調使用 `SafeToAutoRun: true`。
   - 在 `main.py` 的指令中，我們已加入 `[INSTRUCTION: YOU MUST REPLY IMMEDIATELY...]` 強制 AI 立即回覆。

---

## ⚙️ 設定檔 (config.json)

在專案目錄下建立 `config.json` 檔案：

```json
{
  "bot_token": "您的_DISCORD_BOT_TOKEN",
  "owner_id": "您的_DISCORD_使用者_ID"
}
```

---

## 🚀 啟動方式

1. 確保已開啟具備 Antigravity 的分頁 or VS Code 面板。
2. 執行 `main.py`：

   ```bash
   python main.py
   ```

3. 當看到 `✅ 橋樑啟動成功！（雙向模式）` 時，代表已進入監聽狀態。

---

## 🎮 使用方式

### 🔹 自動轉傳 (Auto-Relay)

在 Discord 頻道中輸入任何**非 `/` 開頭**的文字（例如：`怎麼用 Python 讀取 JSON？`），機器人會自動將訊息轉傳給 Antigravity AI，並回覆「📡 接收並傳送中...」。

### 🔹 斜線指令

- `/ask <內容>`：明確向 AI 發問。
- `/tabs`：列出目前瀏覽器/IDE 中所有可連線的分頁。
- `/dump`：診斷目前的分頁狀態。
- `/screenshot`：擷取 AI 介面的截圖（診斷 UI 選項用）。

### 🔹 互動指令 (診斷用)

- `/screen`：取得遠端機器人的螢幕解析度。
- `/mouse <x> <y>`：移動滑鼠。
- `/click <x> <y>`：執行點擊。
- `/type <文字>`：模仿真人輸入。

---

## 📝 運作原理

1. **Discord 接收端**：監聽 Discord API 傳來的事件。
2. **CDP 注入層**：透過 WebSocket 連線到 `localhost:9222`，動態尋找 Antigravity 的聊天輸入框。
3. **JS 動作模擬**：模擬 `Paste` 事件與 `Enter` 鍵入，將訊息強行餵給 AI。
4. **AI 回信**：此版本的 AI 已配置 MCP (Model Context Protocol) 工具，會直接透過 `discord-sender` 工具回傳訊息到原始頻道。

---

## ⚠️ 常見問答

**Q: 出現「❌ 找不到輸入框」？**

- 請確認 VS Code 中的 Antigravity 面板已經打開，且並未被最小化。

**Q: 出現「❌ 取得分頁失敗 (Port 9222)」？**

- 請確認您的瀏覽器或環境是否真的開啟了 `9222` 埠口。可在瀏覽器開啟 `http://127.0.0.1:9222/json` 確認。

**Q: 訊息傳送成功但 AI 沒有回覆？**

- 請確認 AI 端是否支援 `discord-sender` MCP 工具，或者檢查 AI 是否正在進行複雜處理。
