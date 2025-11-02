#!/usr/bin/env python3
"""
agentdemo 基础功能测试
验证系统核心功能是否正常工作
"""

import asyncio
import sys
import os

# 添加当前目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.agent_system import EnhancedDynamicAgentSystem
from src.utils.logger_manager import logger_manager


async def test_system_initialization():
    """测试系统初始化"""
    print("🧪 测试系统初始化...")
    
    api_key = os.environ.get("AGENTDEMO_API_KEY")
    if not api_key:
        print("❌ 请设置 AGENTDEMO_API_KEY 环境变量")
        return False
    
    try:
        system = EnhancedDynamicAgentSystem(api_key)
        await system.initialize_system()
        
        # 检查系统状态
        status = system.get_system_status()
        available_agents = system.get_available_agents()
        
        print(f"✅ 系统初始化成功")
        print(f"   系统状态: {status.overall_status}")
        print(f"   可用 Agent: {available_agents}")
        
        # 检查是否有足够的 Agent
        if len(available_agents) >= 2:  # 至少应该有协调器和一个插件 Agent
            print(f"✅ Agent 加载正常")
        else:
            print(f"⚠️  Agent 数量较少: {len(available_agents)}")
        
        await system.shutdown_system()
        return True
        
    except Exception as e:
        print(f"❌ 系统初始化失败: {e}")
        return False


async def test_agent_functionality():
    """测试 Agent 功能"""
    print("\n🧪 测试 Agent 功能...")
    
    api_key = os.environ.get("AGENTDEMO_API_KEY")
    if not api_key:
        return False
    
    try:
        system = EnhancedDynamicAgentSystem(api_key)
        await system.initialize_system()
        
        # 测试简单查询
        test_query = "查询北京天气"
        print(f"   测试查询: {test_query}")
        
        result = await system.process_query(test_query)
        
        if result.get('final_result', {}).get('error'):
            print(f"❌ 查询处理失败: {result['final_result']['error']}")
            return False
        else:
            print(f"✅ 查询处理成功")
            print(f"   迭代次数: {result.get('iteration_count', 0)}")
            print(f"   响应长度: {len(result.get('final_result', {}).get('content', ''))}")
        
        await system.shutdown_system()
        return True
        
    except Exception as e:
        print(f"❌ Agent 功能测试失败: {e}")
        return False


async def test_logging_system():
    """测试日志系统"""
    print("\n🧪 测试日志系统...")
    
    try:
        # 初始化日志系统
        logger_manager.setup_logging({
            'level': 'INFO',
            'file_logging': False,
            'console_output': True
        })
        
        # 测试各种日志级别
        logger_manager.log_system_event("测试系统事件", level="INFO")
        logger_manager.log_agent_operation("test_agent", "测试 Agent 操作", level="DEBUG")
        logger_manager.log_timeout_event("test_component", "测试超时", 30)
        
        print("✅ 日志系统测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 日志系统测试失败: {e}")
        return False


async def test_timeout_mechanism():
    """测试超时机制"""
    print("\n🧪 测试超时机制...")
    
    api_key = os.environ.get("AGENTDEMO_API_KEY")
    if not api_key:
        return False
    
    try:
        system = EnhancedDynamicAgentSystem(api_key)
        await system.initialize_system()
        
        # 测试一个可能触发超时的复杂查询
        complex_query = "请详细分析多个城市的天气、交通、预算情况，并给出详细的旅行建议"
        
        result = await system.process_query(complex_query)
        
        # 检查性能指标
        performance = result.get('performance', {})
        timeouts = performance.get('total_timeouts', 0)
        retries = performance.get('total_retries', 0)
        
        print(f"✅ 复杂查询处理完成")
        print(f"   超时次数: {timeouts}")
        print(f"   重试次数: {retries}")
        
        if timeouts > 0:
            print("⚠️  检测到超时，系统正确处理了超时情况")
        else:
            print("✅ 无超时发生")
        
        await system.shutdown_system()
        return True
        
    except Exception as e:
        print(f"❌ 超时机制测试失败: {e}")
        return False


async def run_all_tests():
    """运行所有测试"""
    print("🚀 开始 agentdemo 基础功能测试")
    print("=" * 50)
    
    test_results = []
    
    # 运行各个测试
    test_results.append(await test_system_initialization())
    test_results.append(await test_agent_functionality())
    test_results.append(await test_logging_system())
    test_results.append(await test_timeout_mechanism())
    
    # 统计结果
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"\n{'='*50}")
    print("📊 测试结果汇总")
    print(f"{'='*50}")
    print(f"总测试数: {total}")
    print(f"通过测试: {passed}")
    print(f"失败测试: {total - passed}")
    
    if passed == total:
        print("🎉 所有测试通过！系统功能正常。")
        return True
    else:
        print("⚠️  部分测试失败，请检查系统配置。")
        return False


async def main():
    """主函数"""
    success = await run_all_tests()
    
    if success:
        print(f"\n💡 下一步:")
        print("   1. 运行 python demo.py 进行完整演示")
        print("   2. 运行 python main.py --mode interactive 进行交互测试")
        print("   3. 查看 logs/agentdemo.log 获取详细日志")
    else:
        print(f"\n❌ 测试失败，请检查:")
        print("   1. API 密钥是否正确设置")
        print("   2. 依赖包是否安装")
        print("   3. 配置文件是否正确")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
