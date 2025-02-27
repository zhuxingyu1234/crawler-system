import json
import psutil
import time
from redis import Redis

class SpiderMonitor:
    def __init__(self):
        self.redis = Redis()
        self.monitor_key = "spider:status"

    def report_status(self):
        # 实时上报CPU/内存信息
        cpu_percent = psutil.cpu_percent()
        memory_info = psutil.virtual_memory()
        self.redis.hset(self.monitor_key, "node1",
                        f"CPU: {cpu_percent}%, MEM: {memory_info.percent}%")


class SpiderMonitor:
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis = Redis(host=redis_host, port=redis_port)
        self.monitor_key = "scrapy:node:status"  # 统一的监控键

    def collect_metrics(self, spider_name):
        """定时上报指标到 Redis"""
        cpu_percent = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        net_io = psutil.net_io_counters()

        metrics = {
            'timestamp': int(time.time()),
            'spider': spider_name,
            'cpu': cpu_percent,
            'memory': mem,
            'disk': disk,
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'processes': len(psutil.pids())
        }
        self.redis.hset(self.monitor_key, spider_name, json.dumps(metrics))