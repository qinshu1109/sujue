# Week-2 紧急执行指南

> **目标**：在48小时窗口内完成B-1/B-2/B-3阻塞清理，确保项目自动流转至Week-3
> 
> **编写时间**：2025-06-16 19:30  
> **作者**：NuWa 智能项目经理

---

## 🚀 快速开始

```bash
# 一键启动所有修复任务
cd ~/text2sql-mvp0
./scripts/emergency-executor.sh
```

---

## 📋 脚本功能一览

| 脚本 | 功能 | 负责角色 | 执行时机 |
|------|------|----------|----------|
| `fix-deployment.sh` | 修复Podman网络&权限 | FrontEndBot | 0-6小时 |
| `inject-test-data.py` | 注入Mock测试数据 | SchemaSage | 0-6小时 |
| `update-grafana.sh` | 配置监控面板 | ExporterGuru | 6-18小时 |
| `week2-test-runner.py` | 执行T-01~T-07测试 | CIOrchestrator | 6-18小时 |
| `blocker-resolution-status.py` | 实时进度监控 | NuWa | 每6小时 |

---

## ⏰ 48小时执行时间线

### 第一阶段 (0-6小时) 🔴 最高优先级
- **19:30-01:30** FrontEndBot执行部署修复
- **20:00-22:00** SchemaSage并行注入测试数据

### 第二阶段 (6-18小时) 🟡 高优先级
- **01:30-05:30** CIOrchestrator运行验收测试
- **05:30-13:30** ExporterGuru配置可观测性

### 第三阶段 (18-36小时) 🟢 验证阶段
- **13:30-07:30(次日)** 集成测试与性能验证
- 每6小时NuWa检查进度

### 第四阶段 (36-48小时) ✅ 收尾阶段
- **07:30-19:30** 最终验证与进入Week-3

---

## ✅ 成功判定标准

### 1. 部署验证 (B-1)
```bash
# 检查命令
podman ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 预期结果
- 5个容器状态为 healthy
- 端口映射：8000, 5432, 9090, 9101, 3000
```

### 2. 测试执行 (B-2)
```bash
# 查看测试报告
cat logs/week2_test_report.json | jq '.summary'

# 成功标准
- 通过率 ≥ 95%
- 失败用例 ≤ 1个
```

### 3. 可观测性 (B-3)
```bash
# 验证Prometheus抓取
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job:.labels.job, health:.health}'

# Grafana面板检查
- 打开 http://localhost:3000
- 用户名/密码: admin/admin123
- 验证 "PromptX Overview" 数据完整
```

---

## 🚨 风险处理方案

### R-4: 权限问题
```bash
# 自动检测并切换模式
if podman info | grep -q "rootless: true"; then
    ./scripts/fix-deployment.sh --rootless
else
    sudo ./scripts/fix-deployment.sh
fi
```

### R-5: 数据冲突
```bash
# 清理旧数据
rm -f tests/test_data.db
python3 scripts/inject-test-data.py --force
```

### R-6: 端口占用
```bash
# 检查端口占用
lsof -i :9101 || echo "端口可用"

# 如占用，改用备用端口
export EXPORTER_PORT=9102
```

---

## 📊 实时监控命令

```bash
# 查看执行日志
tail -f logs/emergency-execution.log

# 检查阻塞状态
watch -n 300 "python3 scripts/blocker-resolution-status.py"

# 查看进度百分比
python3 -c "
import json
from pathlib import Path
status_files = list(Path('promptx/memory').glob('blocker-*-status.json'))
resolved = sum(1 for f in status_files if json.loads(f.read_text()).get('status') == 'resolved')
print(f'进度: {resolved}/3 ({resolved/3*100:.0f}%)')
"
```

---

## 🔔 告警触发条件

- **ERROR关键字**：日志中出现ERROR立即发送Slack
- **18小时检查点**：B-1/B-2未完成发红色警报
- **36小时检查点**：测试通过率<85%触发紧急会议
- **磁盘空间**：剩余<1GB自动清理日志

---

## 📞 紧急联系

- **技术问题**：触发@Debugger角色
- **进度延迟**：NuWa自动调整计划
- **资源不足**：MetricsWatcher提供优化建议

---

## 🎯 最终目标

**2025-06-18 19:30前**：
- [ ] 所有容器运行正常
- [ ] 测试通过率≥95%
- [ ] 监控数据流畅
- [ ] 自动更新project_stage="W3_in_progress"

---

*女娲曰：时不我待，立即行动！48小时内必达目标！*