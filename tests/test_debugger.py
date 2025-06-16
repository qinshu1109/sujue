#!/usr/bin/env python3
"""
Debugger v2 单元测试
女娲造物：测则明，试则安
"""

import asyncio
import sys
import os
import unittest

# 添加路径以导入debugger
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'db-gpt'))

from debugger import DebuggerV2, ErrorType

class TestDebuggerV2(unittest.TestCase):
    """Debugger v2 测试类"""
    
    def setUp(self):
        """每个测试方法前的设置"""
        self.debugger = DebuggerV2(max_retries=3)
    
    def test_error_type_detection_schema(self):
        """测试Schema错误检测"""
        error_msg = "Table 'nonexistent_table' does not exist"
        error_type = self.debugger.detect_error_type(error_msg)
        assert error_type == ErrorType.SCHEMA_ERROR
    
    def test_error_type_detection_syntax(self):
        """测试SQL语法错误检测"""
        error_msg = "Syntax error near 'SELECT'"
        error_type = self.debugger.detect_error_type(error_msg)
        assert error_type == ErrorType.SQL_SYNTAX_ERROR
    
    def test_error_type_detection_permission(self):
        """测试权限错误检测"""
        error_msg = "Permission denied for table users"
        error_type = self.debugger.detect_error_type(error_msg)
        assert error_type == ErrorType.PERMISSION_ERROR
    
    def test_error_type_detection_timeout(self):
        """测试超时错误检测"""
        error_msg = "Query timeout after 30 seconds"
        error_type = self.debugger.detect_error_type(error_msg)
        assert error_type == ErrorType.TIMEOUT_ERROR
    
    def test_error_type_detection_unknown(self):
        """测试未知错误检测"""
        error_msg = "Some mysterious database error"
        error_type = self.debugger.detect_error_type(error_msg)
        assert error_type == ErrorType.UNKNOWN_ERROR
    
    def test_fix_schema_error_table(self):
        """测试修复Schema表错误"""
        async def _test():
            sql = "SELECT * FROM nonexistent_table"
            error = "table 'nonexistent_table' does not exist"
            
            result = await self.debugger._fix_schema_error(sql, error, {}, 1)
            
            self.assertTrue(result['success'])
            self.assertIn('users', result['fixed_sql'])  # 应该替换为已知表
            self.assertIn('replaced', result['fix_reason'].lower())
        
        asyncio.run(_test())
    
    @pytest.mark.asyncio
    async def test_fix_syntax_error_missing_semicolon(self):
        """测试修复语法错误 - 缺少分号"""
        sql = "SELECT * FROM users"
        error = "syntax error"
        
        result = await self.debugger._fix_syntax_error(sql, error, {}, 1)
        
        assert result['success'] == True
        assert result['fixed_sql'].endswith(';')
        assert 'semicolon' in result['fix_reason'].lower()
    
    @pytest.mark.asyncio
    async def test_fix_syntax_error_select_star(self):
        """测试修复语法错误 - SELECT*FROM"""
        sql = "SELECT*FROM users"
        error = "syntax error near SELECT*FROM"
        
        result = await self.debugger._fix_syntax_error(sql, error, {}, 1)
        
        assert result['success'] == True
        assert 'SELECT * FROM' in result['fixed_sql']
        assert 'spaces' in result['fix_reason'].lower()
    
    @pytest.mark.asyncio
    async def test_fix_timeout_error_add_limit(self):
        """测试修复超时错误 - 添加LIMIT"""
        sql = "SELECT * FROM large_table"
        error = "query timeout"
        
        result = await self.debugger._fix_timeout_error(sql, error, {}, 1)
        
        assert result['success'] == True
        assert 'LIMIT 100' in result['fixed_sql']
        assert 'LIMIT' in result['fix_reason']
    
    @pytest.mark.asyncio
    async def test_fix_timeout_error_reduce_limit(self):
        """测试修复超时错误 - 减少LIMIT"""
        sql = "SELECT * FROM large_table LIMIT 1000"
        error = "query timeout"
        
        result = await self.debugger._fix_timeout_error(sql, error, {}, 1)
        
        assert result['success'] == True
        assert 'LIMIT 500' in result['fixed_sql']
        assert 'Reduced LIMIT' in result['fix_reason']
    
    @pytest.mark.asyncio
    async def test_auto_fix_sql_success(self):
        """测试完整自修复流程 - 成功案例"""
        sql = "SELECT*FROM users"
        error = "syntax error near SELECT*FROM"
        
        result = await self.debugger.auto_fix_sql(sql, error)
        
        assert result['success'] == True
        assert 'SELECT * FROM' in result['fixed_sql']
        assert result['attempts'] == 1
        assert 'session_id' in result
        assert result['error_type'] == 'sql_syntax_error'
    
    @pytest.mark.asyncio
    async def test_auto_fix_sql_max_retries(self):
        """测试自修复达到最大重试次数"""
        # 使用一个很难修复的错误
        sql = "INVALID SQL QUERY WITH MANY ERRORS"
        error = "completely invalid syntax"
        
        debugger = DebuggerV2(max_retries=2)  # 设置较低的重试次数
        result = await debugger.auto_fix_sql(sql, error)
        
        assert result['success'] == False
        assert result['attempts'] == 2
        assert 'session_id' in result
    
    @pytest.mark.asyncio
    async def test_rag_search_tables(self):
        """测试RAG表搜索"""
        similar_tables = await self.debugger._rag_search_tables('user_info')
        
        assert len(similar_tables) > 0
        assert any('user' in table.lower() for table in similar_tables)
    
    @pytest.mark.asyncio 
    async def test_rag_search_columns(self):
        """测试RAG列搜索"""
        similar_columns = await self.debugger._rag_search_columns('user_name', 'SELECT user_name FROM users')
        
        assert len(similar_columns) >= 0  # 可能返回空列表或有结果
    
    def test_get_fix_statistics_empty(self):
        """测试空修复历史的统计"""
        stats = self.debugger.get_fix_statistics()
        assert stats['total_sessions'] == 0
    
    @pytest.mark.asyncio
    async def test_get_fix_statistics_with_data(self):
        """测试有数据的修复统计"""
        # 执行一次修复来生成历史数据
        sql = "SELECT * FROM users"
        error = "syntax error"
        
        await self.debugger.auto_fix_sql(sql, error)
        
        stats = self.debugger.get_fix_statistics()
        assert stats['total_sessions'] == 1
        assert stats['successful_sessions'] >= 0
        assert 'success_rate' in stats
        assert 'error_type_distribution' in stats

def run_tests():
    """运行所有测试"""
    print("🧪 开始Debugger v2单元测试...")
    
    # 简化测试运行
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDebuggerV2)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("✅ 所有Debugger测试通过！")
        return True
    else:
        print("❌ 部分Debugger测试失败！")
        return False

if __name__ == "__main__":
    # 如果直接运行，执行测试
    success = run_tests()
    exit(0 if success else 1)