FROM python:3.10-slim

LABEL maintainer="NuWa <nuwa@text2sql.local>"
LABEL description="LLM代理服务 - 速率控制与负载均衡"

WORKDIR /app

# 安装依赖
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    httpx==0.25.2 \
    redis==5.0.1 \
    prometheus-client==0.19.0 \
    tenacity==8.2.3

# 复制代理服务代码
COPY proxy_server.py .

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

EXPOSE 8080

# 启动命令
CMD ["uvicorn", "proxy_server:app", "--host", "0.0.0.0", "--port", "8080"]