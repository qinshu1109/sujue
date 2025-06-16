#!/usr/bin/env python3
"""
Mock测试服务器 - 用于E2E测试
女娲造物：以简驭繁，以虚应实
"""

import json
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
from datetime import datetime

class MockHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    """Mock HTTP请求处理器"""
    
    def do_GET(self):
        """处理GET请求"""
        if self.path == '/health':
            self.send_json_response({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'version': '0.1.0'
            })
        elif self.path == '/metrics':
            metrics_text = '''# HELP tokens_used_total Total tokens used
# TYPE tokens_used_total counter
tokens_used_total{model="claude-3-opus-20240229",type="input",endpoint="text2sql"} 1500
tokens_used_total{model="claude-3-opus-20240229",type="output",endpoint="text2sql"} 450
tokens_used_total{model="claude-3-sonnet-20240229",type="input",endpoint="validate"} 800
tokens_used_total{model="claude-3-sonnet-20240229",type="output",endpoint="validate"} 200
# HELP token_cost_usd_total Total cost in USD
# TYPE token_cost_usd_total counter
token_cost_usd_total{model="claude-3-opus-20240229",endpoint="text2sql"} 0.03375
'''
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(metrics_text.encode())
        else:
            self.send_error(404, "Not Found")
    
    def do_POST(self):
        """处理POST请求"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            request_data = json.loads(post_data.decode('utf-8'))
        except:
            request_data = {}
        
        if self.path == '/api/text2sql':
            self.handle_text2sql(request_data)
        elif self.path == '/api/sql/validate':
            self.handle_sql_validate(request_data)
        else:
            self.send_error(404, "Not Found")
    
    def handle_text2sql(self, request_data):
        """处理Text2SQL请求"""
        query = request_data.get('query', '')
        
        # 根据查询内容返回不同的模拟结果
        if '用户' in query or 'user' in query.lower():
            sql = 'SELECT name, email FROM users WHERE status = "active" ORDER BY created_at DESC'
            result = [
                {'name': '张三', 'email': 'zhang@example.com'},
                {'name': '李四', 'email': 'li@example.com'},
                {'name': '王五', 'email': 'wang@example.com'}
            ]
        elif '库存' in query or 'inventory' in query.lower():
            sql = 'SELECT * FROM inventory LIMIT 100'
            result = [
                {'product_id': i, 'product_name': f'产品{i}', 'quantity': 100-i} 
                for i in range(1, 11)
            ]
        elif '订单' in query or 'order' in query.lower():
            sql = '''SELECT u.name, o.order_id, p.product_name 
                     FROM users u 
                     JOIN orders o ON u.id = o.user_id 
                     JOIN products p ON o.product_id = p.id 
                     LIMIT 50'''
            result = [
                {'name': '用户1', 'order_id': 'ORD001', 'product_name': '产品A'},
                {'name': '用户2', 'order_id': 'ORD002', 'product_name': '产品B'}
            ]
        elif '产品' in query or 'product' in query.lower():
            sql = 'SELECT * FROM products WHERE status = "active" ORDER BY price DESC'
            result = [
                {'id': 1, 'name': '电子产品A', 'price': 999.99, 'category': '电子'},
                {'id': 2, 'name': '电子产品B', 'price': 799.99, 'category': '电子'}
            ]
        else:
            sql = 'SELECT * FROM sample_table LIMIT 10'
            result = [{'id': 1, 'data': 'sample_data'}]
        
        response = {
            'sql': sql,
            'result': result,
            'explanation': f'该查询用于{query}，已成功执行并返回{len(result)}条结果',
            'confidence': 0.95,
            'execution_time_ms': 250.5,
            'tokens_used': {
                'input': len(query) + 50,  # 模拟输入token数
                'output': len(sql) // 2    # 模拟输出token数
            }
        }
        
        self.send_json_response(response)
    
    def handle_sql_validate(self, request_data):
        """处理SQL验证请求"""
        sql = request_data.get('sql', '').upper()
        
        # SQL安全检查
        if any(keyword in sql for keyword in ['DELETE', 'DROP', 'TRUNCATE', 'INSERT', 'UPDATE']):
            response = {
                'status': 'BLOCK',
                'risks': ['CRITICAL_OPERATION detected in SQL'],
                'suggestions': [],
                'confidence': 0.0,
                'blocked_reason': 'CRITICAL_OPERATION'
            }
        elif 'PAYMENTS' in sql or 'FORBIDDEN' in sql:
            response = {
                'status': 'WARN',
                'risks': ["Table not in whitelist"],
                'suggestions': ['Use approved tables from whitelist'],
                'confidence': 0.7
            }
        else:
            suggestions = []
            confidence = 0.95
            
            # 性能建议
            if 'SELECT *' in sql:
                suggestions.append('Consider specifying columns instead of SELECT *')
                confidence -= 0.05
            
            if sql.count('JOIN') > 3:
                suggestions.append('Multiple JOINs detected - verify performance')
                confidence -= 0.1
            
            response = {
                'status': 'PASS',
                'risks': [],
                'suggestions': suggestions,
                'confidence': max(confidence, 0.5)
            }
        
        self.send_json_response(response)
    
    def send_json_response(self, data, status_code=200):
        """发送JSON响应"""
        response_data = json.dumps(data, ensure_ascii=False, indent=2)
        
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        self.wfile.write(response_data.encode('utf-8'))
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {format % args}")

def start_mock_server(port=8000):
    """启动Mock服务器"""
    handler = MockHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"🚀 Mock服务器启动成功！")
            print(f"🌐 地址: http://localhost:{port}")
            print(f"💡 健康检查: http://localhost:{port}/health")
            print(f"📊 指标接口: http://localhost:{port}/metrics")
            print(f"🔧 Text2SQL: POST http://localhost:{port}/api/text2sql")
            print(f"🛡️ SQL验证: POST http://localhost:{port}/api/sql/validate")
            print("=" * 50)
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print(f"\n⚠️ 服务器停止")
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"❌ 端口{port}已被占用！")
            return False
        else:
            print(f"❌ 启动失败: {e}")
            return False
    
    return True

if __name__ == "__main__":
    import sys
    
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("❌ 端口号必须是数字")
            sys.exit(1)
    
    start_mock_server(port)