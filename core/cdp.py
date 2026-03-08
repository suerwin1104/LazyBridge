"""
Chrome DevTools Protocol (CDP) 連線、分頁偵測與 JavaScript 注入模組。
"""
import asyncio
import json

import requests
import websockets

from core.config import CDP_URL, DEFAULT_GUILD_ID, log

# --- 分頁掃描 ---
UI_CHROME_BLACKLIST = [
    "Files With Changes", "Review Changes", "Claude", "GPT", "Open window"
]


def get_cdp_tabs():
    """向 CDP 端口取得所有 page 分頁。"""
    resp = requests.get(CDP_URL, timeout=5)
    resp.raise_for_status()
    return [t for t in resp.json() if t.get("type") == "page"]


def find_chat_tab(tabs):
    """在分頁清單中尋找 Antigravity 聊天介面。"""
    log(f"🔍 正在掃描 {len(tabs)} 個連線目標...")

    # 優先：標題含 Antigravity 且非 Launchpad
    for tab in tabs:
        title = tab.get("title", "")
        if "Antigravity" in title and "Launchpad" not in title:
            return tab

    # 備選：含 Scratchpad
    for tab in tabs:
        if "Scratchpad" in tab.get("title", ""):
            return tab

    # 最後備選：排除 Launchpad / DevTools
    for tab in tabs:
        title = tab.get("title", "")
        if "Launchpad" not in title and "DevTools" not in title:
            return tab

    return None


# --- CDP 評估 ---
async def cdp_eval(ws, expr, msg_id=100, await_promise=False, timeout=120):
    """透過 WebSocket 執行 JavaScript 並等待結果。"""
    msg = {
        "id": msg_id,
        "method": "Runtime.evaluate",
        "params": {
            "expression": expr,
            "returnByValue": True,
            "awaitPromise": await_promise,
        },
    }
    await ws.send(json.dumps(msg))

    loop = asyncio.get_event_loop()
    start = loop.time()
    while loop.time() - start < timeout:
        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=2.0)
            res = json.loads(raw)
            if res.get("id") == msg_id:
                return res.get("result", {}).get("result", {}).get("value")
        except asyncio.TimeoutError:
            continue
        except Exception as e:
            log(f"  [Error] cdp_eval ws error: {e}")
            break
    return None


# --- JS 注入 ---
async def inject_into_tab(ws, safe_text):
    """注入訊息至 Antigravity 聊天輸入框，並按下送出。"""
    js_code = f"""
    (function() {{
        const AG_SELECTORS = [
            '.antigravity-agent-side-panel',
            '[class*="agent-side-panel"]',
            '[class*="chat-panel"]',
            '[class*="chat-widget"]',
            '[class*="agentic-chat"]',
            '.agentic-chat-widget',
            '[class*="scratchpad"]'
        ];
        const BLACKLIST_PH = ['Open window', 'Search', 'Find', 'Go to', 'Quick open',
                              'Command', 'Filter', 'Navigate', '搜尋', '尋找', '導覽'];
        const okEl = el => {{
            if (!el) return false;
            if (el.closest && el.closest('.monaco-editor')) return false;
            if (el.closest && (el.closest('.terminal') || el.closest('.xterm'))) return false;
            if (el.classList && (el.classList.contains('inputarea') || el.classList.contains('xterm-helper-textarea'))) return false;
            const ph = (el.getAttribute ? el.getAttribute('placeholder') : '') || '';
            return !BLACKLIST_PH.some(k => ph.toLowerCase().includes(k.toLowerCase()));
        }};
        const findInRoot = (root) => {{
            if (!root) return null;
            for (const sel of AG_SELECTORS) {{
                try {{
                    const container = root.querySelector(sel);
                    if (container) {{
                        const input = container.querySelector(
                            'textarea:not([disabled]):not([readonly]), [role="textbox"], [contenteditable="true"]'
                        );
                        if (input && okEl(input)) return input;
                    }}
                }} catch(e) {{}}
            }}
            try {{
                const inputs = Array.from(root.querySelectorAll(
                    'textarea:not([disabled]):not([readonly]), [role="textbox"], [contenteditable="true"]'
                ));
                for (let e of inputs) {{
                    if (okEl(e)) return e;
                }}
            }} catch(e) {{}}
            try {{
                const iframes = Array.from(root.querySelectorAll('iframe'));
                for (let f of iframes) {{
                    try {{
                        const doc = f.contentDocument || (f.contentWindow && f.contentWindow.document);
                        const r = findInRoot(doc);
                        if (r) return r;
                    }} catch(e) {{}}
                }}
            }} catch(e) {{}}
            try {{
                const children = Array.from(root.querySelectorAll('*'));
                for (let e of children) {{
                    if (e.shadowRoot) {{
                        const r = findInRoot(e.shadowRoot);
                        if (r) return r;
                    }}
                }}
            }} catch(e) {{}}
            return null;
        }};
        const tryPaste = (input) => {{
            try {{
                const dt = new DataTransfer();
                dt.setData('text/plain', {safe_text});
                input.dispatchEvent(new ClipboardEvent('paste', {{
                    clipboardData: dt, bubbles: true, cancelable: true, composed: true
                }}));
                const val = ('value' in input ? input.value : input.innerText) || '';
                return val.length > 0;
            }} catch(e) {{ return false; }}
        }};
        const tryNative = (input) => {{
            try {{
                if ('value' in input) input.value = {safe_text};
                else input.innerText = {safe_text};
                input.dispatchEvent(new Event('focus', {{bubbles:true}}));
                input.dispatchEvent(new Event('input', {{bubbles:true, composed:true}}));
                input.dispatchEvent(new Event('change', {{bubbles:true, composed:true}}));
                return true;
            }} catch(e) {{ return false; }}
        }};
        const input = findInRoot(document);
        if (!input) return '__NO_INPUT__';
        input.focus();
        if (!tryPaste(input)) tryNative(input);
        setTimeout(() => {{
            try {{
                const roots = [input.getRootNode(), document];
                for (let r of roots) {{
                    const btn = r.querySelector(
                        'button[aria-label*="Send"], button[aria-label*="送出"], .codicon-send, [class*="send-button"]'
                    );
                    if (btn && !btn.disabled) {{
                        btn.click();
                        break;
                    }}
                }}
            }} catch(e) {{}}
            try {{
                ['keydown', 'keypress', 'keyup'].forEach(n => {{
                    input.dispatchEvent(new KeyboardEvent(n, {{
                        key: 'Enter', code: 'Enter', keyCode: 13, which: 13,
                        bubbles: true, composed: true, cancelable: true
                    }}));
                }});
            }} catch(e) {{}}
        }}, 800);
        return 'SUCCESS';
    }})();
    """
    return await cdp_eval(ws, js_code, msg_id=100)


