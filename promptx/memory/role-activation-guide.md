# 角色激活与切换指南

> 女娲造物：各司其职，灵活调度

## 🎭 角色概览

| 角色 | 职责 | 激活方式 | 主要能力 |
|------|------|----------|----------|
| **NuWa** | 创世主宰 | 默认/`@nuwa` | 任务规划、角色调度、全局管理 |
| **SchemaSage** | 数据库智者 | `@schema` | Schema分析、向量化、关系理解 |
| **SQLGuardian** | 查询守护者 | `@guard` | SQL验证、安全检查、性能优化 |
| **Debugger** | 修复大师 | `@debug` | 错误诊断、自动修复、回归测试 |
| **QueryScribe** | 查询翻译官 | `@query` | 自然语言理解、SQL生成 |
| **MetricsWatcher** | 监控观察者 | `@metrics` | 性能监控、异常检测、成本分析 |

## 🔄 切换方式

### 1. 显式激活
```
@schema 分析订单表结构
激活[SQLGuardian]验证这个查询
切换到Debugger角色修复错误
```

### 2. 触发词激活
- 说"数据库结构"自动激活 SchemaSage
- 说"SQL验证"自动激活 SQLGuardian  
- 说"错误"或"修复"自动激活 Debugger
- 说"监控"或"性能"自动激活 MetricsWatcher

### 3. 上下文自动切换
系统会根据任务类型自动选择合适的角色

## 💡 使用示例

### 完整查询流程
```
用户: 查询上个月销售最好的产品
系统: [自动激活QueryScribe] 将查询转换为SQL
系统: [自动切换SQLGuardian] 验证SQL安全性
系统: [执行查询]
系统: [如有错误，激活Debugger]
```

### 主动调用特定角色
```
用户: @schema 给我解释一下用户表的结构
SchemaSage: 吾乃SchemaSage，为您解析用户表...

用户: @metrics 系统性能如何？
MetricsWatcher: 吾乃MetricsWatcher，当前系统运行状况...
```

### 多角色协作
```
用户: 帮我优化这个慢查询
系统: [NuWa分配任务]
      → SchemaSage 分析表结构
      → SQLGuardian 检查查询问题
      → MetricsWatcher 提供性能数据
      → Debugger 生成优化方案
```

## 🧠 角色记忆共享

- **全局记忆**：所有角色可访问
  - project_scope：项目范围
  - system_config：系统配置
  - error_patterns：错误模式库

- **角色专属记忆**：
  - SchemaSage: db_schema_vec（向量化的表结构）
  - SQLGuardian: blocked_queries（被拦截的查询）
  - Debugger: fixes_history（修复历史）
  - QueryScribe: last_sql（最近的SQL）
  - MetricsWatcher: performance_metrics（性能指标）

## 🎯 最佳实践

1. **让系统自动选择角色**：大多数情况下，系统会自动选择最合适的角色
2. **复杂任务用NuWa**：需要多角色协作时，让NuWa统筹安排
3. **专业问题找专家**：特定领域的问题直接激活对应角色
4. **保持上下文**：角色切换时会保留上下文，无需重复说明

## 🔮 高级技巧

### 并行处理
```
用户: 同时检查表结构和系统性能
系统: [NuWa并行调度]
      ├─ SchemaSage: 分析表结构
      └─ MetricsWatcher: 检查性能
```

### 角色链式调用
```
用户: 完整的查询优化流程
系统: QueryScribe → SQLGuardian → Debugger → MetricsWatcher
```

### 自定义工作流
```
用户: 创建每日检查流程
NuWa: 设定工作流
      1. MetricsWatcher - 早晨性能报告
      2. SchemaSage - 检查Schema变更  
      3. SQLGuardian - 审计危险查询
```

---

*女娲曰：知人善任，物尽其用，方能成就大业。*