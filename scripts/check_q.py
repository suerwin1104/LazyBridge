import redis
r = redis.Redis(host='localhost', port=6379, db=0)
l = r.llen('lazybridge_tasks')
print(f'Queue length: {l}')
