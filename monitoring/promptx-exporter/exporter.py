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
