from scrapy.core.downloader.contextfactory import ScrapyClientContextFactory
from twisted.internet.ssl import CertificateOptions
from OpenSSL import SSL

class CustomSSLContextFactory(ScrapyClientContextFactory):
    def getCertificateOptions(self):
        # 创建全局无验证的SSL上下文
        ctx = SSL.Context(SSL.SSLv23_METHOD)
        ctx.set_verify(SSL.VERIFY_NONE, lambda *args, **kwargs: True)  # 强制禁止所有验证
        ctx.set_options(
            SSL.OP_NO_SSLv2 |
            SSL.OP_NO_SSLv3 |
            SSL.OP_NO_COMPRESSION
        )
        ctx.check_hostname = False  # 关闭主机名检查

        # 劫持Twisted的底层SSL协议参数
        options = CertificateOptions()
        options._context = ctx
        return options
