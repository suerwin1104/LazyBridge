import psutil
workers = []
for p in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if p.info['name'] and 'python' in p.info['name'].lower():
            if p.info['cmdline'] and any('worker.py' in arg for arg in p.info['cmdline']):
                workers.append(p.info)
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass

print(f"Total workers found: {len(workers)}")
for w in workers:
    print(f"PID: {w['pid']}, CMD: {' '.join(w['cmdline'])}")
