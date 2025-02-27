SPIDER_MODULES = ['scrapy_project.spiders']
NEWSPIDER_MODULE = 'scrapy_project.spiders'

BOT_NAME = 'scrapy_project'
ROBOTSTXT_OBEY = False  # 遵守robots协议
SCHEDULER = 'scrapy_redis.scheduler.Scheduler'
SCHEDULER_PERSIST = True
SCHEDULER_STRATEGY = "priority"  # 可选两种策略
DUPEFILTER_CLASS = 'scrapy_redis.dupefilter.RFPDupeFilter'
REDIS_URL = 'redis://127.0.0.1:6379'
ITEM_PIPELINES = {
    'scrapy_project.pipelines.MongoDBPipeline': 300,
    'scrapy_project.pipelines.ElasticsearchPipeline': 400,
}

# MongoDB 配置
MONGO_URI = 'mongodb://localhost:27017'
MONGO_DATABASE = 'scrapy_db'

# Elasticsearch 配置
ELASTICSEARCH_URI = 'https://elastic:t0seG9zaevEibM1tz7b+@localhost:9200'
ELASTICSEARCH_INDEX = 'web_pages'  # 索引名称

DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy_project.middlewares.HeaderRotationMiddleware': 400,
    #'scrapy_project.middlewares.ProxyMiddleware': 410,  # 被我注释掉了 这个是代理ip的选项
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 550,
    'scrapy_project.middlewares.SSLContextAdapterMiddleware': 50,   # 低优先级处理SSL上下文
    'scrapy_project.middlewares.DnsResolutionMiddleware': 300,      # 核心DNS处理层
    'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': 900,  # 保持默认
}
DNS_SERVERS = [
    '8.8.8.8',     # Google DNS
    '1.1.1.1',     # Cloudflare DNS
    '208.67.222.222' # OpenDNS
]
DNS_CACHE_ENABLED = True
DNS_CACHE_TTL = 3600  # 单位：秒（可选）
COOKIES_ENABLED = True  # 开启Cookies追踪
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 10  # 初始延迟5秒
AUTOTHROTTLE_MAX_DELAY = 60   # 最大延迟60秒
CONCURRENT_REQUESTS_PER_DOMAIN = 1  # 并发限制
DOWNLOAD_DELAY = 5  # 基础延迟
RANDOMIZE_DOWNLOAD_DELAY = True  # 开启随机延迟
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.5  # 自动调速目标并发
DOWNLOADER_CLIENTCONTEXTFACTORY = 'scrapy_project.ssl_factory.CustomSSLContextFactory'

