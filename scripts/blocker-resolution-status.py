#!/usr/bin/env python3
"""
阻塞项解决状态追踪器
NuWa实时监控48小时解决计划进展
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

class BlockerTracker:
    """阻塞项追踪器"""
    
    def __init__(self):
        self.project_root = Path("/home/qinshu/text2sql-mvp0")
        self.memory_path = self.project_root / "promptx/memory"
        self.start_time = datetime.fromisoformat("2025-06-16T12:00:00")
        
    def load_resolution_plan(self) -> Dict:
        """加载解决计划"""
        plan_file = self.memory_path / "blocker-resolution-plan.json"
        with open(plan_file, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    def check_blocker_status(self, blocker_id: str) -> Dict:
        """检查单个阻塞项状态"""
        status_file = self.memory_path / f"blocker-{blocker_id}-status.json"
        
        if status_file.exists():
            with open(status_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {"status": "pending"}
            
    def calculate_time_remaining(self, deadline_hours: int) -> str:
        """计算剩余时间"""
        deadline = self.start_time + timedelta(hours=deadline_hours)
        now = datetime.now()
        
        if now > deadline:
            return "已超时"
        else:
            remaining = deadline - now
            hours = int(remaining.total_seconds() // 3600)
            minutes = int((remaining.total_seconds() % 3600) // 60)
            return f"{hours}小时{minutes}分钟"
            
    def generate_status_report(self):
        """生成状态报告"""
        plan = self.load_resolution_plan()
        
        print("="*80)
        print("🎯 阻塞项解决状态报告")
        print(f"报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"计划开始: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # 检查三大阻塞项
        print("\n📋 阻塞项状态:")
        print("-"*60)
        
        blockers_resolved = 0
        for blocker_id, blocker_info in plan['blockers'].items():
            status = self.check_blocker_status(blocker_id)
            
            status_icon = {
                "resolved": "✅",
                "partially_resolved": "🟨",
                "in_progress": "🔄",
                "pending": "⏳"
            }.get(status.get('status', 'pending'), '❓')
            
            print(f"\n{blocker_id}: {blocker_info['name']}")
            print(f"状态: {status_icon} {status.get('status', 'pending')}")
            print(f"影响: {blocker_info['impact']}")
            
            if status.get('status') == 'resolved':
                blockers_resolved += 1
                print(f"解决时间: {status.get('resolved_at', 'N/A')}")
                print(f"解决者: {status.get('resolved_by', 'N/A')}")
                
        # 检查行动项进展
        print("\n\n📊 行动项进展:")
        print("-"*60)
        
        actions_completed = 0
        for action in plan['action_plan']:
            action_id = action['id']
            deadline_hours = action['deadline_hours']
            time_remaining = self.calculate_time_remaining(deadline_hours)
            
            # 检查是否有对应的状态更新
            action_status = "pending"
            for blocker_id in ['B-1', 'B-2', 'B-3']:
                blocker_status = self.check_blocker_status(blocker_id)
                if action['action'] in str(blocker_status.get('actions_taken', [])):
                    action_status = "completed"
                    actions_completed += 1
                    break
                    
            status_icon = "✅" if action_status == "completed" else "⏳"
            
            print(f"\n{action_id}: {action['action']}")
            print(f"  负责: {', '.join(action['responsible_roles'])}")
            print(f"  期限: {deadline_hours}小时 (剩余: {time_remaining})")
            print(f"  状态: {status_icon} {action_status}")
            
        # 总体进度
        print("\n\n📈 总体进度:")
        print("-"*60)
        
        total_blockers = len(plan['blockers'])
        total_actions = len(plan['action_plan'])
        
        blocker_progress = (blockers_resolved / total_blockers) * 100
        action_progress = (actions_completed / total_actions) * 100
        overall_progress = (blocker_progress + action_progress) / 2
        
        print(f"阻塞项解决: {blockers_resolved}/{total_blockers} ({blocker_progress:.1f}%)")
        print(f"行动项完成: {actions_completed}/{total_actions} ({action_progress:.1f}%)")
        print(f"总体进度: {overall_progress:.1f}%")
        
        # 进度条
        bar_length = 50
        filled_length = int(bar_length * overall_progress / 100)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        print(f"\n[{bar}] {overall_progress:.1f}%")
        
        # 风险提示
        print("\n\n⚠️  风险提示:")
        print("-"*60)
        
        if overall_progress < 50 and datetime.now() > self.start_time + timedelta(hours=24):
            print("🔴 进度严重滞后！需要立即采取行动")
        elif overall_progress < 75 and datetime.now() > self.start_time + timedelta(hours=36):
            print("🟡 进度有所延迟，请加快执行速度")
        else:
            print("🟢 进度正常")
            
        # 下一步建议
        print("\n\n💡 下一步建议:")
        print("-"*60)
        
        if blockers_resolved < total_blockers:
            pending_blockers = [
                bid for bid in plan['blockers']
                if self.check_blocker_status(bid).get('status') != 'resolved'
            ]
            print(f"优先解决阻塞项: {', '.join(pending_blockers)}")
            
        # 保存报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "blockers_resolved": blockers_resolved,
            "actions_completed": actions_completed,
            "overall_progress": overall_progress,
            "risk_level": "high" if overall_progress < 50 else "medium" if overall_progress < 75 else "low"
        }
        
        report_file = self.memory_path / f"resolution_status_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        print(f"\n📄 报告已保存至: {report_file}")
        
        return overall_progress >= 100
        
    def trigger_next_actions(self):
        """触发下一步行动"""
        plan = self.load_resolution_plan()
        
        # 检查是否所有阻塞项都已解决
        all_resolved = all(
            self.check_blocker_status(bid).get('status') == 'resolved'
            for bid in plan['blockers']
        )
        
        if all_resolved:
            print("\n\n🎉 所有阻塞项已解决！")
            print("正在更新项目阶段至Week-3...")
            
            # 更新project_scope
            scope_file = self.memory_path / "project_scope.json"
            with open(scope_file, 'r', encoding='utf-8') as f:
                scope = json.load(f)
                
            scope['milestones']['W2']['status'] = 'completed'
            scope['milestones']['W3']['status'] = 'in_progress'
            scope['current_stage'] = 'W3'
            scope['phase_gate_passed'] = datetime.now().isoformat()
            
            with open(scope_file, 'w', encoding='utf-8') as f:
                json.dump(scope, f, ensure_ascii=False, indent=2)
                
            print("✅ 项目已进入Week-3阶段！")
            print("\n启动Week-3任务分配...")
            
            # 这里可以触发Week-3的任务分配逻辑
            
def main():
    tracker = BlockerTracker()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--check-only':
        # 仅检查状态
        tracker.generate_status_report()
    else:
        # 生成报告并触发行动
        all_resolved = tracker.generate_status_report()
        if all_resolved:
            tracker.trigger_next_actions()
            
    print("\n女娲曰：监控不懈，方能及时应变。")

if __name__ == "__main__":
    main()