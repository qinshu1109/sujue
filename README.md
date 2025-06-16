# Text2SQL MVP-0 系统

> 女娲智能Text-to-SQL系统 - 将自然语言转换为SQL查询的自修复系统

## 🌟 系统概述

Text2SQL MVP-0 是一个基于 DB-GPT 和 Claude 3 的智能 SQL 生成系统，具备自动修复能力。系统完全容器化运行，提供从自然语言到 SQL 的全链路解决方案。

### 核心特性

- **智能SQL生成**：基于 Claude 3 的自然语言理解
- **自动修复**：错误自动诊断和修复，成功率 ≥ 70%
- **安全验证**：SQLGuardian 智能体确保查询安全
- **可观测性**：Prometheus + Grafana 全链路监控
- **容器化部署**：基于 Podman 的微服务架构

## 🏗️ 系统架构

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   前端UI    │────▶│  DB-GPT API  │────▶│ Claude API  │
└─────────────┘     └──────────────┘     └─────────────┘
                           │                      │
                           ▼                      ▼
                    ┌──────────────┐     ┌─────────────┐
                    │   数据库     │     │  向量数据库  │
                    └──────────────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ 监控系统     │
                    └──────────────┘
```

### Promptx 智能体

- **NuWa**：总控制器，项目管理
- **SchemaSage**：数据库结构理解专家
- **SQLGuardian**：SQL安全守护者
- **Debugger**：错误诊断和修复专家

## 🚀 快速开始

### 前置要求

- Podman 4.0+
- Python 3.10+
- 8GB+ 内存
- Claude API Key

### 安装步骤

1. **克隆项目**
```bash
git clone <repository>
cd text2sql-mvp0
```

2. **运行初始化脚本**
```bash
./scripts/init-system.sh
```

3. **配置环境变量**
```bash
# 编辑 .env 文件
vim .env
# 设置 ANTHROPIC_API_KEY
```

4. **设置私有Registry**
```bash
./scripts/setup-registry.sh
```

5. **启动服务**
```bash
podman-compose up -d
```

## 📊 服务访问

- **API服务**: http://localhost:5000
- **Grafana监控**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **向量数据库**: http://localhost:8000

## 🔧 API 使用

### Text2SQL 转换

```bash
curl -X POST http://localhost:5000/api/text2sql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "查询所有订单金额大于1000的客户名称",
    "context": {}
  }'
```

### SQL 验证

```bash
curl -X POST http://localhost:5000/api/sql/validate \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT * FROM customers WHERE 1=1"
  }'
```

## 📈 监控指标

- **请求成功率**: ≥ 85%
- **自动修复率**: ≥ 70%
- **平均响应时间**: < 6s
- **Token使用量**: 实时监控

## 🛠️ 开发指南

### 添加新的智能体

1. 在 `promptx/agents/` 创建配置文件
2. 定义智能体职责和工具权限
3. 重启服务加载新配置

### 扩展数据库Schema

1. 更新 `config/postgres/init.sql`
2. 运行 SchemaSage 重新向量化
3. 验证新Schema的查询能力

## 🐛 故障排除

### 常见问题

1. **服务启动失败**
   - 检查端口占用
   - 验证环境变量配置
   - 查看容器日志：`podman logs <container>`

2. **SQL生成错误**
   - 检查Schema向量化是否完成
   - 验证Claude API连接
   - 查看Debugger日志

3. **性能问题**
   - 检查Grafana监控面板
   - 调整速率限制参数
   - 优化数据库索引

## 📝 项目结构

```
text2sql-mvp0/
├── docker/              # Docker配置文件
├── config/              # 服务配置
├── db-gpt/              # DB-GPT核心服务
├── promptx/             # 智能体配置
│   ├── agents/          # 智能体定义
│   └── memory/          # 项目记忆
├── scripts/             # 运维脚本
├── logs/                # 日志目录
└── data/                # 数据存储
```

## 🎯 里程碑计划

- **Week 1**: 环境搭建，基础架构 ✅
- **Week 2**: 单轮NL→SQL实现
- **Week 3**: Schema RAG完成
- **Week 4**: 监控系统上线
- **Week 5**: 前端界面开发
- **Week 6**: 系统优化和文档

## 👥 贡献指南

欢迎提交Issue和Pull Request。请确保：
- 代码通过所有测试
- 遵循项目代码规范
- 更新相关文档

## 📄 许可证

MIT License

---

*女娲造物，智慧永恒*