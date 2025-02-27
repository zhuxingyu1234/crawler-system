import pymongo
from elasticsearch import Elasticsearch

class MongoDBPipeline:
    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri = crawler.settings.get('MONGO_URI'),
            mongo_db = crawler.settings.get('MONGO_DATABASE')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        self.db['webpages'].insert_one(dict(item))
        return item

from elasticsearch import Elasticsearch

class ElasticsearchPipeline:
    def __init__(self, es_uri, es_index):
        self.es_uri = es_uri
        self.es_index = es_index
        self.es = None  # 明确初始化客户端实例

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            es_uri=crawler.settings.get('ELASTICSEARCH_URI'),
            es_index=crawler.settings.get('ELASTICSEARCH_INDEX')
        )

    def open_spider(self, spider):
        # 完整HTTPS配置 (无需 scheme 参数，协议已在hosts的URI中指定)
        self.es = Elasticsearch(
            hosts=[self.es_uri],
            http_auth=('elastic', 't0seG9zaevEibM1tz7b+'),
            verify_certs=False,  # 开发环境禁用证书校验
            ssl_show_warn=False  # 不显示SSL警告
        )

        if not self.es.ping():
            raise ConnectionError("Elasticsearch 连接失败")

    def process_item(self, item, spider):
        if self.es:
            self.es.index(index=self.es_index, document=dict(item))
        return item

