with open("docker-compose.yml", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("redis://redis:6379", "redis://lazybridge_redis:6379")

with open("docker-compose.yml", "w", encoding="utf-8") as f:
    f.write(content)
