import subprocess
import os
import sys
from core.config import log

# 取得 Toonify 相關路徑
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOONIFY_DIR = os.path.join(BASE_DIR, "external", "toonify-mcp")
BRIDGE_JS = os.path.join(TOONIFY_DIR, "dist", "bridge.js")

def optimize_text(text: str) -> str:
    """
    呼叫 Toonify MCP 的核心邏輯進行 Token 優化。
    若優化失敗或未安裝，則回傳原字串。
    """
    if not os.path.exists(BRIDGE_JS):
        # log("⚠️ Toonify bridge.js 不存在，略過優化。")
        return text

    try:
        # 使用 node 執行 bridge.js，並透過 stdin 傳入文本
        process = subprocess.Popen(
            ["node", BRIDGE_JS],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            cwd=TOONIFY_DIR
        )
        stdout, stderr = process.communicate(input=text, timeout=5)
        
        if process.returncode == 0:
            return stdout
        else:
            log(f"❌ Toonify 優化出錯: {stderr}")
            return text
    except Exception as e:
        log(f"❌ 執行 Toonify 失敗: {e}")
        return text

if __name__ == "__main__":
    # 測試用
    test_json = '{"test": "hello world", "data": [1, 2, 3, 4, 5]}'
    optimized = optimize_text(test_json)
    print(f"Original length: {len(test_json)}")
    print(f"Optimized length: {len(optimized)}")
    print(f"Result: {optimized}")
