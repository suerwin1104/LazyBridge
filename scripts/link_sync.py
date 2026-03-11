import subprocess
import re
import os
import time
import requests
import sys

# 載入環境變數
def load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip(' "\'')

load_env()

CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
CF_KV_NAMESPACE_ID = os.getenv("CF_KV_NAMESPACE_ID")
CF_API_TOKEN = os.getenv("CF_API_TOKEN")
REPORTS_PORT = 8080

def update_cloudflare_kv(url):
    """將網址推送到 Cloudflare KV"""
    if not all([CF_ACCOUNT_ID, CF_KV_NAMESPACE_ID, CF_API_TOKEN]):
        print("⚠️ 缺少 Cloudflare 設定，跳過同步。請檢查 .env 檔案。")
        return False

    api_url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/storage/kv/namespaces/{CF_KV_NAMESPACE_ID}/values/current_url"
    
    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "text/plain"
    }

    try:
        response = requests.put(api_url, data=url, headers=headers)
        if response.status_code == 200:
            print(f"✅ 成功同步至 Cloudflare: {url}")
            return True
        else:
            print(f"❌ 同步失敗: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 同步發生錯誤: {e}")
        return False

def start_tunnel():
    """啟動 localtunnel 並監控網址"""
    print(f"🚀 啟動 LocalTunnel (Port {REPORTS_PORT})...")
    
    # 啟動 lt 子程序
    process = subprocess.Popen(
        ["lt", "--port", str(REPORTS_PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    url_found = False
    
    try:
        for line in process.stdout:
            print(f"[LT] {line.strip()}")
            # 搜尋網址模式
            match = re.search(r'your url is: (https://[a-zA-Z0-9\-\.]+)', line)
            if match:
                current_url = match.group(1)
                print(f"✨ 偵測到新網址: {current_url}")
                update_cloudflare_kv(current_url)
                url_found = True
                
            if process.poll() is not None:
                break
    except KeyboardInterrupt:
        print("\n👋 停止隧道服務...")
        process.terminate()

if __name__ == "__main__":
    # 檢查是否安裝 lt
    try:
        subprocess.run(["lt", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("❌ 錯誤: 找不到 'lt' 指令。請先安裝: npm install -g localtunnel")
        sys.exit(1)

    start_tunnel()
