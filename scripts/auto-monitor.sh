#!/bin/bash
# 自动监控脚本 - NuWa每6小时执行
# 实时追踪阻塞解决进度并自动响应

set -e

PROJECT_ROOT="$(cd "$(dirname "$(dirname "${BASH_SOURCE[0]}")")" && pwd)"
MEMORY_PATH="$PROJECT_ROOT/promptx/memory"
LOG_FILE="$PROJECT_ROOT/logs/auto-monitor.log"

# 创建日志目录
mkdir -p "$PROJECT_ROOT/logs"

# ANSI颜色代码
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 检查单个阻塞项状态
check_blocker() {
    local blocker_id=$1
    local status_file="$MEMORY_PATH/blocker-${blocker_id}-status.json"
    
    if [ -f "$status_file" ]; then
        local status=$(python3 -c "import json; print(json.load(open('$status_file'))['status'])")
        echo "$status"
    else
        echo "pending"
    fi
}

# 计算进度
calculate_progress() {
    local b1_status=$(check_blocker "B-1")
    local b2_status=$(check_blocker "B-2")
    local b3_status=$(check_blocker "B-3")
    
    local resolved=0
    [ "$b1_status" = "resolved" ] && ((resolved++))
    [ "$b2_status" = "resolved" ] && ((resolved++))
    [ "$b3_status" = "resolved" ] && ((resolved++))
    
    echo $((resolved * 100 / 3))
}

# 发送告警（模拟）
send_alert() {
    local level=$1
    local message=$2
    
    log "${level}警报: $message"
    
    # 这里可以集成实际的告警系统
    # curl -X POST https://hooks.slack.com/services/xxx \
    #   -H 'Content-type: application/json' \
    #   --data "{\"text\":\"$level: $message\"}"
}

# 自动修复动作
auto_fix_action() {
    local blocker=$1
    
    case $blocker in
        "B-1")
            log "触发B-1自动修复..."
            if [ -f "$PROJECT_ROOT/scripts/fix-deployment.sh" ]; then
                bash "$PROJECT_ROOT/scripts/fix-deployment.sh" --auto-retry >> "$LOG_FILE" 2>&1 || true
            fi
            ;;
        "B-2")
            log "触发B-2自动修复..."
            if [ -f "$PROJECT_ROOT/scripts/inject-test-data.py" ]; then
                python3 "$PROJECT_ROOT/scripts/inject-test-data.py" --force >> "$LOG_FILE" 2>&1 || true
            fi
            ;;
        "B-3")
            log "触发B-3自动修复..."
            # 自动更新Grafana配置
            if [ -f "$PROJECT_ROOT/scripts/update-grafana.sh" ]; then
                bash "$PROJECT_ROOT/scripts/update-grafana.sh" >> "$LOG_FILE" 2>&1 || true
            fi
            ;;
    esac
}

