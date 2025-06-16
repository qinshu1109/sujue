#!/bin/bash
# 启动测试服务器
# 女娲造物：一键启动，万事俱备

set -e

echo "🚀 启动Text2SQL测试服务器..."

# 设置环境变量
export PYTHONPATH="/home/qinshu/text2sql-mvp0/db-gpt:/home/qinshu/text2sql-mvp0/monitoring"
export DB_USER="test_user"
export DB_PASSWORD="test_pass"
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="test_db"
export ANTHROPIC_API_KEY="sk-test-key"
export LLM_PROXY_URL="http://localhost:8080"
export VECTOR_DB_URL="http://localhost:8000"

# 进入项目目录
cd "/home/qinshu/text2sql-mvp0/db-gpt"

# 创建模拟依赖
echo "📦 安装依赖..."
pip3 install --user fastapi uvicorn pydantic structlog prometheus-client sqlalchemy asyncpg anthropic chromadb-client tenacity pyyaml 2>/dev/null || true

# 启动服务（后台运行）
echo "🌟 启动FastAPI服务..."
nohup python3 -c "
import sys
sys.path.append('/home/qinshu/text2sql-mvp0/db-gpt')
sys.path.append('/home/qinshu/text2sql-mvp0/monitoring')

# 模拟启动
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from datetime import datetime

app = FastAPI(title='Text2SQL Test Server')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

@app.get('/health')
async def health():
    return {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat(), 'version': '0.1.0'}

@app.get('/metrics')
async def metrics():
    return '''# HELP tokens_used_total Total tokens used
# TYPE tokens_used_total counter
tokens_used_total{model=\"claude-3-opus-20240229\",type=\"input\",endpoint=\"text2sql\"} 1500
tokens_used_total{model=\"claude-3-opus-20240229\",type=\"output\",endpoint=\"text2sql\"} 450
tokens_used_total{model=\"claude-3-sonnet-20240229\",type=\"input\",endpoint=\"validate\"} 800
tokens_used_total{model=\"claude-3-sonnet-20240229\",type=\"output\",endpoint=\"validate\"} 200
'''

@app.post('/api/text2sql')
async def text2sql(request: dict):
    query = request.get('query', '')
    
    # 模拟SQL生成
    if '用户' in query:
        sql = 'SELECT name, email FROM users WHERE status = \"active\" ORDER BY created_at DESC'
        result = [
            {'name': '张三', 'email': 'zhang@example.com'},
            {'name': '李四', 'email': 'li@example.com'}
        ]
    elif '库存' in query:
        sql = 'SELECT * FROM inventory LIMIT 100'
        result = [{'product_id': i, 'quantity': 100-i} for i in range(10)]
    elif '订单' in query:
        sql = 'SELECT u.name, o.order_id, p.product_name FROM users u JOIN orders o ON u.id = o.user_id JOIN products p ON o.product_id = p.id'
        result = [{'name': '用户1', 'order_id': 'ORD001', 'product_name': '产品A'}]
    else:
        sql = 'SELECT * FROM test_table LIMIT 10'
        result = [{'id': 1, 'data': 'test'}]
    
    return {
        'sql': sql,
        'result': result,
        'explanation': '查询已成功执行',
        'confidence': 0.95,
        'execution_time_ms': 250.5,
        'tokens_used': {'input': 150, 'output': 45}
    }

@app.post('/api/sql/validate')
async def validate_sql(request: dict):
    sql = request.get('sql', '').upper()
    
    if 'DELETE' in sql or 'DROP' in sql or 'TRUNCATE' in sql:
        return {
            'status': 'BLOCK',
            'risks': ['CRITICAL_OPERATION detected in SQL'],
            'blocked_reason': 'CRITICAL_OPERATION',
            'confidence': 0.0
        }
    elif 'PAYMENTS' in sql:
        return {
            'status': 'WARN',
            'risks': [\"Table 'payments' not in whitelist\"],
            'confidence': 0.7
        }
    else:
        return {
            'status': 'PASS',
            'risks': [],
            'confidence': 0.95
        }

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
" > /tmp/test_server.log 2>&1 &

# 记录进程ID
echo $! > /tmp/test_server.pid

echo "⏳ 等待服务启动..."
sleep 3

# 检查服务状态
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ 服务启动成功！"
    echo "🌐 健康检查: http://localhost:8000/health"
    echo "📊 指标接口: http://localhost:8000/metrics"
    echo "🔧 API文档: http://localhost:8000/docs"
    echo ""
    echo "📋 进程ID: $(cat /tmp/test_server.pid)"
    echo "📄 日志文件: /tmp/test_server.log"
else
    echo "❌ 服务启动失败！"
    echo "📄 检查日志: /tmp/test_server.log"
    exit 1
fi