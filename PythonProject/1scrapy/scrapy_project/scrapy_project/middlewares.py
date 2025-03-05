import socket
import random
import requests
import dns.resolver
import logging
from urllib.parse import urlparse
from twisted.internet import threads
import dns.resolver
import socket
from scrapy.exceptions import IgnoreRequest
from scrapy import signals

logger = logging.getLogger(__name__)


class SmartProxyMiddleware:
    TEST_URL = "http://httpbin.org/ip"  # 代理验证地址
    MAX_FAILURES = 3  # 最大连续失败次数

    def __init__(self, redis_host, redis_port):
        self.redis = RedisProxyPool(host=redis_host, port=redis_port)
        self.failure_count = defaultdict(int)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            redis_host=crawler.settings.get('REDIS_HOST', 'localhost'),
            redis_port=crawler.settings.get('REDIS_PORT', 6379)
        )

    def fetch_new_proxies(self, spider):
        """定时补充新代理"""
        # 保持原有代理获取逻辑
        for api in self.proxy_apis:
            try:
                resp = requests.get(api, timeout=8)
                for proxy in resp.json().get('data', []):
                    proxy_str = f"{proxy['protocol']}://{proxy['ip']}:{proxy['port']}"
                    # 验证有效性并入库
                    if self.validate_proxy(proxy_str):
                        self.redis.add_proxy(proxy_str)
            except Exception as e:
                spider.logger.warning(f"代理源 {api} 获取失败: {str(e)}")

    def validate_proxy(self, proxy):
        """验证代理有效性"""
        try:
            resp = requests.get(
                self.TEST_URL,
                proxies={"http": proxy, "https": proxy},
                timeout=5
            )
            return resp.status_code == 200
        except:
            return False

    def process_request(self, request, spider):
        if not self.redis.conn.zcard(self.redis.proxy_key):
            spider.logger.warning("代理池为空，触发动态补充")
            self.fetch_new_proxies(spider)

        if proxy := self.redis.get_random_proxy():
            spider.logger.debug(f"使用代理: {proxy} | 剩余代理数: {self.redis.conn.zcount(...)}")
            request.meta['proxy'] = proxy
            request.meta['download_timeout'] = 10  # 代理特有超时
        else:
            raise IgnoreRequest("无可用代理")

    def process_exception(self, request, exception, spider):
        """代理失效处理"""
        proxy = request.meta.get('proxy')
        if proxy:
            self.failure_count[proxy] += 1
            if self.failure_count[proxy] >= self.MAX_FAILURES:
                spider.logger.error(f"代理永久失效: {proxy}")
                self.redis.remove_dead_proxy(proxy)
                del self.failure_count[proxy]
            else:
                self.redis.decrease_score(proxy)
                spider.logger.warning(f"代理降级: {proxy} | 当前失败次数: {self.failure_count[proxy]}")
        return request.replace(meta=request.meta)  # 重新调度请求

