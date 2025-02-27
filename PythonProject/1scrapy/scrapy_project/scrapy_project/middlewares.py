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

class DnsResolutionMiddleware:
    def __init__(self, dns_servers=None, cache_enabled=True):
        self.dns_servers = dns_servers or ["8.8.8.8", "1.1.1.1"]
        self.cache = {}
        self.cache_enabled = cache_enabled
        self.record_types = ['A', 'AAAA']

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        instance = cls(
            dns_servers=settings.getlist('DNS_SERVERS'),
            cache_enabled=settings.getbool('DNS_CACHE_ENABLED', True)
        )
        crawler.signals.connect(instance.spider_closed, signal=signals.spider_closed)
        return instance

    def spider_closed(self, spider):
        self.cache.clear()
        spider.logger.info("DNS缓存已清空")

    async def resolve_domain(self, domain, spider):
        cached_ip = self.cache.get(domain)
        if cached_ip and self.cache_enabled:
            spider.logger.debug(f"[DNS缓存命中] {domain} -> {cached_ip}")
            return cached_ip

        resolver = dns.resolver.Resolver(configure=False)
        resolver.nameservers = self.dns_servers

        try:
            answer = await threads.deferToThread(resolver.resolve, domain, 'A')
            ip = str(answer[0])
            record_type = 'A'
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            try:
                answer = await threads.deferToThread(resolver.resolve, domain, 'AAAA')
                ip = str(answer[0])
                record_type = 'AAAA'
            except Exception as e:
                ip = await threads.deferToThread(socket.gethostbyname, domain)
                record_type = 'System'
                spider.logger.warning(f"[DNS回退] {domain} 使用系统DNS解析 -> {ip}")
        spider.logger.debug(f"[DNS解析完成] {domain} {record_type}记录 -> {ip}")
        if self.cache_enabled:
            self.cache[domain] = ip
        return ip

    async def process_request(self, request, spider):
        parsed = urlparse(request.url)
        if not parsed.hostname or request.meta.get('dns_bypass'):
            return

        try:
            # DNS解析
            resolved_ip = await self.resolve_domain(parsed.hostname, spider)

            # 构造连接的目标地址，保持原域名但底层使用IP连接
            port = parsed.port
            if not port:
                port = 443 if parsed.scheme == 'https' else 80

            # 核心修改：创建新请求时不替换域名，而是通过meta指定连接目标
            new_request = request.replace(
                meta={
                    **request.meta,
                    'dns_bypass': True,
                    'connect_to': (resolved_ip, port)  # 指定底层连接到IP而非域名
                },
                # 保留原始域名和协议头
                headers={
                    **request.headers,
                    'Host': parsed.hostname  # 关键！确保Host头正确
                }
            )

            return new_request
        except Exception as e:
            spider.logger.error(f"请求预处理失败 - URL: {request.url} 错误: {str(e)}")
            raise IgnoreRequest(f"DNS 解析失败: {str(e)}")


class SSLContextAdapterMiddleware:
    """SSL 上下文适配层"""

    def process_request(self, request, spider):
        if 'ssl_context' in request.meta:
            return request.replace(
                meta={
                    **request.meta,
                    'ssl_context': request.meta['ssl_context']
                }
            )


USER_AGENT_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
]


class ProxyMiddleware:
    def __init__(self):
        self.proxy_apis = [
            "https://proxylist.geonode.com/api/proxy-list?limit=10",
            "https://pubproxy.com/api/proxy",
            "https://api.proxyscrape.com/v2/?request=getproxies"
        ]

    def process_request(self, request, spider):
        for api in self.proxy_apis:
            try:
                resp = requests.get(api, timeout=8)
                proxy = random.choice(resp.json()['data'])
                request.meta['proxy'] = f"http://{proxy['ip']}:{proxy['port']}"
                spider.logger.debug(f"代理设置成功: {proxy['ip']}:{proxy['port']}")
                return
            except Exception as e:
                spider.logger.warn(f"代理获取失败: {api} -> {str(e)}")


class RandomUserAgentMiddleware:
    def process_request(self, request, spider):
        ua = random.choice(USER_AGENT_LIST)
        request.headers['User-Agent'] = ua
        request.headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        request.headers['Accept-Language'] = 'en-US,en;q=0.5'


class HeaderRotationMiddleware:
    def process_request(self, request, spider):
        request.headers.update({
            'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Upgrade-Insecure-Requests': '1'
        })
        # 追加设备指纹
        request.cookies['device_fp'] = self.generate_device_fingerprint()

    @staticmethod
    def generate_device_fingerprint():
        import uuid
        return str(uuid.uuid4()).replace('-', '')