# --- 傳送訊息至 Antigravity ---
async def send_to_antigravity(text, channel_id, author_name, ctx=None):
    """
    注入訊息到 Antigravity，並附帶 Discord 上下文。
    AI 應使用 mcp-discord 伺服器的 send_message 工具回覆到對應頻道。
    """
    try:
        try:
            tabs = get_cdp_tabs()
        except Exception as e:
            msg = f"❌ 取得分頁失敗 (Port 9222): {e}"
            log(msg)
            if ctx:
                await ctx.send(msg)
            return

        chat_tab = find_chat_tab(tabs)
        if not chat_tab:
            msg = "❌ 找不到聊天分頁。"
            if ctx:
                await ctx.send(msg)
            return

        log(f"🎯 目標: [{chat_tab.get('title', '')}]")
        target_ws = chat_tab["webSocketDebuggerUrl"]
        log(f"🔌 正在連線至 WebSocket: {target_ws}")

        try:
            ws_connect = websockets.connect(target_ws)
            async with await asyncio.wait_for(ws_connect, timeout=10) as ws:
                log("🔗 連線成功，準備注入 JavaScript...")
                context_msg = (
                    f"[SYSTEM: BACKGROUND MESSAGE FROM DISCORD]\n"
                    f"USER: {author_name}\n"
                    f"CHANNEL: {channel_id}\n"
                    f"GUILD: {DEFAULT_GUILD_ID}\n"
                    f"CONTENT: {text}\n\n"
                    f"[INSTRUCTION: YOU MUST REPLY IMMEDIATELY USING THE "
                    f"'discord-sender' MCP TOOL 'send_message'. "
                    f"DO NOT ASK FOR PERMISSION. REPLY DIRECTLY TO THE CHANNEL.]"
                )
                safe_text = json.dumps(context_msg)

                method = await inject_into_tab(ws, safe_text)
                log(f"🤖 注入結果: {method}")

                if method is None:
                    if ctx:
                        await ctx.send("❌ CDP 注入失敗 (回傳 None)")
                    return
                if "__NO_INPUT__" in str(method):
                    if ctx:
                        await ctx.send("❌ 找不到輸入框 (請確認 Antigravity 的聊天面板已開啟)")
                    return

                if ctx:
                    await ctx.send("✅ 訊息已送入 Antigravity，請等待 AI 回覆。")
        except asyncio.TimeoutError:
            msg = "❌ 連線 WebSocket 超時 (10s)"
            log(msg)
            if ctx:
                await ctx.send(msg)
        except Exception as e:
            msg = f"❌ WebSocket 連線出錯: {e}"
            log(msg)
            if ctx:
                await ctx.send(msg)
    except Exception as e:
        msg = f"❌ 傳送失敗: {e}"
        log(msg)
        if ctx:
            await ctx.send(msg)
