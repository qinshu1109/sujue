"""
角色切换器 - 女娲智能角色管理系统
实现灵活的角色切换和任务分配
"""

import json
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

class RoleSwitcher:
    """角色切换管理器"""
    
    def __init__(self, config_path: str = "/app/promptx/core/role-manager.json"):
        self.config_path = Path(config_path)
        self.current_role = "NuWa"
        self.role_config = self._load_config()
        self.context_history = []
        self.shared_memory = {}
        
    def _load_config(self) -> Dict:
        """加载角色配置"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def detect_role_from_input(self, user_input: str) -> Optional[str]:
        """从用户输入检测应该激活的角色"""
        # 1. 检查显式激活
        explicit_pattern = r'@(\w+)|激活\[(\w+)\]|切换到(\w+)角色'
        match = re.search(explicit_pattern, user_input)
        if match:
            role_name = match.group(1) or match.group(2) or match.group(3)
            if role_name in self.role_config.get('roles', {}):
                return role_name
        
        # 2. 基于触发词检测
        for role_name, role_info in self.role_config.get('roles', {}).items():
            triggers = role_info.get('triggers', [])
            for trigger in triggers:
                if trigger.lower() in user_input.lower():
                    return role_name
        
        # 3. 基于上下文检测
        context_triggers = self.role_config.get('role_switching_rules', {}).get('activation_methods', [])[1].get('triggers', {})
        for category, keywords in context_triggers.items():
            for keyword in keywords:
                if keyword in user_input:
                    # 映射到对应角色
                    role_mapping = {
                        'schema_related': 'SchemaSage',
                        'security_related': 'SQLGuardian',
                        'error_related': 'Debugger',
                        'monitoring_related': 'MetricsWatcher'
                    }
                    return role_mapping.get(category)
        
        return None
    
    def switch_role(self, target_role: str, task_context: str = "") -> Tuple[str, str]:
        """切换到目标角色"""
        if target_role not in self.role_config.get('roles', {}):
            return self.current_role, f"未知角色: {target_role}"
        
        # 生成交接信息
        handover_message = self._generate_handover(self.current_role, target_role, task_context)
        
        # 记录切换历史
        self.context_history.append({
            'timestamp': datetime.now().isoformat(),
            'from_role': self.current_role,
            'to_role': target_role,
            'context': task_context,
            'handover': handover_message
        })
        
        # 更新当前角色
        previous_role = self.current_role
        self.current_role = target_role
        
        # 获取激活提示
        activation_prompt = self.role_config['roles'][target_role].get('activation_prompt', '')
        
        return target_role, activation_prompt
    
    def _generate_handover(self, from_role: str, to_role: str, context: str) -> str:
        """生成角色交接信息"""
        if from_role == "NuWa":
            return f"女娲将任务委托给{to_role}：{context}"
        else:
            return f"{from_role}完成部分任务，现交由{to_role}继续：{context}"
    
    def get_role_tools(self, role_name: Optional[str] = None) -> List[str]:
        """获取角色可用的工具"""
        role = role_name or self.current_role
        return self.role_config.get('roles', {}).get(role, {}).get('tools', [])
    
    def get_role_capabilities(self, role_name: Optional[str] = None) -> List[str]:
        """获取角色能力列表"""
        role = role_name or self.current_role
        return self.role_config.get('roles', {}).get(role, {}).get('capabilities', [])
    
    def update_shared_memory(self, key: str, value: any):
        """更新共享记忆"""
        self.shared_memory[key] = {
            'value': value,
            'updated_by': self.current_role,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_shared_memory(self, key: str) -> Optional[any]:
        """获取共享记忆"""
        if key in self.shared_memory:
            return self.shared_memory[key]['value']
        return None
    
    def get_role_specific_memory_keys(self, role_name: Optional[str] = None) -> List[str]:
        """获取角色特定的记忆键"""
        role = role_name or self.current_role
        memory_config = self.role_config.get('memory_sharing', {})
        
        # 全局键 + 角色特定键
        global_keys = memory_config.get('global_keys', [])
        role_keys = memory_config.get('role_specific_keys', {}).get(role, [])
        
        return global_keys + role_keys
    
    def suggest_next_role(self, current_task: str, completed_tasks: List[str]) -> Optional[str]:
        """基于当前任务建议下一个角色"""
        # 实现任务流程推荐逻辑
        task_flow = {
            'nl_to_sql': ['QueryScribe', 'SQLGuardian'],
            'schema_analysis': ['SchemaSage', 'QueryScribe'],
            'error_fixing': ['Debugger', 'SQLGuardian'],
            'monitoring': ['MetricsWatcher', 'Debugger']
        }
        
        for task_type, role_sequence in task_flow.items():
            if task_type in current_task.lower():
                # 找到当前角色在序列中的位置
                if self.current_role in role_sequence:
                    current_index = role_sequence.index(self.current_role)
                    if current_index < len(role_sequence) - 1:
                        return role_sequence[current_index + 1]
        
        return None
    
    def generate_role_report(self) -> Dict:
        """生成角色使用报告"""
        role_usage = {}
        for entry in self.context_history:
            role = entry['to_role']
            if role not in role_usage:
                role_usage[role] = 0
            role_usage[role] += 1
        
        return {
            'current_role': self.current_role,
            'total_switches': len(self.context_history),
            'role_usage': role_usage,
            'last_switch': self.context_history[-1] if self.context_history else None
        }


# 单例实例
_role_switcher_instance = None

def get_role_switcher() -> RoleSwitcher:
    """获取角色切换器单例"""
    global _role_switcher_instance
    if _role_switcher_instance is None:
        _role_switcher_instance = RoleSwitcher()
    return _role_switcher_instance