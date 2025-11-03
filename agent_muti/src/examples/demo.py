# multi_agent_system/examples/demo.py
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..core.agent_system import EnhancedDynamicAgentSystem


async def demo_enhanced_system():
    """演示增强版系统"""
    api_key = "hk-fwuzp810000596427a889f4a9def096b062f5a0d01ac0abd"  # 替换为你的实际 API 密钥

    if api_key == "your_openai_api_key_here":
        print("❌ 请设置有效的 OpenAI API 密钥")
        print("请在 demo.py 中设置你的 API 密钥")
        return

    # 创建增强系统
    system = EnhancedDynamicAgentSystem(api_key)
    await system.initialize_system()

    # 设置迭代阶段超时
    system.set_iteration_timeout("think", 2500)
    system.set_iteration_timeout("plan", 2500)
    system.set_iteration_timeout("action", 4500)
    system.set_iteration_timeout("next", 1500)

    # 测试复杂查询
    complex_queries = [
        "两人去成都玩三天大概要花多少钱？天气怎么样？怎么去最方便？",
        "我想规划一次去上海的旅行，需要了解天气、交通和预算，还要考虑酒店和景点",
        "帮我比较北京、上海、广州三个城市的旅行成本，包括交通、住宿和餐饮",
        "我需要一个完整的杭州五日游计划，要详细的天气预测、交通方案和每日预算",
    ]

    print("🚀 增强多Agent系统演示")
    print("系统特性: 多轮迭代 + 动态规划 + 插件扩展")
    print("=" * 60)

    for i, query in enumerate(complex_queries, 1):
        print(f"\n🧪 复杂用例 {i}: {query}")
        print("-" * 50)

        try:
            response = await system.process_query(query)

            print(f"🎯 最终回答:")
            print(f"{response.content}")

            print(f"\n📊 执行详情:")
            print(f"• 迭代轮次: {response.metadata.get('iterations')}")
            print(f"• 使用Agent: {len(response.data.get('agent_registry', []))}")
            print(f"• 置信度: {response.confidence:.2f}")
            print(f"• 完成原因: {response.metadata.get('completion_reason')}")

        except Exception as e:
            print(f"❌ 处理失败: {e}")

        print("-" * 50)
        if i < len(complex_queries):
            input("按 Enter 继续...")

    # 显示性能报告
    print("\n📈 性能报告:")
    performance_report = system.get_performance_report()
    print(f"• 总请求数: {performance_report['overall_metrics']['total_requests']}")
    print(f"• 成功率: {performance_report['overall_metrics']['success_rate']:.1f}%")
    print(f"• 平均响应时间: {performance_report['overall_metrics']['average_response_time']:.2f}秒")
    print(f"• 系统健康状态: {performance_report['system_health']['status']}")

    await system.shutdown_system()


async def demo_iteration_process():
    """演示迭代过程"""
    api_key = "your_openai_api_key_here"  # 替换为你的实际 API 密钥

    if api_key == "your_openai_api_key_here":
        print("❌ 请设置有效的 OpenAI API 密钥")
        return

    system = EnhancedDynamicAgentSystem(api_key)
    await system.initialize_system()

    print("🔄 迭代过程演示")
    print("=" * 50)

    test_query = "帮我规划一次去北京的旅行，需要了解天气、交通方式和预算"

    print(f"测试查询: {test_query}")
    print("-" * 40)

    try:
        response = await system.process_query(test_query)

        # 显示迭代历史
        iteration_history = response.data.get('iteration_result', {}).get('history', [])
        print(f"\n📋 迭代历史 ({len(iteration_history)} 个步骤):")

        for i, step in enumerate(iteration_history, 1):
            print(f"\n步骤 {i}: {step['state'].upper()}")
            print(f"  数据: {json.dumps(step['data'], ensure_ascii=False, indent=2)}")

            if step.get('agent_responses'):
                print(f"  Agent响应: {len(step['agent_responses'])} 个")

    except Exception as e:
        print(f"❌ 处理失败: {e}")

    await system.shutdown_system()


if __name__ == "__main__":
    import json

    # 运行主演示
    asyncio.run(demo_enhanced_system())

    # 运行迭代过程演示
    # asyncio.run(demo_iteration_process())