# 主监控逻辑
main() {
    log "=========================================="
    log "🔍 NuWa自动监控开始"
    log "=========================================="
    
    # 获取当前时间和开始时间的差值（小时）
    START_TIME="2025-06-16T19:30:00"
    CURRENT_TIME=$(date -u +%s)
    START_TIMESTAMP=$(date -d "$START_TIME" +%s 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%S" "$START_TIME" +%s)
    HOURS_ELAPSED=$(( (CURRENT_TIME - START_TIMESTAMP) / 3600 ))
    
    log "执行时间: 已过${HOURS_ELAPSED}小时"
    
    # 检查各阻塞项状态
    log ""
    log "📋 阻塞项状态检查:"
    
    B1_STATUS=$(check_blocker "B-1")
    B2_STATUS=$(check_blocker "B-2")
    B3_STATUS=$(check_blocker "B-3")
    
    # 状态显示
    display_status() {
        local blocker=$1
        local status=$2
        local icon="⏳"
        local color=$YELLOW
        
        case $status in
            "resolved")
                icon="✅"
                color=$GREEN
                ;;
            "in_progress")
                icon="🔄"
                color=$BLUE
                ;;
            "failed")
                icon="❌"
                color=$RED
                ;;
        esac
        
        echo -e "${color}$blocker: $icon $status${NC}"
    }
    
    display_status "B-1 部署验证" "$B1_STATUS"
    display_status "B-2 测试执行" "$B2_STATUS"
    display_status "B-3 可观测性" "$B3_STATUS"
    
    # 计算总体进度
    PROGRESS=$(calculate_progress)
    log ""
    log "📊 总体进度: ${PROGRESS}%"
    
    # 进度条显示
    FILLED=$((PROGRESS / 5))
    EMPTY=$((20 - FILLED))
    PROGRESS_BAR=$(printf '█%.0s' $(seq 1 $FILLED))$(printf '░%.0s' $(seq 1 $EMPTY))
    echo -e "${GREEN}[$PROGRESS_BAR]${NC} ${PROGRESS}%"
    
    # 时间检查点判断
    if [ $HOURS_ELAPSED -ge 18 ] && [ $HOURS_ELAPSED -lt 24 ]; then
        log ""
        log "⏰ 18小时检查点"
        if [ "$B1_STATUS" != "resolved" ] || [ "$B2_STATUS" != "resolved" ]; then
            send_alert "🔴 红色" "B-1或B-2未在18小时内完成！"
            # 触发自动修复
            [ "$B1_STATUS" != "resolved" ] && auto_fix_action "B-1"
            [ "$B2_STATUS" != "resolved" ] && auto_fix_action "B-2"
        fi
    elif [ $HOURS_ELAPSED -ge 36 ] && [ $HOURS_ELAPSED -lt 42 ]; then
        log ""
        log "⏰ 36小时检查点"
        # 检查测试通过率
        if [ -f "$PROJECT_ROOT/logs/week2_test_report.json" ]; then
            PASS_RATE=$(python3 -c "import json; report=json.load(open('$PROJECT_ROOT/logs/week2_test_report.json')); print(report['summary']['pass_rate'].strip('%'))")
            if [ "$PASS_RATE" -lt 85 ]; then
                send_alert "🟡 黄色" "测试通过率仅${PASS_RATE}%，低于85%目标"
            fi
        fi
    elif [ $HOURS_ELAPSED -ge 48 ]; then
        log ""
        log "⏰ 48小时最终检查"
        if [ $PROGRESS -eq 100 ]; then
            log "🎉 所有阻塞项已解决！"
            # 自动更新项目阶段
            python3 "$PROJECT_ROOT/scripts/phase-gate-executor.py" --auto-proceed
        else
            send_alert "🔴 红色" "48小时期限已到，仍有阻塞未解决"
        fi
    fi
    
    # 资源检查
    log ""
    log "💾 系统资源检查:"
    
    # 磁盘空间
    DISK_USAGE=$(df -h "$PROJECT_ROOT" | awk 'NR==2 {print $5}' | sed 's/%//')
    DISK_AVAILABLE=$(df -BG "$PROJECT_ROOT" | awk 'NR==2 {print $4}' | sed 's/G//')
    
    if [ $DISK_USAGE -gt 90 ] || [ $DISK_AVAILABLE -lt 2 ]; then
        send_alert "⚠️ 警告" "磁盘空间不足！使用率${DISK_USAGE}%，剩余${DISK_AVAILABLE}GB"
        # 自动清理
        find "$PROJECT_ROOT/logs" -name "*.log" -mtime +7 -delete
        log "已清理7天前的日志文件"
    else
        log "磁盘空间正常: 使用${DISK_USAGE}%，剩余${DISK_AVAILABLE}GB"
    fi
    
    # 下一步建议
    log ""
    log "💡 下一步建议:"
    
    if [ "$B1_STATUS" != "resolved" ]; then
        log "- 优先解决B-1部署问题，执行: ./scripts/fix-deployment.sh"
    fi
    
    if [ "$B2_STATUS" != "resolved" ]; then
        log "- 解决B-2测试数据问题，执行: python3 ./scripts/inject-test-data.py"
    fi
    
    if [ "$B3_STATUS" != "resolved" ]; then
        log "- 配置监控系统，联系ExporterGuru角色"
    fi
    
    if [ $PROGRESS -eq 100 ]; then
        log "- 所有阻塞已清除，准备进入Week-3阶段"
    fi
    
    # 保存监控报告
    REPORT_FILE="$MEMORY_PATH/monitor_report_$(date +%Y%m%d_%H%M).json"
    cat > "$REPORT_FILE" << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "hours_elapsed": $HOURS_ELAPSED,
  "progress_percentage": $PROGRESS,
  "blockers": {
    "B-1": "$B1_STATUS",
    "B-2": "$B2_STATUS",
    "B-3": "$B3_STATUS"
  },
  "disk_usage": $DISK_USAGE,
  "next_check": "$(date -d '+6 hours' -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
    
    log ""
    log "📄 监控报告已保存: $REPORT_FILE"
    log "下次检查时间: $(date -d '+6 hours' '+%Y-%m-%d %H:%M:%S')"
}

# 运行主函数
main

# 如果是持续监控模式
if [ "$1" = "--daemon" ]; then
    while true; do
        sleep 21600  # 6小时
        main
    done
fi