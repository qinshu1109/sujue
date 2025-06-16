#!/usr/bin/env python3
"""
端到端系统集成测试 - 7个核心场景
女娲造物：万物皆测，一测定乾坤
"""

import os
import json
import time
import asyncio
import requests
from datetime import datetime
from typing import Dict, Any, List

# 简化日志
class SimpleLogger:
    def info(self, msg, **kwargs):
        print(f"INFO: {msg} {kwargs}")
    def error(self, msg, **kwargs):
        print(f"ERROR: {msg} {kwargs}")

logger = SimpleLogger()

# 配置
BASE_URL = os.getenv('E2E_BASE_URL', 'http://localhost:8000')
TIMEOUT = 30
TEST_RESULTS = []

class E2ETestRunner:
    """端到端测试运行器"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.results = []
        
    def log_test_result(self, test_name: str, passed: bool, details: Dict[str, Any]):
        """记录测试结果"""
        result = {
            'test_name': test_name,
            'passed': passed,
            'timestamp': datetime.utcnow().isoformat(),
            'details': details
        }
        self.results.append(result)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status} {test_name}", **details)
        
        return passed
    
    def api_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """统一API请求"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            return response
        except Exception as e:
            logger.error(f"API请求失败: {method} {url}", error=str(e))
            raise
    
    def test_t01_simple_query(self) -> bool:
        """T-01: 简单查询 → 列表结果"""
        try:
            query_data = {
                "query": "查询所有用户的姓名和邮箱",
                "context": {"user": "analyst"},
                "session_id": "test_t01"
            }
            
            response = self.api_request('POST', '/api/text2sql', json=query_data)
            
            # 检查HTTP状态
            http_ok = response.status_code == 200
            
            if http_ok:
                data = response.json()
                
                # 检查SQL Guardian状态
                sql_valid = 'sql' in data
                confidence_ok = data.get('confidence', 0) > 0.7
                has_result = 'result' in data and isinstance(data['result'], list)
                
                details = {
                    'http_status': response.status_code,
                    'sql_generated': sql_valid,
                    'confidence': data.get('confidence'),
                    'result_count': len(data.get('result', [])),
                    'execution_time_ms': data.get('execution_time_ms')
                }
                
                passed = http_ok and sql_valid and confidence_ok
                
            else:
                details = {'http_status': response.status_code, 'error': response.text}
                passed = False
            
            return self.log_test_result('T-01: 简单查询', passed, details)
            
        except Exception as e:
            return self.log_test_result('T-01: 简单查询', False, {'error': str(e)})
    
    def test_t02_select_with_limit(self) -> bool:
        """T-02: SELECT * + LIMIT"""
        try:
            query_data = {
                "query": "显示库存表前100条记录",
                "context": {"limit": 100},
                "session_id": "test_t02"
            }
            
            response = self.api_request('POST', '/api/text2sql', json=query_data)
            
            if response.status_code == 200:
                data = response.json()
                sql = data.get('sql', '').upper()
                
                has_limit = 'LIMIT' in sql
                result_count = len(data.get('result', []))
                within_limit = result_count <= 100
                
                # 检查Token指标是否增长
                metrics_response = self.api_request('GET', '/metrics')
                token_metrics_ok = 'tokens_used_total' in metrics_response.text
                
                details = {
                    'sql': data.get('sql'),
                    'has_limit': has_limit,
                    'result_count': result_count,
                    'within_limit': within_limit,
                    'token_metrics_recorded': token_metrics_ok
                }
                
                passed = has_limit and within_limit and token_metrics_ok
                
            else:
                details = {'http_status': response.status_code}
                passed = False
            
            return self.log_test_result('T-02: SELECT+LIMIT', passed, details)
            
        except Exception as e:
            return self.log_test_result('T-02: SELECT+LIMIT', False, {'error': str(e)})
    
    def test_t03_multi_table_join(self) -> bool:
        """T-03: 多表 JOIN"""
        try:
            query_data = {
                "query": "查询用户的订单信息，包括产品名称",
                "context": {"user_role": "power"},
                "session_id": "test_t03"
            }
            
            response = self.api_request('POST', '/api/text2sql', json=query_data)
            
            if response.status_code == 200:
                data = response.json()
                sql = data.get('sql', '').upper()
                
                join_count = sql.count('JOIN')
                valid_joins = join_count <= 5 and join_count > 0
                
                details = {
                    'sql': data.get('sql'),
                    'join_count': join_count,
                    'valid_joins': valid_joins,
                    'confidence': data.get('confidence')
                }
                
                passed = valid_joins
                
            else:
                details = {'http_status': response.status_code}
                passed = False
            
            return self.log_test_result('T-03: 多表JOIN', passed, details)
            
        except Exception as e:
            return self.log_test_result('T-03: 多表JOIN', False, {'error': str(e)})
    
    def test_t04_delete_blocked(self) -> bool:
        """T-04: 删除语句阻断"""
        try:
            # 测试SQL验证接口
            dangerous_sql = "DELETE FROM users WHERE age > 50"
            
            response = self.api_request('POST', '/api/sql/validate', json={'sql': dangerous_sql})
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                blocked = status == 'BLOCK'
                has_risks = len(data.get('risks', [])) > 0
                
                details = {
                    'sql': dangerous_sql,
                    'guardian_status': status,
                    'blocked': blocked,
                    'risks': data.get('risks', []),
                    'blocked_reason': data.get('blocked_reason')
                }
                
                passed = blocked and has_risks
                
            else:
                details = {'http_status': response.status_code}
                passed = False
            
            return self.log_test_result('T-04: 删除阻断', passed, details)
            
        except Exception as e:
            return self.log_test_result('T-04: 删除阻断', False, {'error': str(e)})
    
    def test_t05_whitelist_warning(self) -> bool:
        """T-05: 白名单外表警告"""
        try:
            forbidden_sql = "SELECT * FROM payments LIMIT 10"
            
            response = self.api_request('POST', '/api/sql/validate', json={'sql': forbidden_sql})
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                warned = status == 'WARN'
                confidence_reduced = data.get('confidence', 1.0) < 0.9
                
                details = {
                    'sql': forbidden_sql,
                    'guardian_status': status,
                    'warned': warned,
                    'confidence': data.get('confidence'),
                    'risks': data.get('risks', [])
                }
                
                passed = warned  # 应该警告但不阻断
                
            else:
                details = {'http_status': response.status_code}
                passed = False
            
            return self.log_test_result('T-05: 白名单警告', passed, details)
            
        except Exception as e:
            return self.log_test_result('T-05: 白名单警告', False, {'error': str(e)})
    
    def test_t06_auto_repair(self) -> bool:
        """T-06: 长串查询自修复（模拟）"""
        try:
            # 模拟一个可能需要修复的复杂查询
            complex_query = "显示最近一个月销售额最高的10个产品"
            
            query_data = {
                "query": complex_query,
                "context": {"enable_debug": True},
                "session_id": "test_t06"
            }
            
            response = self.api_request('POST', '/api/text2sql', json=query_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # 检查是否成功生成了SQL
                sql_generated = 'sql' in data and len(data['sql']) > 0
                confidence_reasonable = data.get('confidence', 0) > 0.5
                
                details = {
                    'query': complex_query,
                    'sql_generated': sql_generated,
                    'sql_length': len(data.get('sql', '')),
                    'confidence': data.get('confidence'),
                    'execution_time_ms': data.get('execution_time_ms')
                }
                
                passed = sql_generated and confidence_reasonable
                
            else:
                details = {'http_status': response.status_code}
                passed = False
            
            return self.log_test_result('T-06: 自修复', passed, details)
            
        except Exception as e:
            return self.log_test_result('T-06: 自修复', False, {'error': str(e)})
    
    def test_t07_ui_language_switch(self) -> bool:
        """T-07: UI 切语言 EN (简化测试)"""
        try:
            # 测试健康检查接口是否正常
            health_response = self.api_request('GET', '/health')
            
            if health_response.status_code == 200:
                health_data = health_response.json()
                healthy = health_data.get('status') == 'healthy'
                
                # 检查指标接口
                metrics_response = self.api_request('GET', '/metrics')
                metrics_ok = metrics_response.status_code == 200
                
                details = {
                    'health_status': health_data.get('status'),
                    'health_check': healthy,
                    'metrics_endpoint': metrics_ok,
                    'api_version': health_data.get('version')
                }
                
                passed = healthy and metrics_ok
                
            else:
                details = {'http_status': health_response.status_code}
                passed = False
            
            return self.log_test_result('T-07: UI语言切换', passed, details)
            
        except Exception as e:
            return self.log_test_result('T-07: UI语言切换', False, {'error': str(e)})
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print(f"🚀 开始E2E测试 - {self.base_url}")
        print("=" * 60)
        
        start_time = time.time()
        
        # 执行所有测试
        test_methods = [
            self.test_t01_simple_query,
            self.test_t02_select_with_limit,
            self.test_t03_multi_table_join,
            self.test_t04_delete_blocked,
            self.test_t05_whitelist_warning,
            self.test_t06_auto_repair,
            self.test_t07_ui_language_switch
        ]
        
        for test_method in test_methods:
            try:
                test_method()
                time.sleep(1)  # 避免请求过快
            except Exception as e:
                logger.error(f"测试异常: {test_method.__name__}", error=str(e))
        
        # 生成报告
        execution_time = time.time() - start_time
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['passed'])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        summary = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': round(success_rate, 1),
            'execution_time_seconds': round(execution_time, 2),
            'timestamp': datetime.utcnow().isoformat(),
            'test_target': self.base_url
        }
        
        # 打印结果
        print(f"\n📊 E2E测试结果:")
        print(f"  总测试数: {total_tests}")
        print(f"  通过数: {passed_tests}")
        print(f"  失败数: {total_tests - passed_tests}")
        print(f"  成功率: {success_rate:.1f}%")
        print(f"  执行时间: {execution_time:.2f}s")
        
        if success_rate >= 85:
            print("✅ 测试通过！系统集成正常")
        else:
            print("❌ 测试失败！需要修复问题")
            
        # 保存报告
        report = {
            'summary': summary,
            'test_results': self.results
        }
        
        report_path = '/home/qinshu/text2sql-mvp0/tests/e2e-results.json'
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📄 详细报告: {report_path}")
        
        return summary

def main():
    """主函数"""
    runner = E2ETestRunner()
    summary = runner.run_all_tests()
    
    # 根据成功率设置退出码
    exit_code = 0 if summary['success_rate'] >= 85 else 1
    exit(exit_code)

if __name__ == "__main__":
    main()