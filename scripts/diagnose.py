"""
LazyBridge 快速診斷工具
執行方式: python -m scripts.diagnose  或  python scripts/diagnose.py
"""
import json
import sys
import os

# 確保可以匯入專案模組
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

PASS = "✅"
FAIL = "❌"
WARN = "⚠️"


def check_cdp():
    print("=" * 50)
    print("LazyBridge 環境診斷")
    print("=" * 50)
    print()

    # 1. 檢查 CDP 連線
    print("[1] 檢查 CDP 調試端口 9222...")
    try:
        resp = requests.get("http://127.0.0.1:9222/json", timeout=3)
        tabs = resp.json()
        print(f"{PASS} CDP 端口 9222 正常，找到 {len(tabs)} 個分頁")
    except requests.exceptions.ConnectionError:
        print(f"{FAIL} 無法連線到 127.0.0.1:9222")
        print()
        print("  解決方法：請以除錯模式啟動 VS Code：")
        print("  方法A: 執行  start_vscode_debug.bat")
        print("  方法B: 在命令提示字元執行:")
        print("         code --remote-debugging-port=9222")
        print()
        print("  ⚠️ 注意：若 VS Code 已開啟，需完全關閉後再以上述方式重新啟動")
        return False
    except Exception as e:
        print(f"{FAIL} 連線錯誤: {e}")
        return False

    # 2. 列出所有分頁
    print()
    print("[2] 分頁列表：")
    pages = [t for t in tabs if t.get("type") == "page"]
    if not pages:
        print(f"{FAIL} 沒有找到任何 page 類型的分頁")
        return False

    for i, t in enumerate(pages):
        title = t.get("title", "(無標題)")
        url = t.get("url", "")[:60]
        print(f"  [{i+1}] {title[:50]}")
        print(f"       {url}")

    # 3. 找聊天分頁
    print()
    print("[3] 尋找 Antigravity 聊天分頁...")
    chat_tab = None
    for t in pages:
        title = t.get("title", "")
        if ("Scratchpad" in title or "Antigravity" in title) and "Launchpad" not in title:
            chat_tab = t
            break
    if not chat_tab and pages:
        chat_tab = pages[0]
        print(f"{WARN} 未找到明確的 Antigravity 分頁，使用第一個分頁：{chat_tab['title']}")
    else:
        print(f"{PASS} 找到目標分頁：{chat_tab['title']}")

    # 4. 測試 WebSocket 連線 + 輸入框偵測
    print()
    print("[4] 測試 WebSocket 連線與輸入框偵測...")
    try:
        import asyncio
        import websockets

        async def check_input():
            ws_url = chat_tab["webSocketDebuggerUrl"]
            async with websockets.connect(ws_url) as ws:
                js = """
                (function() {
                    const findInRoot = (root) => {
                        for (let e of root.querySelectorAll('textarea:not([disabled]):not([readonly])')) return e;
                        for (let e of root.querySelectorAll('[role="textbox"]')) return e;
                        for (let e of root.querySelectorAll('[contenteditable="true"]')) return e;
                        for (let e of root.querySelectorAll('*')) {
                            if (e.shadowRoot) {
                                const r = findInRoot(e.shadowRoot);
                                if (r) return r;
                            }
                        }
                        return null;
                    };
                    const input = findInRoot(document);
                    if (!input) return 'NOT_FOUND';
                    const ph = input.getAttribute('placeholder') || input.getAttribute('aria-label') || '';
                    return input.tagName + (ph ? '[' + ph.slice(0, 40) + ']' : '');
                })()
                """
                msg = {
                    "id": 1,
                    "method": "Runtime.evaluate",
                    "params": {"expression": js, "returnByValue": True},
                }
                await ws.send(json.dumps(msg))
                for _ in range(30):
                    raw = await ws.recv()
                    res = json.loads(raw)
                    if res.get("id") == 1:
                        return res.get("result", {}).get("result", {}).get("value")
            return None

        result = asyncio.run(check_input())
        if result and result != "NOT_FOUND":
            print(f"{PASS} 找到輸入框: {result}")
        elif result == "NOT_FOUND":
            print(f"{FAIL} 找不到輸入框！")
            print("  可能原因：")
            print("  - Antigravity 面板尚未載入完成，請稍候後再試")
            print("  - 請確認 Antigravity 聊天視窗在 VS Code 中是開啟狀態")
        else:
            print(f"{WARN} 輸入框偵測超時（result=None）")

    except Exception as e:
        print(f"{FAIL} WebSocket 連線失敗: {e}")
        return False

    print()
    print("=" * 50)
    print("診斷完成")
    print("=" * 50)
    return True


if __name__ == "__main__":
    check_cdp()
