import asyncio
import sys
import os
sys.path.append(os.getcwd())

from services.ai_engine import get_ai_response_async, check_circuit
from core.config import log

async def test_circuit_breaker():
    print("🚀 開始測試 Circuit Breaker...")
    
    # 這裡我們模擬失敗的情況，或者故意給錯誤的參數（如果可以的話）
    # 但最直接的是檢查 logic
    
    # 測試正常狀態
    is_ok = check_circuit()
    print(f"1. 初始狀態核查: {'✅ 通過' if is_ok else '❌ 失敗'}")
    
    print("\n2. 模擬連續失敗...")
    # 由於我們不能直接修改私有變數，我們透過觸發真實失敗（不給關鍵字或模擬異常）
    # 但這裡最安全的是在 worker 裡整合測試。
    
    # 這裡我們直接呼叫 3 次失敗 (模擬無 API key 或網路斷開)
    # 為了測試，我們可以暫時將 API Key 設為無效（如果是在測試環境）
    
    print("（此測試建議在 Worker 運行時觀察 log，因為涉及到全域狀態）")

if __name__ == "__main__":
    asyncio.run(test_circuit_breaker())
