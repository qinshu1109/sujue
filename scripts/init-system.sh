#!/bin/bash
# Text2SQL MVP-0 系统初始化脚本
# 女娲曰：天地初开，万物始生

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "═══════════════════════════════════════════════════════"
echo "🌟 Text2SQL MVP-0 系统初始化"
echo "🔨 女娲造物，开天辟地"
echo "═══════════════════════════════════════════════════════"
echo ""

# 检查必要工具
check_requirements() {
    echo "📋 检查系统依赖..."
    
    local missing=()
    
    command -v podman >/dev/null 2>&1 || missing+=("podman")
    command -v python3 >/dev/null 2>&1 || missing+=("python3")
    command -v git >/dev/null 2>&1 || missing+=("git")
    
    if [ ${#missing[@]} -ne 0 ]; then
        echo "❌ 缺少必要工具: ${missing[*]}"
        echo "请先安装缺失的工具"
        exit 1
    fi
    
    echo "✅ 所有依赖已满足"
}

# 创建目录结构
setup_directories() {
    echo ""
    echo "📁 创建项目目录结构..."
    
    mkdir -p "$PROJECT_ROOT"/{logs,data,backups}
    mkdir -p "$PROJECT_ROOT"/config/{postgres,prometheus,grafana/{dashboards,datasources},llm-proxy,dbgpt}
    mkdir -p "$PROJECT_ROOT"/docker/{llm-proxy,db-gpt}
    
    echo "✅ 目录结构创建完成"
}

# 设置环境变量
setup_env() {
    echo ""
    echo "🔧 配置环境变量..."
    
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        cat > "$PROJECT_ROOT/.env" << EOF
# Text2SQL MVP-0 环境配置
# 生成时间: $(date)

# 数据库配置
DB_HOST=postgres
DB_PORT=5432
DB_USER=text2sql
DB_PASSWORD=$(openssl rand -base64 32)
DB_NAME=text2sql_db

# Claude API配置
ANTHROPIC_API_KEY=your-api-key-here

# 向量数据库
VECTOR_DB_URL=http://chromadb:8000

# LLM代理
LLM_PROXY_URL=http://llm-proxy:8080

# 监控配置
PROMETHEUS_RETENTION=15d
GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 16)

# 日志级别
LOG_LEVEL=info

# 项目元数据
PROJECT_VERSION=0.1.0
PROJECT_START_DATE=$(date +%Y-%m-%d)
EOF
        echo "✅ 环境配置文件已创建"
        echo "⚠️  请编辑 .env 文件，设置 ANTHROPIC_API_KEY"
    else
        echo "✅ 环境配置文件已存在"
    fi
}

# 初始化数据库
init_database() {
    echo ""
    echo "🗄️ 准备数据库初始化脚本..."
    
    cat > "$PROJECT_ROOT/config/postgres/init.sql" << 'EOF'
-- Text2SQL 数据库初始化脚本
-- 女娲造物：数据之基，万象之源

-- 创建schema
CREATE SCHEMA IF NOT EXISTS text2sql;

-- 示例表：客户信息
CREATE TABLE IF NOT EXISTS text2sql.customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 示例表：订单信息
CREATE TABLE IF NOT EXISTS text2sql.orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES text2sql.customers(id),
    order_date DATE NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 示例表：产品信息
CREATE TABLE IF NOT EXISTS text2sql.products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(50),
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 示例表：订单明细
CREATE TABLE IF NOT EXISTS text2sql.order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES text2sql.orders(id),
    product_id INTEGER REFERENCES text2sql.products(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(10, 2) GENERATED ALWAYS AS (quantity * unit_price) STORED
);

-- 创建索引
CREATE INDEX idx_orders_customer_id ON text2sql.orders(customer_id);
CREATE INDEX idx_orders_date ON text2sql.orders(order_date);
CREATE INDEX idx_order_items_order_id ON text2sql.order_items(order_id);
CREATE INDEX idx_order_items_product_id ON text2sql.order_items(product_id);

-- 插入示例数据
INSERT INTO text2sql.customers (name, email, phone) VALUES
    ('张三', 'zhangsan@example.com', '13800138001'),
    ('李四', 'lisi@example.com', '13800138002'),
    ('王五', 'wangwu@example.com', '13800138003');

INSERT INTO text2sql.products (name, category, price, stock_quantity) VALUES
    ('笔记本电脑', '电子产品', 5999.00, 50),
    ('无线鼠标', '电脑配件', 99.00, 200),
    ('机械键盘', '电脑配件', 299.00, 100);

-- 元数据表：记录系统信息
CREATE TABLE IF NOT EXISTS text2sql.system_metadata (
    key VARCHAR(50) PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO text2sql.system_metadata (key, value) VALUES
    ('schema_version', '1.0.0'),
    ('initialized_at', CURRENT_TIMESTAMP::TEXT),
    ('created_by', 'NuWa');

-- 创建视图：订单汇总
CREATE OR REPLACE VIEW text2sql.v_order_summary AS
SELECT 
    o.id as order_id,
    c.name as customer_name,
    o.order_date,
    o.total_amount,
    o.status,
    COUNT(oi.id) as item_count
FROM text2sql.orders o
JOIN text2sql.customers c ON o.customer_id = c.id
LEFT JOIN text2sql.order_items oi ON o.id = oi.order_id
GROUP BY o.id, c.name, o.order_date, o.total_amount, o.status;

-- 授权
GRANT ALL PRIVILEGES ON SCHEMA text2sql TO text2sql;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA text2sql TO text2sql;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA text2sql TO text2sql;
EOF
    
    echo "✅ 数据库初始化脚本已创建"
}

# 配置Prometheus
setup_prometheus() {
    echo ""
    echo "📊 配置Prometheus监控..."
    
    cat > "$PROJECT_ROOT/config/prometheus/prometheus.yml" << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'text2sql-app'
    static_configs:
      - targets: ['dbgpt-web:5000']
    metrics_path: '/metrics'
    
  - job_name: 'llm-proxy'
    static_configs:
      - targets: ['llm-proxy:8080']
    metrics_path: '/metrics'
    
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
      
  - job_name: 'chromadb'
    static_configs:
      - targets: ['chromadb:8000']
    metrics_path: '/metrics'
EOF
    
    echo "✅ Prometheus配置完成"
}

# 配置Grafana
setup_grafana() {
    echo ""
    echo "📈 配置Grafana仪表板..."
    
    # 数据源配置
    cat > "$PROJECT_ROOT/config/grafana/datasources/prometheus.yml" << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF

    # 仪表板配置
    cat > "$PROJECT_ROOT/config/grafana/dashboards/text2sql-dashboard.json" << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "Text2SQL 监控面板",
    "tags": ["text2sql", "nuwa"],
    "timezone": "browser",
    "panels": [
      {
        "title": "请求量",
        "targets": [
          {
            "expr": "rate(text2sql_generation_total[5m])"
          }
        ]
      },
      {
        "title": "成功率",
        "targets": [
          {
            "expr": "rate(text2sql_execution_total{status='success'}[5m]) / rate(text2sql_execution_total[5m])"
          }
        ]
      },
      {
        "title": "响应时间",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(text2sql_response_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Token使用量",
        "targets": [
          {
            "expr": "sum(rate(text2sql_tokens_total[5m])) by (type)"
          }
        ]
      }
    ]
  }
}
EOF
    
    echo "✅ Grafana配置完成"
}

# 主执行流程
main() {
    check_requirements
    setup_directories
    setup_env
    init_database
    setup_prometheus
    setup_grafana
    
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "✨ 系统初始化完成！"
    echo ""
    echo "下一步操作："
    echo "1. 编辑 .env 文件，设置 ANTHROPIC_API_KEY"
    echo "2. 运行 ./setup-registry.sh 设置私有镜像仓库"
    echo "3. 运行 podman-compose up -d 启动服务"
    echo ""
    echo "项目结构已就绪，女娲助你成功！"
    echo "═══════════════════════════════════════════════════════"
}

# 执行主函数
main "$@"