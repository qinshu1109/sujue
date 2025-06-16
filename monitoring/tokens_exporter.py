#!/usr/bin/env python3
"""
Prometheus Token使用量导出器
女娲造物：量化智能，精准监控
"""

import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional
import structlog
from prometheus_client import Counter, Histogram, Gauge, start_http_server, REGISTRY

# 配置日志
logger = structlog.get_logger()

class TokenMetricsExporter:
    """Token指标导出器"""
    
    def __init__(self, port: int = 9100):
        self.port = port
        self.server_thread = None
        self.running = False
        
        # 定义Prometheus指标
        self.tokens_used_total = Counter(
            'tokens_used_total',
            'Total tokens consumed by the Text2SQL system',
            ['model', 'type', 'endpoint']
        )
        
        self.token_cost_usd_total = Counter(
            'token_cost_usd_total', 
            'Total cost in USD for token usage',
            ['model', 'endpoint']
        )
        
        self.query_response_time = Histogram(
            'text2sql_query_duration_seconds',
            'Time spent processing text2sql queries',
            ['endpoint', 'status'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
        )
        
        self.active_queries = Gauge(
            'text2sql_active_queries',
            'Number of currently active queries'
        )
        
        self.model_availability = Gauge(
            'text2sql_model_availability',
            'Model availability status (1=available, 0=unavailable)',
            ['model']
        )
        
        # Token价格映射（每1K tokens的USD价格）
        self.token_prices = {
            'claude-3-opus-20240229': {
                'input': 0.015,   # $15/1M input tokens
                'output': 0.075   # $75/1M output tokens
            },
            'claude-3-sonnet-20240229': {
                'input': 0.003,   # $3/1M input tokens
                'output': 0.015   # $15/1M output tokens
            },
            'claude-3-haiku-20240307': {
                'input': 0.00025, # $0.25/1M input tokens
                'output': 0.00125 # $1.25/1M output tokens
            }
        }
        
        logger.info("TokenMetricsExporter初始化完成", port=self.port)
    
    def record_token_usage(self, 
                          model: str,
                          input_tokens: int,
                          output_tokens: int, 
                          endpoint: str = "text2sql"):
        """记录Token使用量"""
        try:
            # 记录输入tokens
            self.tokens_used_total.labels(
                model=model,
                type="input", 
                endpoint=endpoint
            ).inc(input_tokens)
            
            # 记录输出tokens
            self.tokens_used_total.labels(
                model=model,
                type="output",
                endpoint=endpoint
            ).inc(output_tokens)
            
            # 计算成本
            if model in self.token_prices:
                input_cost = (input_tokens / 1000) * self.token_prices[model]['input']
                output_cost = (output_tokens / 1000) * self.token_prices[model]['output']
                total_cost = input_cost + output_cost
                
                self.token_cost_usd_total.labels(
                    model=model,
                    endpoint=endpoint
                ).inc(total_cost)
                
                logger.info("Token使用量已记录",
                           model=model,
                           input_tokens=input_tokens,
                           output_tokens=output_tokens,
                           cost_usd=round(total_cost, 6),
                           endpoint=endpoint)
            else:
                logger.warning("未知模型价格", model=model)
                
        except Exception as e:
            logger.error(f"记录Token使用量失败: {e}")
    
    def record_query_time(self, endpoint: str, status: str, duration: float):
        """记录查询响应时间"""
        self.query_response_time.labels(
            endpoint=endpoint,
            status=status
        ).observe(duration)
    
    def set_active_queries(self, count: int):
        """设置当前活跃查询数"""
        self.active_queries.set(count)
    
    def set_model_availability(self, model: str, available: bool):
        """设置模型可用性"""
        self.model_availability.labels(model=model).set(1 if available else 0)
    
    def start_server(self):
        """启动Prometheus HTTP服务器"""
        if self.running:
            logger.warning("Exporter服务器已在运行")
            return
        
        try:
            def run_server():
                start_http_server(self.port)
                logger.info(f"Prometheus指标服务器启动", port=self.port)
                while self.running:
                    time.sleep(1)
            
            self.running = True
            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()
            
            # 初始化一些基础指标
            for model in self.token_prices.keys():
                self.set_model_availability(model, True)
            
            logger.info("TokenMetricsExporter服务启动成功", 
                       endpoint=f"http://localhost:{self.port}/metrics")
            
        except Exception as e:
            logger.error(f"启动Exporter服务器失败: {e}")
            self.running = False
    
    def stop_server(self):
        """停止服务器"""
        if self.running:
            self.running = False
            logger.info("TokenMetricsExporter服务停止")
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """获取当前指标快照"""
        try:
            from prometheus_client import generate_latest
            metrics_data = generate_latest(REGISTRY).decode('utf-8')
            
            # 解析tokens_used_total指标
            token_metrics = {}
            for line in metrics_data.split('\n'):
                if line.startswith('tokens_used_total'):
                    token_metrics[line] = True
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'metrics_endpoint': f"http://localhost:{self.port}/metrics",
                'token_metrics_count': len(token_metrics),
                'server_running': self.running
            }
            
        except Exception as e:
            logger.error(f"获取指标快照失败: {e}")
            return {}

# 全局实例
_exporter_instance = None

def get_exporter(port: int = 9100) -> TokenMetricsExporter:
    """获取全局Exporter实例"""
    global _exporter_instance
    if _exporter_instance is None:
        _exporter_instance = TokenMetricsExporter(port)
    return _exporter_instance

def main():
    """主函数 - 用于测试"""
    exporter = get_exporter(9100)
    exporter.start_server()
    
    # 模拟一些数据
    print("🚀 启动Token指标测试...")
    
    # 模拟查询
    exporter.record_token_usage(
        model="claude-3-opus-20240229",
        input_tokens=150,
        output_tokens=45,
        endpoint="text2sql"
    )
    
    exporter.record_token_usage(
        model="claude-3-sonnet-20240229", 
        input_tokens=200,
        output_tokens=60,
        endpoint="validate"
    )
    
    exporter.record_query_time("text2sql", "success", 1.5)
    exporter.set_active_queries(3)
    
    print(f"📊 指标已记录，访问: http://localhost:9100/metrics")
    print("🔍 测试命令: curl localhost:9100/metrics | grep tokens_used_total")
    
    # 保持运行
    try:
        while True:
            time.sleep(10)
            # 模拟更多数据
            exporter.record_token_usage(
                model="claude-3-haiku-20240307",
                input_tokens=100, 
                output_tokens=30,
                endpoint="text2sql"
            )
            
    except KeyboardInterrupt:
        print("\n⚠️ 停止服务...")
        exporter.stop_server()

if __name__ == "__main__":
    main()