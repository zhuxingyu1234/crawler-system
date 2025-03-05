import time
import requests
from redis_manager import RedisProxyPool


class ProxyPoolManager:
    def __init__(self):
        self.redis = RedisProxyPool()
        self.refresh_interval = 600  # 10分钟维护一次

    def run(self):
        while True:
            self.clean_low_quality_proxies()
            self.refresh_proxy_pool()
            time.sleep(self.refresh_interval)

    def clean_low_quality_proxies(self):
        """清理低分代理"""
        self.redis.conn.zremrangebyscore("proxy_pool", "-inf", 50)

    def refresh_proxy_pool(self):
        """补充新鲜代理"""
        # 调用原始代理源API获取
        resp = requests.get("https://proxylist.geonode.com/api/proxy-list?limit=100")
        for proxy in resp.json()['data']:
            if proxy['protocols'] and 'socks5' not in proxy['protocols']:
                proxy_url = f"{proxy['protocols'][0]}://{proxy['ip']}:{proxy['port']}"
                self.redis.add_proxy(proxy_url)