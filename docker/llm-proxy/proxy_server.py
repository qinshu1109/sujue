"""
LLM代理服务器 - 提供速率限制和请求转发
女娲智慧：控流如治水，疏堵结合
"""

import os
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from collections import deque

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
import httpx
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from tenacity import retry, stop_after_attempt, wait_exponential

# 配置
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
ANTHROPIC_BASE_URL = "https://api.anthropic.com"
RATE_LIMIT_RPM = int(os.getenv('RATE_LIMIT_RPM', '60'))  # 每分钟请求数
RATE_LIMIT_TPM = int(os.getenv('RATE_LIMIT_TPM', '100000'))  # 每分钟token数

# Prometheus指标
request_counter = Counter('llm_proxy_requests_total', 'Total requests', ['status'])
token_counter = Counter('llm_proxy_tokens_total', 'Total tokens', ['type'])
rate_limit_gauge = Gauge('llm_proxy_rate_limit_remaining', 'Remaining rate limit', ['type'])
latency_histogram = Histogram('llm_proxy_latency_seconds', 'Request latency')

app = FastAPI(title="LLM Proxy Service", version="1.0.0")

class RateLimiter:
    """速率限制器"""
    
    def __init__(self, rpm_limit: int, tpm_limit: int):
        self.rpm_limit = rpm_limit
        self.tpm_limit = tpm_limit
        self.request_times = deque()
        self.token_usage = deque()
        self._lock = asyncio.Lock()
    
    async def check_and_update(self, estimated_tokens: int = 1000) -> bool:
        """检查是否可以发送请求"""
        async with self._lock:
            now = time.time()
            minute_ago = now - 60
            
            # 清理过期记录
            while self.request_times and self.request_times[0] < minute_ago:
                self.request_times.popleft()
            
            while self.token_usage and self.token_usage[0][0] < minute_ago:
                self.token_usage.popleft()
            
            # 检查请求数限制
            if len(self.request_times) >= self.rpm_limit:
                return False
            
            # 检查token限制
            current_tokens = sum(tokens for _, tokens in self.token_usage)
            if current_tokens + estimated_tokens > self.tpm_limit:
                return False
            
            # 记录新请求
            self.request_times.append(now)
            self.token_usage.append((now, estimated_tokens))
            
            # 更新指标
            rate_limit_gauge.labels(type='rpm').set(self.rpm_limit - len(self.request_times))
            rate_limit_gauge.labels(type='tpm').set(self.tpm_limit - current_tokens - estimated_tokens)
            
            return True
    
    async def update_actual_tokens(self, actual_tokens: int):
        """更新实际使用的token数"""
        async with self._lock:
            if self.token_usage:
                # 更新最后一条记录
                timestamp, _ = self.token_usage[-1]
                self.token_usage[-1] = (timestamp, actual_tokens)

# 创建速率限制器实例
rate_limiter = RateLimiter(RATE_LIMIT_RPM, RATE_LIMIT_TPM)

# HTTP客户端
http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(60.0),
    headers={
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01"
    }
)

@app.on_event("shutdown")
async def shutdown_event():
    """关闭时清理资源"""
    await http_client.aclose()

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "rate_limits": {
            "rpm_limit": RATE_LIMIT_RPM,
            "tpm_limit": RATE_LIMIT_TPM
        }
    }

@app.get("/metrics")
async def metrics():
    """Prometheus指标"""
    return Response(content=generate_latest(), media_type="text/plain")

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_request(request: Request, path: str):
    """代理所有请求到Anthropic API"""
    
    # 检查速率限制
    estimated_tokens = 2000  # 估算token数
    if request.method == "POST" and "/messages" in path:
        try:
            body = await request.json()
            # 根据消息长度估算token
            content_length = sum(len(msg.get("content", "")) for msg in body.get("messages", []))
            estimated_tokens = max(1000, content_length * 2)
        except:
            pass
    
    if not await rate_limiter.check_and_update(estimated_tokens):
        request_counter.labels(status='rate_limited').inc()
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait before retrying."
        )
    
    # 构建目标URL
    target_url = f"{ANTHROPIC_BASE_URL}/{path}"
    
    # 准备请求
    headers = dict(request.headers)
    headers.pop("host", None)
    headers["x-api-key"] = ANTHROPIC_API_KEY
    
    try:
        # 发送请求
        start_time = time.time()
        
        if request.method == "POST":
            body = await request.body()
            response = await http_client.post(
                target_url,
                content=body,
                headers=headers,
                params=dict(request.query_params)
            )
        else:
            response = await http_client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                params=dict(request.query_params)
            )
        
        # 记录延迟
        latency = time.time() - start_time
        latency_histogram.observe(latency)
        
        # 解析响应以获取实际token使用量
        if response.status_code == 200 and "/messages" in path:
            try:
                response_data = response.json()
                usage = response_data.get("usage", {})
                total_tokens = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
                
                # 更新实际token使用量
                await rate_limiter.update_actual_tokens(total_tokens)
                
                # 记录token指标
                token_counter.labels(type='input').inc(usage.get("input_tokens", 0))
                token_counter.labels(type='output').inc(usage.get("output_tokens", 0))
            except:
                pass
        
        # 记录请求指标
        request_counter.labels(status='success' if response.status_code < 400 else 'error').inc()
        
        # 返回响应
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
        
    except httpx.TimeoutException:
        request_counter.labels(status='timeout').inc()
        raise HTTPException(status_code=504, detail="Request timeout")
    except Exception as e:
        request_counter.labels(status='error').inc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/messages")
async def messages_endpoint(request: Request):
    """兼容OpenAI格式的消息端点"""
    # 转发到Anthropic的messages端点
    return await proxy_request(request, "v1/messages")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)