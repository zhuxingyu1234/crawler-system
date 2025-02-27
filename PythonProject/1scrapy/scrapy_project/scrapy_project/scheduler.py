from scrapy_redis.scheduler import Scheduler
from scrapy_redis import picklecompat  # 使用 Redis 的序列化工具

class DistributedScheduler(Scheduler):
    def __init__(self, server, strategy="priority"):
        super().__init__(server)
        self.strategy = strategy
        self.queue_key = "distributed:requests"  # 确保队列名与Redis中一致

    def next_request(self):
        # 从 Redis 获取请求的字节数据（具体取决于你的队列结构）
        if self.strategy == "priority":
            # ZPOPMAX 返回 (member, score) 元组
            data = self.server.zpopmax(self.queue_key)
            if data:
                request_bytes = data[0][0]  # 提取请求的字节数据
            else:
                return None
        else:
            # LPOP 直接返回请求的字节数据
            request_bytes = self.server.lpop(self.queue_key)

        # 反序列化字节数据为 Scrapy 的 Request 对象
        if request_bytes:
            return picklecompat.loads(request_bytes)
        return None
