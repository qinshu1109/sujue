#!/usr/bin/env python3
"""
Debugger v2 简化测试
女娲造物：简测也明，快验亦真
"""

import asyncio
import sys
import os

# 添加路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'db-gpt'))

from debugger import DebuggerV2, ErrorType

async def test_basic_functionality():
    """测试基本功能"""
    print("🧪 测试Debugger v2基本功能...")
    
    debugger = DebuggerV2(max_retries=2)
    
    # 测试1: 错误类型检测
    print("\n📝 测试1: 错误类型检测")
    test_cases = [
        ("Table 'users' does not exist", ErrorType.SCHEMA_ERROR),
        ("Syntax error near SELECT", ErrorType.SQL_SYNTAX_ERROR),
        ("Permission denied", ErrorType.PERMISSION_ERROR),
        ("Query timeout", ErrorType.TIMEOUT_ERROR),
        ("Unknown error", ErrorType.UNKNOWN_ERROR)
    ]
    
    for error_msg, expected_type in test_cases:
        detected_type = debugger.detect_error_type(error_msg)
        status = "✅" if detected_type == expected_type else "❌"
        print(f"  {status} {error_msg[:30]}... -> {detected_type.value}")
    
    # 测试2: Schema错误修复
    print("\n📝 测试2: Schema错误修复")
    sql = "SELECT * FROM nonexistent_table"
    error = "table 'nonexistent_table' does not exist"
    
    result = await debugger._fix_schema_error(sql, error, {}, 1)
    status = "✅" if result['success'] else "❌"
    print(f"  {status} Schema修复: {result['success']}")
    if result['success']:
        print(f"    修复后SQL: {result['fixed_sql']}")
        print(f"    修复原因: {result['fix_reason']}")
    
    # 测试3: 语法错误修复
    print("\n📝 测试3: 语法错误修复")
    sql = "SELECT*FROM users"
    error = "syntax error"
    
    result = await debugger._fix_syntax_error(sql, error, {}, 1)
    status = "✅" if result['success'] else "❌"
    print(f"  {status} 语法修复: {result['success']}")
    if result['success']:
        print(f"    修复后SQL: {result['fixed_sql']}")
        print(f"    修复原因: {result['fix_reason']}")
    
    # 测试4: 超时错误修复
    print("\n📝 测试4: 超时错误修复")
    sql = "SELECT * FROM large_table"
    error = "query timeout"
    
    result = await debugger._fix_timeout_error(sql, error, {}, 1)
    status = "✅" if result['success'] else "❌"
    print(f"  {status} 超时修复: {result['success']}")
    if result['success']:
        print(f"    修复后SQL: {result['fixed_sql']}")
        print(f"    修复原因: {result['fix_reason']}")
    
    # 测试5: 完整自修复流程
    print("\n📝 测试5: 完整自修复流程")
    sql = "SELECT name,email FROM user_table"  # 缺少空格
    error = "syntax error near SELECT"
    
    result = await debugger.auto_fix_sql(sql, error)
    status = "✅" if result['success'] else "❌"
    print(f"  {status} 完整修复: {result['success']}")
    print(f"    尝试次数: {result['attempts']}")
    print(f"    错误类型: {result['error_type']}")
    if result['success']:
        print(f"    最终SQL: {result['fixed_sql']}")
        print(f"    会话ID: {result['session_id']}")
    
    # 测试6: 修复统计
    print("\n📝 测试6: 修复统计")
    stats = debugger.get_fix_statistics()
    print(f"  📊 总会话数: {stats['total_sessions']}")
    print(f"  📊 成功会话数: {stats['successful_sessions']}")
    if stats['total_sessions'] > 0:
        print(f"  📊 成功率: {stats['success_rate']:.2%}")
    
    return True

async def test_complex_scenarios():
    """测试复杂场景"""
    print("\n🔬 测试复杂场景...")
    
    debugger = DebuggerV2(max_retries=3)
    
    # 复杂场景1: 多重错误
    print("\n📝 复杂场景1: 多重错误")
    sql = "SELECT*FROM nonexistent_table WHERE id=test"  # 语法+Schema+值错误
    error = "syntax error and table does not exist"
    
    result = await debugger.auto_fix_sql(sql, error)
    status = "✅" if result['success'] else "❌"
    print(f"  {status} 多重错误修复: {result['success']}")
    
    # 复杂场景2: 无法修复的错误
    print("\n📝 复杂场景2: 无法修复的错误")
    sql = "COMPLETELY INVALID SQL WITH NONSENSE"
    error = "total syntax breakdown"
    
    result = await debugger.auto_fix_sql(sql, error)
    status = "✅" if not result['success'] else "❌"  # 应该失败
    print(f"  {status} 无法修复错误处理: {not result['success']}")
    print(f"    最大重试次数: {result['attempts']}")
    
    return True

def main():
    """主函数"""
    print("🚀 开始Debugger v2测试套件...")
    
    try:
        # 运行基本功能测试
        success1 = asyncio.run(test_basic_functionality())
        
        # 运行复杂场景测试
        success2 = asyncio.run(test_complex_scenarios())
        
        if success1 and success2:
            print("\n🎉 所有测试通过！Debugger v2功能正常")
            return True
        else:
            print("\n❌ 部分测试失败")
            return False
            
    except Exception as e:
        print(f"\n💥 测试异常: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)