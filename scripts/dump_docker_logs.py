import subprocess
result = subprocess.run(["docker", "compose", "logs", "--tail=30", "worker"], capture_output=True, text=True, encoding="utf-8", errors="replace")
print(result.stdout)
