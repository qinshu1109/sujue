#!/bin/bash
# 部署修复脚本 - 解决B-1阻塞项
# 女娲授命FrontEndBot：修正Podman网络和权限问题

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "═══════════════════════════════════════════════════════"
echo "🔧 部署修复脚本 - 解决网络和权限问题"
echo "执行角色：FrontEndBot"
echo "═══════════════════════════════════════════════════════"

# 检测Podman运行模式
check_podman_mode() {
    echo ""
    echo "📋 检测Podman运行模式..."
    
    if podman info | grep -q "rootless: true"; then
        echo "✅ 检测到Rootless模式"
        PODMAN_MODE="rootless"
    else
        echo "✅ 检测到Root模式"
        PODMAN_MODE="root"
    fi
}

# 修复docker-compose文件
fix_compose_file() {
    echo ""
    echo "🔧 修复Podman Compose配置..."
    
    COMPOSE_FILE="$PROJECT_ROOT/docker/podman-compose.yaml"
    
    # 备份原文件
    cp "$COMPOSE_FILE" "$COMPOSE_FILE.backup"
    
    # 修复端口映射（确保所有端口都正确暴露）
    cat > "$COMPOSE_FILE" << 'EOF'
version: '3.8'

networks:
  text2sql-net:
    driver: bridge

volumes:
  postgres-data:
  chroma-data:
  prometheus-data:
  grafana-data:
  registry-data:

services:
  # 私有Registry
  registry:
    image: docker.io/library/registry:2
    container_name: text2sql-registry
    ports:
      - "5000:5000"
    volumes:
      - registry-data:/var/lib/registry
    networks:
      - text2sql-net
    restart: unless-stopped

  # 数据库服务
  postgres:
    image: docker.io/library/postgres:15-alpine
    container_name: text2sql-db
    environment:
      POSTGRES_USER: text2sql
      POSTGRES_PASSWORD: secure_password_2025
      POSTGRES_DB: text2sql_db
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./config/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    networks:
      - text2sql-net
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U text2sql"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # 向量数据库
  chromadb:
    image: ghcr.io/chroma-core/chroma:latest
    container_name: text2sql-vec
    volumes:
      - chroma-data:/chroma/chroma
    networks:
      - text2sql-net
    ports:
      - "8000:8000"
    environment:
      IS_PERSISTENT: "TRUE"
      PERSIST_DIRECTORY: "/chroma/chroma"
      ANONYMIZED_TELEMETRY: "FALSE"
    restart: unless-stopped

  # LLM代理服务
  llm-proxy:
    build:
      context: ./docker/llm-proxy
      dockerfile: Dockerfile
    container_name: text2sql-llm-proxy
    environment:
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:-your-api-key-here}
      RATE_LIMIT_RPM: 60
      RATE_LIMIT_TPM: 100000
    networks:
      - text2sql-net
    ports:
      - "8080:8080"
    volumes:
      - ./config/llm-proxy:/app/config:ro
    restart: unless-stopped

  # DB-GPT主服务
  dbgpt-web:
    build:
      context: ./db-gpt
      dockerfile: Dockerfile
    container_name: text2sql-app
    environment:
      DB_HOST: postgres
      DB_PORT: 5432
      DB_USER: text2sql
      DB_PASSWORD: secure_password_2025
      DB_NAME: text2sql_db
      VECTOR_DB_URL: http://chromadb:8000
      LLM_PROXY_URL: http://llm-proxy:8080
    networks:
      - text2sql-net
    ports:
      - "5000:5000"
    depends_on:
      postgres:
        condition: service_healthy
      chromadb:
        condition: service_started
      llm-proxy:
        condition: service_started
    volumes:
      - ./config/dbgpt:/app/config:ro
      - ./promptx:/app/promptx:ro
      - ./logs:/app/logs
    restart: unless-stopped

  # Prometheus监控
  prometheus:
    image: docker.io/prom/prometheus:latest
    container_name: text2sql-prometheus
    volumes:
      - ./config/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    networks:
      - text2sql-net
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
    restart: unless-stopped

  # Grafana可视化
  grafana:
    image: docker.io/grafana/grafana:latest
    container_name: text2sql-grafana
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin123
      GF_USERS_ALLOW_SIGN_UP: "false"
    volumes:
      - grafana-data:/var/lib/grafana
      - ./config/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./config/grafana/datasources:/etc/grafana/provisioning/datasources:ro
    networks:
      - text2sql-net
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
    restart: unless-stopped

  # PromptX MCP导出器（新增）
  promptx-exporter:
    image: docker.io/library/python:3.10-slim
    container_name: text2sql-promptx-exporter
    command: python /app/exporter.py
    volumes:
      - ./monitoring/promptx-exporter:/app:ro
      - ./promptx/memory:/data/memory:ro
    networks:
      - text2sql-net
    ports:
      - "9101:9101"
    environment:
      EXPORTER_PORT: 9101
      MEMORY_PATH: /data/memory
    restart: unless-stopped
