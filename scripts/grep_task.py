with open('bot.log', 'r', encoding='utf-8', errors='ignore') as f:
    for i, line in enumerate(f):
        if 'LazyBridgem' in line:
            print(f"Line {i+1}: {line.strip()}")
        if 'ARTIFICIAL_PUSH' in line or 'DEBUG TEST' in line:
             print(f"Line {i+1}: {line.strip()}")
