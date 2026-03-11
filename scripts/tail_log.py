with open('bot.log', 'r', errors='ignore') as f:
    lines = f.readlines()
    for line in lines[-100:]:
        print(line.strip()[:300])