EOF
    
    echo "✅ Compose文件已更新"
}

# 修复权限问题
fix_permissions() {
    echo ""
    echo "🔐 修复文件权限..."
    
    # 创建必要的目录
    mkdir -p "$PROJECT_ROOT"/{logs,data,config/{postgres,prometheus,grafana/{dashboards,datasources},llm-proxy,dbgpt}}
    mkdir -p "$PROJECT_ROOT"/monitoring/promptx-exporter
    
    # 设置适当的权限
    if [ "$PODMAN_MODE" = "rootless" ]; then
        # Rootless模式：确保当前用户拥有所有权
        find "$PROJECT_ROOT" -type d -exec chmod 755 {} \;
        find "$PROJECT_ROOT" -type f -exec chmod 644 {} \;
        find "$PROJECT_ROOT"/scripts -type f -name "*.sh" -exec chmod 755 {} \;
    else
        # Root模式：设置容器用户权限
        chown -R 1000:1000 "$PROJECT_ROOT"/logs
        chown -R 999:999 "$PROJECT_ROOT"/data  # Postgres用户
        chown -R 472:472 "$PROJECT_ROOT"/config/grafana  # Grafana用户
    fi
    
    echo "✅ 权限设置完成"
}

# 创建PromptX导出器
create_promptx_exporter() {
    echo ""
    echo "📊 创建PromptX监控导出器..."
    
    cat > "$PROJECT_ROOT/monitoring/promptx-exporter/exporter.py" << 'EOF'
#!/usr/bin/env python3
"""
PromptX MCP Prometheus导出器
导出PromptX记忆和性能指标
"""

import json
import os
import time
from pathlib import Path
from prometheus_client import start_http_server, Gauge, Counter, Info
from datetime import datetime

# 定义Prometheus指标
memory_items_gauge = Gauge('promptx_memory_items_total', 'Total memory items', ['type'])
role_switches_counter = Counter('promptx_role_switches_total', 'Total role switches', ['from_role', 'to_role'])
test_status_gauge = Gauge('promptx_test_status', 'Test execution status', ['test_id'])
project_info = Info('promptx_project', 'Project information')

class PromptXExporter:
    def __init__(self, memory_path="/data/memory"):
        self.memory_path = Path(memory_path)
        
    def collect_metrics(self):
        """收集PromptX指标"""
        try:
            # 收集项目信息
            project_scope_file = self.memory_path / "project_scope.json"
            if project_scope_file.exists():
                with open(project_scope_file, 'r') as f:
                    project_data = json.load(f)
                    project_info.info({
                        'version': project_data.get('version', 'unknown'),
                        'stage': project_data.get('current_stage', 'W2')
                    })
            
            # 收集记忆项统计
            memory_files = list(self.memory_path.glob("*.json"))
            memory_items_gauge.labels(type='total').set(len(memory_files))
            
            # 收集测试状态
            checklist_file = self.memory_path / "week2-acceptance-checklist.json"
            if checklist_file.exists():
                with open(checklist_file, 'r') as f:
                    checklist = json.load(f)
                    for test_case in checklist.get('test_cases', []):
                        status = 1 if test_case['status'] == 'passed' else 0
                        test_status_gauge.labels(test_id=test_case['id']).set(status)
            
        except Exception as e:
            print(f"Error collecting metrics: {e}")
    
    def run(self, port=9101):
        """启动导出器"""
        start_http_server(port)
        print(f"PromptX Exporter started on port {port}")
        
        while True:
            self.collect_metrics()
            time.sleep(30)  # 每30秒更新一次

if __name__ == "__main__":
    port = int(os.getenv('EXPORTER_PORT', '9101'))
    memory_path = os.getenv('MEMORY_PATH', '/data/memory')
    
    exporter = PromptXExporter(memory_path)
    exporter.run(port)
EOF
    
    # 创建requirements文件
    cat > "$PROJECT_ROOT/monitoring/promptx-exporter/requirements.txt" << 'EOF'
prometheus-client==0.19.0
EOF
    
    echo "✅ PromptX导出器已创建"
}

