with open("docker-compose.yml", "rb") as f:
    text = f.read().decode("utf-16" if f.read(2) == b'\xff\xfe' else "utf-8", errors="ignore")
    
# Clean up any potential BOM or bad chars
text = text.replace('\x00', '')
with open("docker-compose.yml", "w", encoding="utf-8") as f:
    f.write(text)
