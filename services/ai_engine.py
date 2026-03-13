"""
AI 引擎模組 (Phase 2)。
直接透過 API 與 LLM (Claude/GPT/Gemini) 互動，不再依賴瀏覽器 CDP 注入。
"""
import os
import time
from core.config import ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, log

# Circuit Breaker State
FAILURE_THRESHOLD = 3
CIRCUIT_OPEN_DURATION = 300 # 5 minutes
_consecutive_failures = 0
_circuit_open_until = 0

def check_circuit():
    """Returns True if the circuit is CLOSED (ok to proceed)."""
    global _consecutive_failures, _circuit_open_until
    if _circuit_open_until > time.time():
        return False
    return True

# 我們這裡優先使用 Anthropic (Claude 3.5 Sonnet) 作為核心引擎
# 若您偏好 OpenAI 或 Gemini，可以在此切換優先順序

def get_ai_response(prompt, system_prompt="You are a helpful assistant."):
    """透過 API 取得 AI 回覆與 Token 使用量。"""
    
    # 預設回傳格式
    result = {"text": "", "tokens": 0, "model_name": "unknown"}

    if ANTHROPIC_API_KEY:
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=ANTHROPIC_API_KEY)
            message = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=4000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            result["text"] = message.content[0].text
            result["tokens"] = message.usage.input_tokens + message.usage.output_tokens
            result["model_name"] = "claude-3-5-sonnet"
            return result
        except Exception as e:
            log(f"❌ Anthropic API 呼叫失敗: {e}")
            result["text"] = f"Error: {e}"
            return result

    elif OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            result["text"] = response.choices[0].message.content
            result["tokens"] = response.usage.total_tokens
            result["model_name"] = "gpt-4o"
            return result
        except Exception as e:
            log(f"❌ OpenAI API 呼叫失敗: {e}")
            result["text"] = f"Error: {e}"
            return result
            
    elif GEMINI_API_KEY:
        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=GEMINI_API_KEY)
            
            # Using the new google.genai SDK syntax
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt
                ),
                contents=prompt
            )
            
            result["text"] = response.text
            # token counts are directly available in response.usage_metadata
            try:
                result["tokens"] = response.usage_metadata.total_token_count
            except:
                result["tokens"] = (len(prompt) + len(response.text)) // 4
            result["model_name"] = "gemini-1.5-flash"
            return result
        except Exception as e:
            log(f"❌ Gemini API 呼叫失敗: {e}")
            result["text"] = f"Error: {e}"
            return result
    else:
        log("⚠️ 未偵測到 API Key")
        result["text"] = "❌ 尚未設定 AI API Key"
        return result

async def get_ai_response_async(prompt, system_prompt=None):
    """非同步版本的 AI 回覆 (適用於 Worker)，具備斷路器 (Circuit Breaker) 保護。"""
    global _consecutive_failures, _circuit_open_until
    
    if system_prompt is None:
        from core.config import get_soul_content
        system_prompt = get_soul_content()
    
    if not check_circuit():
        wait_time = int(_circuit_open_until - time.time())
        log(f"🔌 [CircuitBreaker] 斷路器已開啟 (OPEN)。跳過請求。剩餘冷卻時間: {wait_time}s。")
        return {"text": f"[CircuitBreaker] 系統進入保護模式。請於 {wait_time} 秒後再試。", "tokens": 0}

    import asyncio
    try:
        # 使用 asyncio.to_thread 執行同步的 API 呼叫
        result = await asyncio.to_thread(get_ai_response, prompt, system_prompt)
        
        # 成功則重置連續失敗計數
        _consecutive_failures = 0
        return result
    except Exception as e:
        _consecutive_failures += 1
        log(f"💥 [CircuitBreaker] API 呼叫失敗 ({_consecutive_failures}/{FAILURE_THRESHOLD}): {e}")
        
        if _consecutive_failures >= FAILURE_THRESHOLD:
            _circuit_open_until = time.time() + CIRCUIT_OPEN_DURATION
            log(f"🚨 [CircuitBreaker] 達到失敗閾值。開啟斷路器 {CIRCUIT_OPEN_DURATION}s。")
            
        return {"text": f"❌ Error (Failures: {_consecutive_failures}): {e}", "tokens": 0}
