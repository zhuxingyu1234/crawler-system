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

class RedisProxyPool:
    def __init__(self, host='localhost', port=6379, db=0):
        self.conn = redis.Redis(host=host, port=port, db=db)
        self.proxy_key = "proxy_pool"

    def add_proxy(self, proxy, score=100):
        """添加代理并初始化分数"""
        self.conn.zadd(self.proxy_key, {proxy: score})

    def decrease_score(self, proxy, penalty=20):
        """降低代理分数"""
        self.conn.zincrby(self.proxy_key, -penalty, proxy)

    def get_random_proxy(self, scheme='http'):
        """按协议类型获取代理"""
        all_proxies = self.conn.zrangebyscore(self.proxy_key, 50, 100, withscores=True)
        filtered = [
            (p, s) for p, s in all_proxies
            if p.decode().startswith(f"{scheme}://")
        ]
        # ...权重随机选择逻辑

    def remove_dead_proxy(self, proxy):
        """移除死亡代理"""
        self.conn.zrem(self.proxy_key, proxy)

    # 智能处理含认证信息的代理
    def process_request(self, request, spider):
        proxy = self.redis.get_random_proxy()
        if '@' in proxy:  # 格式 user:pwd@ip:port
            request.meta['proxy'] = proxy
        else:
            # 从数据库获取认证信息
            auth = self.get_proxy_auth(proxy)
            request.meta['proxy'] = f"http://{auth}@{proxy.split('//')[1]}"