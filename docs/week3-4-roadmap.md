# Week 3-4 开发路线图

> 女娲智能项目管理 - Text2SQL MVP-0 后续迭代计划

## 📋 Phase-Gate 评审状态

- **评审日期**: 2025-06-16
- **当前阶段**: Week-2 条件通过
- **阻塞项**: 
  - [ ] 系统部署验证
  - [ ] 验收测试执行（目标：通过率≥85%）

## 🎯 Week-3 计划（功能强化）

### 时间线：2025-06-18 至 2025-06-24

| 任务ID | 任务名称 | 负责角色 | 优先级 | 交付标准 |
|--------|----------|----------|--------|----------|
| 3-1 | **UI精炼 & 国际化** | QueryScribe + FrontEndBot | P0 | React单页应用，支持中英文切换 |
| 3-2 | **自修复策略升级** | Debugger | P0 | 可配置重试次数(≤3)，错误分类体系 |
| 3-3 | **Prompt成本跟踪** | MetricsWatcher | P1 | Token使用仪表板，成本预警机制 |
| 3-4 | **安全规则扩展** | SQLGuardian | P1 | 正则黑名单配置，动态白名单管理 |
| 3-5 | **CI/CD流水线** | NuWa | P2 | GitHub Actions自动化构建和测试 |

### 3-1 UI精炼详细设计

```javascript
// 前端架构
frontend/
├── src/
│   ├── components/
│   │   ├── QueryInput.jsx      // 自然语言输入组件
│   │   ├── SQLDisplay.jsx      // SQL展示和编辑
│   │   ├── ResultTable.jsx     // 结果表格展示
│   │   └── MetricsDashboard.jsx // 性能指标面板
│   ├── i18n/
│   │   ├── zh-CN.json
│   │   └── en-US.json
│   └── services/
│       └── text2sql-api.js
```

### 3-2 自修复策略配置

```json
{
  "auto_fix_config": {
    "max_retry_attempts": 3,
    "retry_backoff": "exponential",
    "error_categories": {
      "syntax_error": {
        "strategy": "ast_repair",
        "confidence_threshold": 0.8
      },
      "column_not_found": {
        "strategy": "schema_fuzzy_match",
        "similarity_threshold": 0.7
      },
      "timeout": {
        "strategy": "query_optimization",
        "add_limit": true
      }
    }
  }
}
```

## 🚀 Week-4 计划（性能与稳定性）

### 时间线：2025-06-25 至 2025-07-01

| 任务ID | 任务名称 | 负责角色 | 优先级 | 交付标准 |
|--------|----------|----------|--------|----------|
| 4-1 | **缓存层优化** | SchemaSage | P0 | Redis LRU缓存，命中率>60% |
| 4-2 | **高并发压测** | MetricsWatcher | P0 | 200 QPS稳定运行，错误率<1% |
| 4-3 | **SLA告警系统** | NuWa + MetricsWatcher | P1 | PagerDuty集成，分级告警 |
| 4-4 | **运维文档** | QueryScribe | P1 | 完整的DevOps Runbook |

### 4-1 缓存架构

```yaml
cache_layers:
  L1_memory:
    type: "in-process"
    ttl: 300  # 5分钟
    max_size: 100MB
  
  L2_redis:
    type: "redis"
    ttl: 3600  # 1小时
    eviction: "LRU"
    
  cache_keys:
    - schema_vectors: "schema:v1:{table_name}"
    - query_results: "result:{query_hash}"
    - sql_templates: "template:{intent_type}"
```

### 4-2 性能基准

```yaml
performance_targets:
  latency:
    p50: 3s
    p95: 5s
    p99: 8s
  
  throughput:
    sustained: 100 QPS
    peak: 200 QPS
    
  resource_limits:
    cpu: 4 cores
    memory: 8GB
    connections: 1000
```

## 📊 关键指标追踪

### Week-3 验收标准
- [ ] UI可用性测试通过率 > 90%
- [ ] 自修复成功率提升至 80%
- [ ] Token成本降低 20%
- [ ] 安全拦截准确率 100%

### Week-4 验收标准
- [ ] 缓存命中率 > 60%
- [ ] 200 QPS压测通过
- [ ] SLA达成率 99.9%
- [ ] 文档完整度 100%

## 🚨 风险管理

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| UI开发延期 | 中 | 高 | 提前准备模板，使用组件库 |
| 性能瓶颈 | 高 | 高 | 分阶段优化，先达100 QPS |
| 成本超支 | 中 | 中 | 设置预算告警，优化Prompt |
| 文档不全 | 低 | 中 | 边开发边记录，自动生成 |

## 🔄 每日站会模板

```markdown
### 日期：YYYY-MM-DD
**昨日完成**：
- [角色] 完成了...

**今日计划**：
- [角色] 将要...

**阻塞问题**：
- 无 / 具体问题描述

**需要协助**：
- 无 / 需要XX角色协助...
```

## 📝 交付物清单

### Week-3 交付物
1. **前端应用** `frontend-v0.2.tar.gz`
2. **配置文件** `auto-fix-config.json`
3. **成本报表** `token-usage-week3.xlsx`
4. **安全规则** `security-rules-v2.yaml`
5. **CI配置** `.github/workflows/ci.yml`

### Week-4 交付物
1. **性能报告** `performance-test-report.pdf`
2. **缓存设计** `cache-architecture.md`
3. **告警配置** `alerting-rules.yaml`
4. **运维手册** `devops-runbook-v0.9.pdf`

---

*女娲曰：谋定而后动，知止而有得。循序渐进，方成大器。*