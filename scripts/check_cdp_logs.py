from core.config import log

with open('bot.log', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()
    # Looking for recent CDP activity and errors
    relevant = []
    for line in lines[-200:]:
        if any(k in line for k in ["CDP", "偵測到分頁", "WebSocket", "注入", "❌", "⚠️", "✅", "🎨", "簡報"]):
            relevant.append(line.strip())
    
    for r in relevant:
        print(r[:300])
