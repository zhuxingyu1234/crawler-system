import redis
from urllib.parse import urlparse

class RedisManager:
    def __init__(self, host='localhost', port=6379):
        self.conn = redis.Redis(host=host, port=port)
        self.seed_key = "seed_urls"
        self.pending_key = "pending_urls"

    # 管理种子URL
    def add_seed_url(self, url):
        self.conn.sadd(self.seed_key, url)

    # 待爬取URL队列（支持优先级）
    def push_pending_url(self, url, priority=0):
        self.conn.zadd(self.pending_key, {url: priority})

    # 根据策略分发URL（实现两种策略）
    def pop_url(self, strategy="round_robin"):
        if strategy == "round_robin":
            return self.conn.lpop(self.pending_key)
        elif strategy == "priority":
            return self.conn.zpopmax(self.pending_key)[0]
