FROM python:3.10-slim

LABEL maintainer="NuWa <nuwa@text2sql.local>"
LABEL description="DB-GPT核心服务 - 女娲造物"

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要目录
RUN mkdir -p /app/logs /app/data /app/promptx

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV DB_GPT_HOME=/app
ENV AWEL_WORKFLOW_DIR=/app/workflows

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

EXPOSE 5000

# 启动命令
CMD ["python", "-m", "dbgpt", "start", "webserver", "--host", "0.0.0.0", "--port", "5000"]