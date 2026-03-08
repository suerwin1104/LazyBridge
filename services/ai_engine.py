"""
AI 引擎模組 (Phase 2)。
直接透過 API 與 LLM (Claude/GPT/Gemini) 互動，不再依賴瀏覽器 CDP 注入。
"""
import os
from core.config import ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, log

# 我們這裡優先使用 Anthropic (Claude 3.5 Sonnet) 作為核心引擎
# 若您偏好 OpenAI 或 Gemini，可以在此切換優先順序

def get_ai_response(prompt, system_prompt="You are a helpful assistant."):
    """透過 API 取得 AI 回覆。"""
    
    # 目前優先順序: Anthropic -> OpenAI 
    # Gemini 支援已加入，但預設需要調整順序或特別指定才能啟用
    
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
            return message.content[0].text
        except Exception as e:
            log(f"❌ Anthropic API 呼叫失敗: {e}")
            return f"Error: {e}"

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
            return response.choices[0].message.content
        except Exception as e:
            log(f"❌ OpenAI API 呼叫失敗: {e}")
            return f"Error: {e}"
            
    # --- Gemini 支援 (預設未啟用/順位較低) ---
    elif GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            
            # 使用 Gemini 1.5 Flash (速度快、成本低)
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=system_prompt
            )
            
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            log(f"❌ Gemini API 呼叫失敗: {e}")
            return f"Error: {e}"
            
    else:
        log("⚠️ 未偵測到 API Key (ANTHROPIC_API_KEY 或 OPENAI_API_KEY 或 GEMINI_API_KEY)")
        return "❌ 尚未設定 AI API Key，請檢查 .env 檔案。"

async def get_ai_response_async(prompt, system_prompt="You are a helpful assistant."):
    """非同步版本的 AI 回覆 (適用於 Worker)。"""
    import asyncio
    # 這裡簡單包裹同步調用為 thread，實際生產環境建議用 httpx/non-blocking SDK
    return await asyncio.to_thread(get_ai_response, prompt, system_prompt)
