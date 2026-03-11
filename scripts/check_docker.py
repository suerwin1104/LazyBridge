import subprocess
import sys
try:
    result = subprocess.run(["docker", "compose", "ps", "-a"], capture_output=True, text=True, check=True)
    print("DOCKER COMPOSE PS -a:")
    print(result.stdout)
except Exception as e:
    print("Error:", e)
