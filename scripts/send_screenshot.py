import os
import sys
import requests
import json
import glob

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.config import get_bot_token, BRIEFING_CHANNEL_ID

def send_latest_screenshot():
    token = get_bot_token()
    channel_id = BRIEFING_CHANNEL_ID
    
    # 找尋最新的截圖
    downloads_dir = r"C:\Users\USER\Downloads"
    files = glob.glob(os.path.join(downloads_dir, "screenshot_*.png"))
    
    if not files:
        print("❌ 找不到任何截圖檔案")
        return
        
    latest_screenshot = max(files, key=os.path.getctime)
    print(f"找到最新截圖: {latest_screenshot}")
    
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {token}"
    }
    
    print("正在上傳圖片至 Discord...")
    try:
        with open(latest_screenshot, "rb") as f:
            files_data = {
                "file": ("screenshot.png", f, "image/png")
            }
            payload = {
                "payload_json": json.dumps({
                    "content": "✅ **真正的截圖來了！**\n這是剛才擷取的 Antigravity 與 VS Code 畫面："
                })
            }
            
            response = requests.post(url, headers=headers, data=payload, files=files_data)
            
            if response.status_code == 200:
                print("✅ 截圖上傳成功！")
            else:
                print(f"❌ 上傳失敗: HTTP {response.status_code}")
                print(response.text)
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")

if __name__ == "__main__":
    send_latest_screenshot()
