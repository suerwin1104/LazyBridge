import subprocess
import re
import os
import time
import requests
import sys
import threading

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

# 解析服務地圖: "report:8080,hbms:3000"
SERVICE_MAP_STR = os.getenv("MULTI_SERVICE_MAP", "report:8080")
SERVICE_MAP = {}
for item in SERVICE_MAP_STR.split(","):
    if ":" in item:
        name, port = item.split(":", 1)
        SERVICE_MAP[name.strip()] = port.strip()

def update_cloudflare_kv(service_name, url):
    """將網址推送到 Cloudflare KV"""
    if not all([CF_ACCOUNT_ID, CF_KV_NAMESPACE_ID, CF_API_TOKEN]):
        print(f"⚠️ [{service_name}] 缺少 Cloudflare 設定，跳過同步。")
        return False

    # KV Key 格式: link_{service_name}
    kv_key = f"link_{service_name}"
    api_url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/storage/kv/namespaces/{CF_KV_NAMESPACE_ID}/values/{kv_key}"
    
    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "text/plain"
    }

    try:
        response = requests.put(api_url, data=url, headers=headers)
        if response.status_code == 200:
            print(f"✅ [{service_name}] 成功同步至 Cloudflare KV '{kv_key}': {url}")
            return True
        else:
            print(f"❌ [{service_name}] 同步失敗: {response.text}")
            return False
    except Exception as e:
        print(f"❌ [{service_name}] 同步發生錯誤: {e}")
        return False

def run_tunnel(service_name, port):
    """啟動單個服務的隧道 (優先使用 cloudflared)"""
    # 檢查是否有 cloudflared
    has_cf = False
    cf_cmd = "cloudflared"
    
    # 嘗試直接執行或檢查常見 Windows 路徑
    try:
        res = subprocess.run(["cloudflared", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=os.name == 'nt')
        if res.returncode == 0:
            has_cf = True
    except:
        pass
        
    if not has_cf:
        # 檢查常見安裝路徑 (例如: C:\Program Files (x86)\cloudflared\cloudflared.exe)
        common_paths = [
            os.path.expandvars(r"%ProgramFiles%\cloudflared\cloudflared.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\cloudflared\cloudflared.exe"),
            r"C:\bin\cloudflared.exe"
        ]
        for path in common_paths:
            if os.path.exists(path):
                cf_cmd = path
                has_cf = True
                break

    if has_cf:
        print(f"🚀 [{service_name}] 啟動 Cloudflare Tunnel (Port {port})...")
        process = subprocess.Popen(
            [cf_cmd, "tunnel", "--url", f"http://localhost:{port}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, 
            text=True,
            bufsize=1,
            universal_newlines=True,
            shell=os.name == 'nt'
        )
        output_source = process.stdout
    else:
        print(f"🚀 [{service_name}] 啟動 LocalTunnel (Port {port})...")
        process = subprocess.Popen(
            ["lt", "--port", str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            shell=os.name == 'nt'
        )
        output_source = process.stdout

    try:
        for line in iter(output_source.readline, ''):
            if not line:
                break
            
            # 搜尋 Cloudflare 網址
            cf_match = re.search(r'https://[a-zA-Z0-9\-\.]+\.trycloudflare\.com', line)
            if cf_match:
                current_url = cf_match.group(0)
                print(f"✨ [{service_name}] 偵測到 CF 網址: {current_url}")
                update_cloudflare_kv(service_name, current_url)
            
            # 搜尋 LocalTunnel 網址
            lt_match = re.search(r'your url is: (https://[a-zA-Z0-9\-\.]+)', line)
            if lt_match:
                current_url = lt_match.group(1)
                print(f"✨ [{service_name}] 偵測到 LT 網址: {current_url}")
                update_cloudflare_kv(service_name, current_url)
                
            if process.poll() is not None:
                break
    except Exception as e:
        print(f"⚠️ [{service_name}] 隧道中斷: {e}")
    finally:
        process.terminate()

def main():
    if not SERVICE_MAP:
        print("❌ 錯誤: MULTI_SERVICE_MAP 格式不正確或為空。")
        return

    # 檢查是否安裝必要的工具
    has_any = False
    for tool in ["cloudflared", "lt"]:
        try:
            subprocess.run([tool, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=os.name == 'nt')
            has_any = True
        except:
            continue
    
    if not has_any:
        print("❌ 錯誤: 找不到 'cloudflared' 或 'lt' 指令。")
        print("建議安裝 Cloudflare Tunnel: https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.msi")
        sys.exit(1)

    threads = []
    print(f"🌐 準備啟動多服務同步中心: {list(SERVICE_MAP.keys())}")
    
    for name, port in SERVICE_MAP.items():
        t = threading.Thread(target=run_tunnel, args=(name, port), daemon=True)
        t.start()
        threads.append(t)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 停止所有同步服務...")

if __name__ == "__main__":
    main()
