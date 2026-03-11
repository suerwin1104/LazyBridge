import sys
with open('bot.log', 'r', errors='ignore') as f:
    lines = f.readlines()
    for line in lines[-2000:]:
        if "[Self-Correction]" in line or "簡報生成失敗" in line or "JSON" in line or "{" in line:
            print(line.strip()[:200])
