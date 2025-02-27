from flask import Flask, jsonify
import json
from redis import Redis

app = Flask(__name__)
redis_client = Redis(host='localhost', port=6379)  # 与爬虫使用相同的 Redis 配置

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """获取所有爬虫节点的监控数据"""
    raw_data = redis_client.hgetall("scrapy:node:status")
    parsed_data = {}
    for spider_name, metrics_json in raw_data.items():
        spider_name = spider_name.decode('utf-8')  # Redis返回的是bytes类型，需解码
        parsed_data[spider_name] = json.loads(metrics_json.decode('utf-8'))
    return jsonify(parsed_data)

@app.route('/metrics/<spider_name>', methods=['GET'])
def get_spider_metrics(spider_name):
    """获取指定爬虫的监控数据"""
    metrics_json = redis_client.hget("scrapy:node:status", spider_name)
    if not metrics_json:
        return jsonify({"error": "Spider not found"}), 404
    return jsonify(json.loads(metrics_json.decode('utf-8')))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
