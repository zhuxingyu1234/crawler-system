import scrapy

class WebPageItem(scrapy.Item):
    # 基础字段
    url = scrapy.Field()
    status = scrapy.Field()
    content_length = scrapy.Field()

    # IP专用字段
    client_ip = scrapy.Field()

    # HTML页面字段
    title = scrapy.Field()  # HTML页面的标题
    meta_description = scrapy.Field()  # HTML页面的描述
    headers = scrapy.Field()  # 预留扩展字段

    # 错误处理字段
    parse_error = scrapy.Field()  # 用于记录解析异常
