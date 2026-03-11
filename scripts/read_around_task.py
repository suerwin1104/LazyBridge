with open('bot.log', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()
    # Read around line 1431
    for i in range(1430, min(1480, len(lines))):
        print(f"{i+1}: {lines[i].strip()}")
