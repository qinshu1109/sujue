#!/usr/bin/env python3
"""
SQLGuardian 白名单热加载测试脚本
女娲造物：守护数据，如臂使指
"""

import os
import time
import yaml
import requests
import json
from datetime import datetime

class SecurityHotReloadTester:
    def __init__(self):
        self.config_path = "/home/qinshu/text2sql-mvp0/config/security/allowed_tables.yml"
        self.api_base = "http://localhost:8000"
        self.test_results = []
        
    def load_current_config(self):
        """加载当前配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"❌ 配置加载失败: {e}")
            return None
    
    def modify_config(self, new_tables):
        """修改配置文件"""
        try:
            config = self.load_current_config()
            if not config:
                return False
                
            # 备份原配置
            self.original_config = config.copy()
            
            # 修改白名单
            config['allowed_tables'] = new_tables
            config['last_updated'] = datetime.utcnow().isoformat() + "Z"
            
            # 写入文件
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            print(f"✅ 配置已更新: {new_tables}")
            return True
            
        except Exception as e:
            print(f"❌ 配置修改失败: {e}")
            return False
    
    def restore_config(self):
        """恢复原配置"""
        try:
            if hasattr(self, 'original_config'):
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(self.original_config, f, default_flow_style=False, allow_unicode=True)
                print("🔄 配置已恢复")
        except Exception as e:
            print(f"❌ 配置恢复失败: {e}")
    
    def test_sql_validation(self, sql, expected_status):
        """测试SQL验证"""
        try:
            response = requests.post(f"{self.api_base}/api/sql/validate", 
                json={"sql": sql},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                actual_status = result.get('status', 'UNKNOWN')
                
                test_result = {
                    'sql': sql[:50] + '...' if len(sql) > 50 else sql,
                    'expected': expected_status,
                    'actual': actual_status,
                    'passed': actual_status == expected_status,
                    'timestamp': datetime.now().isoformat()
                }
                
                self.test_results.append(test_result)
                
                status_icon = "✅" if test_result['passed'] else "❌"
                print(f"{status_icon} SQL验证: {sql[:30]}... -> {actual_status}")
                
                return test_result['passed']
                
            else:
                print(f"❌ API调用失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            return False
    
    def run_hotreload_test(self):
        """执行热加载测试"""
        print("🔥 开始 SQLGuardian 白名单热加载测试")
        print("=" * 60)
        
        # 1. 测试初始状态
        print("\n📋 阶段1: 测试初始白名单")
        initial_tests = [
            ("SELECT * FROM users", "PASS"),          # 白名单表
            ("SELECT * FROM products", "PASS"),       # 白名单表  
            ("SELECT * FROM forbidden_table", "WARN"), # 非白名单表
        ]
        
        for sql, expected in initial_tests:
            time.sleep(1)  # 避免请求过快
            self.test_sql_validation(sql, expected)
        
        # 2. 修改配置 - 移除users表
        print("\n🔧 阶段2: 修改配置 - 移除users表")
        if self.modify_config(['products', 'orders', 'categories']):
            time.sleep(3)  # 等待热加载生效
            
            # 测试配置是否生效
            hotreload_tests = [
                ("SELECT * FROM users", "WARN"),         # 应该被警告
                ("SELECT * FROM products", "PASS"),      # 仍在白名单
                ("SELECT * FROM orders", "PASS"),        # 仍在白名单
            ]
            
            for sql, expected in hotreload_tests:
                time.sleep(1)
                self.test_sql_validation(sql, expected)
        
        # 3. 再次修改配置 - 添加新表
        print("\n🔧 阶段3: 添加新表到白名单")
        if self.modify_config(['products', 'orders', 'categories', 'new_table', 'users']):
            time.sleep(3)  # 等待热加载生效
            
            # 测试新配置
            new_config_tests = [
                ("SELECT * FROM users", "PASS"),         # 重新允许
                ("SELECT * FROM new_table", "PASS"),     # 新添加的表
                ("SELECT * FROM forbidden_table", "WARN"), # 仍然禁止
            ]
            
            for sql, expected in new_config_tests:
                time.sleep(1)
                self.test_sql_validation(sql, expected)
        
        # 4. 恢复原配置
        print("\n🔄 阶段4: 恢复原配置")
        self.restore_config()
        time.sleep(3)
        
        # 验证恢复
        restore_tests = [
            ("SELECT * FROM users", "PASS"),
            ("SELECT * FROM products", "PASS"),
        ]
        
        for sql, expected in restore_tests:
            time.sleep(1)
            self.test_sql_validation(sql, expected)
        
        # 5. 生成报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print("\n📊 测试报告")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for t in self.test_results if t['passed'])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"总测试数: {total_tests}")
        print(f"通过数: {passed_tests}")
        print(f"成功率: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("✅ 热加载功能正常！")
        else:
            print("❌ 热加载功能异常！")
            
        # 保存详细报告
        report = {
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'success_rate': success_rate,
                'timestamp': datetime.now().isoformat()
            },
            'details': self.test_results
        }
        
        report_path = "/home/qinshu/text2sql-mvp0/logs/security-hotreload-test.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📄 详细报告已保存: {report_path}")
        
        return success_rate >= 80

def main():
    """主函数"""
    tester = SecurityHotReloadTester()
    
    try:
        success = tester.run_hotreload_test()
        exit_code = 0 if success else 1
        print(f"\n🎯 测试完成，退出码: {exit_code}")
        exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        tester.restore_config()
        exit(1)
    except Exception as e:
        print(f"\n💥 测试异常: {e}")
        tester.restore_config()
        exit(1)

if __name__ == "__main__":
    main()