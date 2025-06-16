#!/usr/bin/env python3
"""
Debugger v2 - 智能自修复系统
女娲造物：察错知因，回天有术
"""

import re
import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from datetime import datetime
# 简化日志
class SimpleLogger:
    def info(self, msg, **kwargs): print(f"INFO: {msg}")
    def warning(self, msg, **kwargs): print(f"WARN: {msg}")
    def error(self, msg, **kwargs): print(f"ERROR: {msg}")

logger = SimpleLogger()

class ErrorType(Enum):
    """错误类型枚举"""
    SCHEMA_ERROR = "schema_error"           # Schema相关错误
    SQL_SYNTAX_ERROR = "sql_syntax_error"   # SQL语法错误
    PERMISSION_ERROR = "permission_error"   # 权限错误
    TIMEOUT_ERROR = "timeout_error"         # 超时错误
    UNKNOWN_ERROR = "unknown_error"         # 未知错误

class DebuggerV2:
    """自修复调试器 v2"""
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.error_patterns = self._load_error_patterns()
        self.fix_strategies = self._load_fix_strategies()
        self.fixes_history = []
        
    def _load_error_patterns(self) -> Dict[ErrorType, List[str]]:
        """加载错误模式"""
        return {
            ErrorType.SCHEMA_ERROR: [
                r"table.*does not exist",
                r"column.*does not exist", 
                r"relation.*does not exist",
                r"no such table",
                r"unknown column"
            ],
            ErrorType.SQL_SYNTAX_ERROR: [
                r"syntax error",
                r"unexpected token",
                r"missing.*from",
                r"invalid syntax",
                r"malformed query"
            ],
            ErrorType.PERMISSION_ERROR: [
                r"permission denied",
                r"access denied",
                r"insufficient privileges",
                r"unauthorized"
            ],
            ErrorType.TIMEOUT_ERROR: [
                r"timeout",
                r"connection.*timeout",
                r"query.*timeout"
            ]
        }
    
    def _load_fix_strategies(self) -> Dict[ErrorType, callable]:
        """加载修复策略"""
        return {
            ErrorType.SCHEMA_ERROR: self._fix_schema_error,
            ErrorType.SQL_SYNTAX_ERROR: self._fix_syntax_error,
            ErrorType.PERMISSION_ERROR: self._fix_permission_error,
            ErrorType.TIMEOUT_ERROR: self._fix_timeout_error,
            ErrorType.UNKNOWN_ERROR: self._fix_unknown_error
        }
    
    def detect_error_type(self, error_message: str) -> ErrorType:
        """检测错误类型"""
        error_lower = error_message.lower()
        
        for error_type, patterns in self.error_patterns.items():
            for pattern in patterns:
                if re.search(pattern, error_lower):
                    logger.info(f"检测到错误类型: {error_type.value}", 
                               pattern=pattern, error=error_message[:100])
                    return error_type
        
        return ErrorType.UNKNOWN_ERROR
    
    async def auto_fix_sql(self, 
                          original_sql: str, 
                          error_message: str,
                          context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """自动修复SQL - 主入口"""
        fix_session = {
            'original_sql': original_sql,
            'error_message': error_message,
            'context': context or {},
            'attempts': [],
            'start_time': datetime.utcnow().isoformat(),
            'session_id': f"fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        
        logger.info("开始自修复会话", session_id=fix_session['session_id'])
        
        # 检测错误类型
        error_type = self.detect_error_type(error_message)
        
        # 获取修复策略
        fix_strategy = self.fix_strategies.get(error_type, self._fix_unknown_error)
        
        current_sql = original_sql
        
        for attempt in range(1, self.max_retries + 1):
            logger.info(f"尝试修复 {attempt}/{self.max_retries}", 
                       error_type=error_type.value)
            
            try:
                # 执行修复策略
                fix_result = await fix_strategy(
                    current_sql, 
                    error_message, 
                    context, 
                    attempt
                )
                
                attempt_record = {
                    'attempt': attempt,
                    'error_type': error_type.value,
                    'fix_strategy': fix_strategy.__name__,
                    'input_sql': current_sql,
                    'output_sql': fix_result.get('fixed_sql'),
                    'fix_reason': fix_result.get('fix_reason'),
                    'confidence': fix_result.get('confidence', 0.5),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                fix_session['attempts'].append(attempt_record)
                
                if fix_result.get('success'):
                    # 修复成功
                    fix_session['status'] = 'SUCCESS'
                    fix_session['final_sql'] = fix_result['fixed_sql']
                    fix_session['end_time'] = datetime.utcnow().isoformat()
                    
                    # 记录到历史
                    self.fixes_history.append(fix_session)
                    
                    logger.info("自修复成功", 
                               session_id=fix_session['session_id'],
                               attempts=attempt,
                               final_sql=fix_result['fixed_sql'][:100])
                    
                    return {
                        'success': True,
                        'fixed_sql': fix_result['fixed_sql'],
                        'fix_reason': fix_result['fix_reason'],
                        'attempts': attempt,
                        'session_id': fix_session['session_id'],
                        'error_type': error_type.value
                    }
                else:
                    # 修复失败，准备下次尝试
                    if fix_result.get('fixed_sql'):
                        current_sql = fix_result['fixed_sql']
                    
                    logger.warning(f"修复尝试{attempt}失败", 
                                 reason=fix_result.get('fix_reason'))
                
            except Exception as e:
                logger.error(f"修复策略执行异常: {e}", attempt=attempt)
                
                attempt_record = {
                    'attempt': attempt,
                    'error_type': error_type.value,
                    'fix_strategy': fix_strategy.__name__,
                    'input_sql': current_sql,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }
                fix_session['attempts'].append(attempt_record)
        
        # 所有尝试都失败
        fix_session['status'] = 'FAILED'
        fix_session['end_time'] = datetime.utcnow().isoformat()
        self.fixes_history.append(fix_session)
        
        logger.error("自修复失败", 
                    session_id=fix_session['session_id'],
                    total_attempts=self.max_retries)
        
        return {
            'success': False,
            'original_sql': original_sql,
            'error_message': error_message,
            'attempts': self.max_retries,
            'session_id': fix_session['session_id'],
            'error_type': error_type.value
        }
    
    async def _fix_schema_error(self, 
                               sql: str, 
                               error: str, 
                               context: Dict[str, Any], 
                               attempt: int) -> Dict[str, Any]:
        """修复Schema错误 - 触发RAG检索重写"""
        logger.info("执行Schema错误修复策略")
        
        # 提取错误的表名或列名
        table_match = re.search(r"table ['\"]?(\w+)['\"]? does not exist", error.lower())
        column_match = re.search(r"column ['\"]?(\w+)['\"]? does not exist", error.lower())
        
        if table_match:
            missing_table = table_match.group(1)
            
            # 模拟RAG检索 - 查找相似表名
            similar_tables = await self._rag_search_tables(missing_table)
            
            if similar_tables:
                # 替换表名
                fixed_sql = re.sub(
                    rf'\b{missing_table}\b', 
                    similar_tables[0], 
                    sql, 
                    flags=re.IGNORECASE
                )
                
                return {
                    'success': True,
                    'fixed_sql': fixed_sql,
                    'fix_reason': f'Table "{missing_table}" replaced with "{similar_tables[0]}"',
                    'confidence': 0.8
                }
        
        elif column_match:
            missing_column = column_match.group(1)
            
            # 模拟列名修复
            similar_columns = await self._rag_search_columns(missing_column, sql)
            
            if similar_columns:
                fixed_sql = re.sub(
                    rf'\b{missing_column}\b',
                    similar_columns[0],
                    sql,
                    flags=re.IGNORECASE
                )
                
                return {
                    'success': True,
                    'fixed_sql': fixed_sql,
                    'fix_reason': f'Column "{missing_column}" replaced with "{similar_columns[0]}"',
                    'confidence': 0.7
                }
        
        return {
            'success': False,
            'fix_reason': 'No suitable schema replacement found',
            'confidence': 0.0
        }
    
    async def _fix_syntax_error(self, 
                               sql: str, 
                               error: str, 
                               context: Dict[str, Any], 
                               attempt: int) -> Dict[str, Any]:
        """修复SQL语法错误 - Rule-based修补"""
        logger.info("执行SQL语法错误修复策略")
        
        fixed_sql = sql
        fixes_applied = []
        
        # 常见语法修复规则
        syntax_fixes = [
            # 缺少分号
            (r'^(.*[^;])\s*$', r'\1;', 'Added missing semicolon'),
            
            # SELECT * FROM 缺少空格
            (r'SELECT\*FROM', 'SELECT * FROM', 'Added spaces around SELECT *'),
            
            # 缺少FROM关键字
            (r'SELECT\s+[\w,\s]+\s+(\w+)(?!\s+FROM)', r'SELECT \g<0> FROM \1', 'Added missing FROM'),
            
            # JOIN语法修复
            (r'JOIN\s+(\w+)\s+(\w+)', r'JOIN \1 ON \2', 'Fixed JOIN syntax'),
            
            # WHERE条件修复
            (r'WHERE\s+(\w+)\s*=\s*([^\'"\d]\w*)', r'WHERE \1 = "\2"', 'Added quotes to string value'),
            
            # ORDER BY修复
            (r'ORDER\s+(\w+)', r'ORDER BY \1', 'Added missing BY in ORDER BY'),
        ]
        
        for pattern, replacement, description in syntax_fixes:
            if re.search(pattern, fixed_sql, re.IGNORECASE):
                new_sql = re.sub(pattern, replacement, fixed_sql, flags=re.IGNORECASE)
                if new_sql != fixed_sql:
                    fixed_sql = new_sql
                    fixes_applied.append(description)
        
        if fixes_applied:
            return {
                'success': True,
                'fixed_sql': fixed_sql,
                'fix_reason': f'Applied fixes: {", ".join(fixes_applied)}',
                'confidence': 0.9
            }
        
        return {
            'success': False,
            'fix_reason': 'No applicable syntax fixes found',
            'confidence': 0.0
        }
    
    async def _fix_permission_error(self, 
                                   sql: str, 
                                   error: str, 
                                   context: Dict[str, Any], 
                                   attempt: int) -> Dict[str, Any]:
        """修复权限错误"""
        logger.info("执行权限错误修复策略")
        
        # 权限错误通常需要切换到允许的表
        if 'permission denied' in error.lower():
            # 模拟切换到公开表
            public_tables = ['public_users', 'sample_data', 'demo_table']
            
            # 查找SQL中的表名并替换
            table_pattern = r'FROM\s+(\w+)'
            match = re.search(table_pattern, sql, re.IGNORECASE)
            
            if match:
                original_table = match.group(1)
                fixed_sql = re.sub(
                    rf'\b{original_table}\b',
                    public_tables[0],
                    sql,
                    flags=re.IGNORECASE
                )
                
                return {
                    'success': True,
                    'fixed_sql': fixed_sql,
                    'fix_reason': f'Switched to public table: {public_tables[0]}',
                    'confidence': 0.6
                }
        
        return {
            'success': False,
            'fix_reason': 'Cannot resolve permission error',
            'confidence': 0.0
        }
    
    async def _fix_timeout_error(self, 
                                sql: str, 
                                error: str, 
                                context: Dict[str, Any], 
                                attempt: int) -> Dict[str, Any]:
        """修复超时错误"""
        logger.info("执行超时错误修复策略")
        
        fixed_sql = sql
        
        # 添加LIMIT子句减少查询数据量
        if 'LIMIT' not in sql.upper():
            fixed_sql = sql.rstrip(';') + ' LIMIT 100;'
            
            return {
                'success': True,
                'fixed_sql': fixed_sql,
                'fix_reason': 'Added LIMIT 100 to reduce query time',
                'confidence': 0.8
            }
        
        # 如果已有LIMIT，尝试减少数量
        limit_match = re.search(r'LIMIT\s+(\d+)', sql, re.IGNORECASE)
        if limit_match:
            current_limit = int(limit_match.group(1))
            new_limit = max(10, current_limit // 2)  # 减半，最少10
            
            fixed_sql = re.sub(
                r'LIMIT\s+\d+',
                f'LIMIT {new_limit}',
                sql,
                flags=re.IGNORECASE
            )
            
            return {
                'success': True,
                'fixed_sql': fixed_sql,
                'fix_reason': f'Reduced LIMIT from {current_limit} to {new_limit}',
                'confidence': 0.7
            }
        
        return {
            'success': False,
            'fix_reason': 'Cannot optimize query further',
            'confidence': 0.0
        }
    
    async def _fix_unknown_error(self, 
                                sql: str, 
                                error: str, 
                                context: Dict[str, Any], 
                                attempt: int) -> Dict[str, Any]:
        """修复未知错误 - 通用策略"""
        logger.info("执行未知错误修复策略")
        
        # 尝试一些通用修复
        if attempt == 1:
            # 第一次尝试：简化查询
            simplified_sql = self._simplify_query(sql)
            if simplified_sql != sql:
                return {
                    'success': True,
                    'fixed_sql': simplified_sql,
                    'fix_reason': 'Simplified complex query',
                    'confidence': 0.5
                }
        
        return {
            'success': False,
            'fix_reason': 'Unknown error cannot be resolved',
            'confidence': 0.0
        }
    
    def _simplify_query(self, sql: str) -> str:
        """简化复杂查询"""
        # 移除复杂的子查询
        simplified = re.sub(r'\([^)]*SELECT[^)]*\)', 'simplified_subquery', sql, flags=re.IGNORECASE)
        
        # 限制JOIN数量
        joins = re.findall(r'\bJOIN\b', simplified, re.IGNORECASE)
        if len(joins) > 3:
            # 保留前3个JOIN，移除其余
            parts = re.split(r'\bJOIN\b', simplified, flags=re.IGNORECASE)
            simplified = 'JOIN'.join(parts[:4])  # 保留主查询+3个JOIN
        
        return simplified
    
    async def _rag_search_tables(self, missing_table: str) -> List[str]:
        """RAG检索相似表名"""
        # 模拟RAG检索
        available_tables = [
            'users', 'user_profiles', 'customers',
            'products', 'product_catalog', 'items',
            'orders', 'order_items', 'transactions',
            'categories', 'tags', 'labels'
        ]
        
        # 简单的相似度匹配
        similar = []
        missing_lower = missing_table.lower()
        
        for table in available_tables:
            if missing_lower in table.lower() or table.lower() in missing_lower:
                similar.append(table)
        
        return similar[:3]  # 返回最多3个相似表
    
    async def _rag_search_columns(self, missing_column: str, sql: str) -> List[str]:
        """RAG检索相似列名"""
        # 模拟列名映射
        column_mapping = {
            'name': ['username', 'full_name', 'display_name'],
            'email': ['email_address', 'contact_email', 'user_email'],
            'id': ['user_id', 'product_id', 'order_id'],
            'price': ['cost', 'amount', 'total'],
            'date': ['created_at', 'updated_at', 'timestamp']
        }
        
        missing_lower = missing_column.lower()
        
        for key, alternatives in column_mapping.items():
            if key in missing_lower or missing_lower in key:
                return alternatives[:2]
        
        return []
    
    def get_fix_statistics(self) -> Dict[str, Any]:
        """获取修复统计信息"""
        if not self.fixes_history:
            return {'total_sessions': 0}
        
        total_sessions = len(self.fixes_history)
        successful_sessions = len([s for s in self.fixes_history if s.get('status') == 'SUCCESS'])
        
        error_type_counts = {}
        for session in self.fixes_history:
            for attempt in session.get('attempts', []):
                error_type = attempt.get('error_type')
                if error_type:
                    error_type_counts[error_type] = error_type_counts.get(error_type, 0) + 1
        
        return {
            'total_sessions': total_sessions,
            'successful_sessions': successful_sessions,
            'success_rate': successful_sessions / total_sessions if total_sessions > 0 else 0,
            'error_type_distribution': error_type_counts,
            'average_attempts': sum(len(s.get('attempts', [])) for s in self.fixes_history) / total_sessions if total_sessions > 0 else 0
        }

# 全局实例
_debugger_instance = None

def get_debugger(max_retries: int = 3) -> DebuggerV2:
    """获取全局Debugger实例"""
    global _debugger_instance
    if _debugger_instance is None:
        _debugger_instance = DebuggerV2(max_retries)
    return _debugger_instance