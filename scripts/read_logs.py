with open("bot.log", "r", errors="replace") as f:
    lines = f.readlines()
    with open("temp_log.txt", "w", encoding="utf-8") as out:
        out.write("".join(lines[-30:]))
