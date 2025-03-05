import json
import scrapy
from scrapy import signals
from scrapy_redis.spiders import RedisSpider
from scrapy.exceptions import CloseSpider
from scrapy_project.items import WebPageItem
from urllib.parse import urlparse
from scrapy_project.monitors import SpiderMonitor


class DistributedSpider(RedisSpider):
    name = "main_spider"
    redis_key = "distributed:start_urls"
    test_flag = "VERSION_2.3"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 初始化监控器
        self.monitor = SpiderMonitor(interval=10)  # 每10秒上报一次
        self.monitor.start_monitoring(self)  # 启动监控

    def spider_closed(self, reason):
        self.monitor.timer.stop()  # 关闭定时器

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.validate_redis_data, signal=signals.spider_opened)
        return spider

    def validate_redis_data(self):
        sample = self.server.lindex(self.redis_key, 0)
        if not sample:
            self.logger.error(" Redis队列为空，无法启动爬虫")
            raise CloseSpider("empty_redis_queue")

        try:
            json.loads(sample)
            self.logger.info(" Redis数据格式验证通过")
        except Exception as e:
            self.logger.error(f" 非JSON格式数据: {str(e)}")
            self.logger.debug(f"原始数据调试: {sample[:100]}")  # 只输出前100字节避免日志过长
            raise CloseSpider(reason="invalid_redis_data_format")

    def make_requests_from_data(self, data):
        try:
            if isinstance(data, bytes):
                json_data = json.loads(data.decode('utf-8'))
                url = json_data['url']  # 直接触发KeyError若缺少此字段
            else:
                url = data  # 兼容纯字符串模式
            return scrapy.Request(url, meta=json_data.get('meta', {}))
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"非常规数据格式，尝试解析为直接URL: {e}")
            return scrapy.Request(data.decode('utf-8') if isinstance(data, bytes) else data)

    def parse(self, response):
        item = WebPageItem()
        item['url'] = response.url
        item['status'] = response.status
        item['content_length'] = len(response.body)
        item['proxy_used'] = response.meta.get('proxy', 'none')

        try:
            parsed_url = urlparse(response.url)
            if 'ip' in parsed_url.path:
                # 处理IP查询接口
                data = json.loads(response.text)
                if isinstance(data, dict):
                    item['client_ip'] = data.get('origin', 'Unknown')
            else:
                # 处理HTML页面
                item['title'] = response.css('title::text').get('')
                # 安全的meta description提取
                item['meta_description'] = response.xpath(
                    '//meta[@name="description"]/@content'
                ).get('')

                # 提取所有链接
                item['links'] = response.css('a::attr(href)').getall()

                # 提取所有图片链接
                item['images'] = response.css('img::attr(src)').getall()

        except Exception as e:
            item['parse_error'] = f"{type(e).__name__}: {str(e)}"
            self.logger.error(f"解析异常 URL: {response.url} 错误: {str(e)}")

        yield item