#!/usr/bin/env python3
"""
agentdemo 演示脚本
验证系统功能和超时处理机制
"""

import asyncio
import sys
import os
import time

# 添加当前目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.agent_system import EnhancedDynamicAgentSystem
from src.utils.logger_manager import logger_manager


async def run_demo_tests():
    """运行演示测试"""
    print("🚀 开始 agentdemo 演示测试")
    print("=" * 50)
    
    # 检查 API 密钥
    api_key = os.environ.get("AGENTDEMO_API_KEY")
    if not api_key:
        print("❌ 请设置 AGENTDEMO_API_KEY 环境变量")
        print("   例如: export AGENTDEMO_API_KEY='your_openai_api_key'")
        return
    
    # 初始化系统
    print("🔧 初始化系统...")
    system = EnhancedDynamicAgentSystem(api_key)
    await system.initialize_system()
    
    print(f"✅ 系统初始化完成 - 可用 Agent: {system.get_available_agents()}")
    
    # 测试查询
    test_queries = [
        "查询北京明天的天气",
        "从上海到广州有哪些交通方式？",
        "去杭州旅游3天需要多少预算？",
        "我想去西安旅游，帮我规划一下行程"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*40}")
        print(f"测试 {i}/{len(test_queries)}: {query}")
        print(f"{'='*40}")
        
        start_time = time.time()
        
        try:
            result = await system.process_query(query)
            execution_time = time.time() - start_time
            
            # 显示结果
            final_result = result.get('final_result', {})
            
            if final_result.get('error'):
                print(f"❌ 处理失败: {final_result['error']}")
            else:
                print(f"✅ 处理成功")
                print(f"   响应: {final_result.get('content', '')[:100]}...")
                print(f"   迭代次数: {result.get('iteration_count', 0)}")
                print(f"   执行时间: {execution_time:.2f}s")
                
                # 显示性能指标
                performance = result.get('performance', {})
                if performance:
                    print(f"   超时次数: {performance.get('total_timeouts', 0)}")
                    print(f"   重试次数: {performance.get('total_retries', 0)}")
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ 查询处理异常: {e}")
            print(f"   执行时间: {execution_time:.2f}s")
        
        # 短暂等待，避免 API 限制
        await asyncio.sleep(1)
    
    # 显示系统状态和性能指标
    print(f"\n{'='*50}")
    print("📊 系统性能统计")
    print(f"{'='*50}")
    
    status = system.get_system_status()
    metrics = system.get_performance_metrics()
    
    print(f"系统状态: {status.overall_status}")
    print(f"活跃 Agent: {status.active_agents}/{status.total_agents}")
    print(f"系统运行时间: {status.uptime:.2f}s")
    
    if metrics:
        system_metrics = metrics.get('system', {})
        print(f"总查询数: {system_metrics.get('total_queries', 0)}")
        print(f"成功查询: {system_metrics.get('successful_queries', 0)}")
        print(f"失败查询: {system_metrics.get('failed_queries', 0)}")
        print(f"成功率: {system_metrics.get('success_rate', 0):.1f}%")
    
    # 显示 Agent 性能
    print(f"\n🤖 Agent 性能指标:")
    agent_metrics = metrics.get('agents', {})
    for agent_name, agent_metric in agent_metrics.items():
        print(f"  {agent_name}:")
        print(f"    总请求: {agent_metric.get('total_requests', 0)}")
        print(f"    成功率: {agent_metric.get('success_rate', 0):.1f}%")
        print(f"    超时率: {agent_metric.get('timeout_rate', 0):.1f}%")
    
    # 关闭系统
    print(f"\n🔚 关闭系统...")
    await system.shutdown_system()
    
    print(f"\n🎉 演示测试完成！")


async def test_timeout_handling():
    """测试超时处理机制"""
    print(f"\n{'='*50}")
    print("⏰ 测试超时处理机制")
    print(f"{'='*50}")
    
    api_key = os.environ.get("AGENTDEMO_API_KEY")
    if not api_key:
        print("❌ 请设置 AGENTDEMO_API_KEY 环境变量")
        return
    api_key = "hk-fwuzp810000596427a889f4a9def096b062f5a0d01ac0abd"
    # 初始化系统
    system = EnhancedDynamicAgentSystem(api_key)
    await system.initialize_system()
    
    # 测试超长查询（可能触发超时）
    long_query = "请详细分析北京、上海、广州、深圳、杭州、成都、武汉、西安这八个城市的天气、交通、预算情况，并给出详细的旅行建议，包括每个城市的最佳旅行时间、必去景点、特色美食、住宿推荐、交通方式、预算估算等详细信息。"
    
    print(f"测试查询: {long_query[:50]}...")
    print("这个查询可能会触发超时处理机制...")
    
    start_time = time.time()
    
    try:
        result = await system.process_query(long_query)
        execution_time = time.time() - start_time
        
        print(f"✅ 查询处理完成")
        print(f"   执行时间: {execution_time:.2f}s")
        print(f"   迭代次数: {result.get('iteration_count', 0)}")
        
        # 检查超时情况
        performance = result.get('performance', {})
        if performance.get('total_timeouts', 0) > 0:
            print(f"⚠️  检测到超时: {performance['total_timeouts']} 次")
        else:
            print(f"✅ 无超时发生")
            
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"❌ 查询处理异常: {e}")
        print(f"   执行时间: {execution_time:.2f}s")
    
    # 关闭系统
    await system.shutdown_system()


async def main():
    """主函数"""
    print("🎬 agentdemo 演示脚本")
    print("=" * 50)
    
    # 运行基本演示
    await run_demo_tests()
    
    # 运行超时处理测试
    await test_timeout_handling()
    
    print(f"\n🎊 所有演示测试完成！")
    print("💡 提示: 查看 logs/agentdemo.log 文件获取详细日志信息")


if __name__ == "__main__":
    asyncio.run(main())
