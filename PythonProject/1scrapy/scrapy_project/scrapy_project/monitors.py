import psutil
import time
import json
from redis import Redis
from twisted.internet import task  # Scrapy 基于 Twisted 框架，需用其定时器


class SpiderMonitor:
    def __init__(self, redis_host='localhost', redis_port=6379, interval=10):
        self.redis = Redis(host=redis_host, port=redis_port)
        self.monitor_key = "scrapy:node:status"  # Redis中存储监控数据的键
        self.interval = interval  # 上报间隔（秒）

    def start_monitoring(self, spider):
        """启动定时监控任务"""
        self.spider_name = spider.name
        self.timer = task.LoopingCall(self._collect_metrics)
        self.timer.start(self.interval)

    def _collect_metrics(self):
        """采集并上报指标到 Redis"""
        try:
            cpu_percent = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            net_io = psutil.net_io_counters()

            metrics = {
                'timestamp': int(time.time()),
                'spider': self.spider_name,
                'cpu': cpu_percent,
                'memory': mem,
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
            }
            # 将数据序列化为JSON并保存到Redis的哈希表中
            self.redis.hset(
                self.monitor_key,
                self.spider_name,
                json.dumps(metrics)
            )
        except Exception as e:
            self.spider.logger.error(f'监控数据上报失败: {str(e)}')