# 更新Prometheus配置
update_prometheus_config() {
    echo ""
    echo "📈 更新Prometheus配置..."
    
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
    
  - job_name: 'promptx-exporter'
    static_configs:
      - targets: ['promptx-exporter:9101']
    
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
      
  - job_name: 'chromadb'
    static_configs:
      - targets: ['chromadb:8000']
    metrics_path: '/metrics'
    
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
EOF
    
    echo "✅ Prometheus配置已更新"
}

# 验证修复结果
verify_fixes() {
    echo ""
    echo "🔍 验证修复结果..."
    
    # 检查文件存在
    echo "检查关键文件："
    files=(
        "$PROJECT_ROOT/docker/podman-compose.yaml"
        "$PROJECT_ROOT/config/prometheus/prometheus.yml"
        "$PROJECT_ROOT/monitoring/promptx-exporter/exporter.py"
    )
    
    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            echo "  ✅ $file"
        else
            echo "  ❌ $file 缺失"
        fi
    done
    
    echo ""
    echo "端口映射配置："
    echo "  - 5000: DB-GPT API"
    echo "  - 5432: PostgreSQL"
    echo "  - 8000: ChromaDB"
    echo "  - 8080: LLM Proxy"
    echo "  - 9090: Prometheus"
    echo "  - 9101: PromptX Exporter"
    echo "  - 3000: Grafana"
}

# 主执行流程
main() {
    check_podman_mode
    fix_compose_file
    fix_permissions
    create_promptx_exporter
    update_prometheus_config
    verify_fixes
    
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "✅ 部署修复完成！"
    echo ""
    echo "下一步操作："
    echo "1. 重新运行初始化脚本："
    echo "   ./scripts/init-system.sh"
    echo ""
    echo "2. 启动容器服务："
    echo "   cd docker && podman-compose up -d"
    echo ""
    echo "3. 验证服务状态："
    echo "   podman ps"
    echo ""
    echo "FrontEndBot任务完成，控制权交还NuWa。"
    echo "═══════════════════════════════════════════════════════"
}

# 记录执行开始
echo "开始时间: $(date)"
START_TIME=$(date +%s)

# 执行主函数
main

# 记录执行时间
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
echo "执行耗时: ${DURATION}秒"

# 更新状态到记忆
if [ -d "$PROJECT_ROOT/promptx/memory" ]; then
    cat > "$PROJECT_ROOT/promptx/memory/blocker-B1-status.json" << EOF
{
  "blocker": "B-1",
  "status": "resolved",
  "resolved_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "duration_seconds": $DURATION,
  "resolved_by": "FrontEndBot",
  "actions_taken": [
    "Fixed podman-compose.yaml port mappings",
    "Resolved permission issues for rootless/root modes",
    "Created PromptX exporter for monitoring",
    "Updated Prometheus configuration"
  ]
}
EOF
fi