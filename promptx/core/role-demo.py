#!/usr/bin/env python3
"""
角色切换演示脚本
展示如何在Text2SQL系统中灵活调用不同角色
"""

from role_switcher import get_role_switcher
import json

def demo_role_switching():
    """演示角色切换功能"""
    print("=" * 60)
    print("🌟 Text2SQL 角色管理系统演示")
    print("=" * 60)
    
    # 获取角色切换器实例
    switcher = get_role_switcher()
    
    # 演示场景1：用户查询需要多角色协作
    print("\n场景1：用户查询 - 多角色协作")
    print("-" * 40)
    
    user_query = "查询上个月销售额最高的10个产品"
    print(f"用户: {user_query}")
    
    # 自动检测应该使用的角色
    detected_role = switcher.detect_role_from_input(user_query)
    print(f"\n系统检测到需要激活: {detected_role}")
    
    # 切换到QueryScribe
    role, message = switcher.switch_role("QueryScribe", user_query)
    print(f"\n{message}")
    print(f"可用工具: {switcher.get_role_tools()}")
    
    # QueryScribe完成翻译后，切换到SQLGuardian
    sql = "SELECT p.name, SUM(oi.subtotal) as total_sales FROM products p JOIN order_items oi ON p.id = oi.product_id WHERE DATE_TRUNC('month', o.order_date) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') GROUP BY p.id ORDER BY total_sales DESC LIMIT 10"
    
    role, message = switcher.switch_role("SQLGuardian", f"验证SQL: {sql}")
    print(f"\n{message}")
    print(f"角色能力: {', '.join(switcher.get_role_capabilities()[:3])}...")
    
    # 演示场景2：错误处理
    print("\n\n场景2：错误处理 - Debugger介入")
    print("-" * 40)
    
    error_msg = "ERROR: relation 'orders' does not exist"
    print(f"执行出错: {error_msg}")
    
    # 自动激活Debugger
    role, message = switcher.switch_role("Debugger", error_msg)
    print(f"\n{message}")
    
    # 更新共享记忆
    switcher.update_shared_memory("last_error", {
        "error": error_msg,
        "sql": sql,
        "timestamp": "2025-06-16T10:30:00"
    })
    
    # 演示场景3：系统监控
    print("\n\n场景3：定期监控 - MetricsWatcher")
    print("-" * 40)
    
    role, message = switcher.switch_role("MetricsWatcher", "执行日常性能检查")
    print(f"\n{message}")
    
    # 显示角色特定的记忆键
    memory_keys = switcher.get_role_specific_memory_keys()
    print(f"MetricsWatcher可访问的记忆: {', '.join(memory_keys)}")
    
    # 演示场景4：Schema分析
    print("\n\n场景4：数据库结构分析")
    print("-" * 40)
    
    user_input = "@schema 分析新添加的用户行为表"
    detected = switcher.detect_role_from_input(user_input)
    role, message = switcher.switch_role(detected, "分析user_behavior表结构")
    print(f"\n{message}")
    
    # 生成角色使用报告
    print("\n\n📊 角色使用统计")
    print("-" * 40)
    report = switcher.generate_role_report()
    print(f"当前角色: {report['current_role']}")
    print(f"总切换次数: {report['total_switches']}")
    print("\n角色使用频率:")
    for role, count in report['role_usage'].items():
        print(f"  {role}: {count}次")
    
    # 演示NuWa的协调能力
    print("\n\n场景5：NuWa总控制")
    print("-" * 40)
    
    role, message = switcher.switch_role("NuWa", "需要完成一个复杂的数据分析任务")
    print(f"\n{message}")
    print("\n女娲决定任务分配：")
    print("1. SchemaSage - 分析相关表结构")
    print("2. QueryScribe - 将需求转换为SQL")
    print("3. SQLGuardian - 验证查询安全性")
    print("4. MetricsWatcher - 监控执行性能")
    
    # 展示角色协作模式
    print("\n\n🔄 角色协作模式")
    print("-" * 40)
    print("1. 顺序协作: User → QueryScribe → SQLGuardian → Executor")
    print("2. 并行协作: SchemaSage + MetricsWatcher 同时工作")
    print("3. 层级协作: NuWa → (多个执行角色) → 结果汇总")

def show_role_capabilities():
    """展示所有角色的能力矩阵"""
    print("\n\n📋 角色能力矩阵")
    print("=" * 80)
    
    switcher = get_role_switcher()
    roles = ["NuWa", "SchemaSage", "SQLGuardian", "Debugger", "QueryScribe", "MetricsWatcher"]
    
    for role in roles:
        role_info = switcher.role_config['roles'].get(role, {})
        print(f"\n{role} - {role_info.get('title', '')}")
        print(f"描述: {role_info.get('description', '')}")
        print(f"工具: {', '.join(role_info.get('tools', []))}")
        print(f"触发词: {', '.join(role_info.get('triggers', []))}")

if __name__ == "__main__":
    # 运行演示
    demo_role_switching()
    show_role_capabilities()
    
    print("\n\n✨ 演示完成！")
    print("女娲曰：各司其职，协同造化，方成大器。")