# multi_agent_system/examples/interactive_demo.py
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..core.agent_system import EnhancedDynamicAgentSystem
from ..models.agent_models import AgentResponse


async def interactive_demo():
    """交互式演示"""
    api_key = "your_openai_api_key_here"  # 替换为你的实际 API 密钥

    if api_key == "your_openai_api_key_here":
        print("❌ 请设置有效的 OpenAI API 密钥")
        print("请在 interactive_demo.py 中设置你的 API 密钥")
        return

    # 创建系统
    system = EnhancedDynamicAgentSystem(api_key)
    await system.initialize_system()

    print("🤖 增强多Agent旅行规划系统")
    print("=" * 60)
    print("系统特性:")
    print("• 多轮迭代思考 (Think-Plan-Action-Next)")
    print("• 动态插件扩展")
    print("• 智能规划策略")
    print("• 并行执行优化")
    print("=" * 60)
    print("可用命令:")
    print("• 'status' - 查看系统状态")
    print("• 'performance' - 查看性能报告")
    print("• 'agents' - 查看已注册Agent")
    print("• 'clear' - 清除对话历史")
    print("• 'quit' - 退出程序")
    print("=" * 60)

    while True:
        try:
            user_input = input("\n💬 您的旅行需求: ").strip()

            if user_input.lower() in ['quit', 'exit', '退出']:
                print("👋 感谢使用增强多Agent系统!")
                break
            elif user_input.lower() == 'status':
                status = system.get_system_status()
                print("🔧 系统状态:")
                print(f"   已注册Agent: {status['registered_agents']}")
                print(f"   对话记忆: {status['conversation_memory']} 条")
                print(f"   系统健康: {status['system_health']['status']}")
                if status['system_health']['issues']:
                    print(f"   问题: {status['system_health']['issues']}")
                continue
            elif user_input.lower() == 'performance':
                report = system.get_performance_report()
                print("📊 性能报告:")
                print(f"   总请求数: {report['overall_metrics']['total_requests']}")
                print(f"   成功率: {report['overall_metrics']['success_rate']:.1f}%")
                print(f"   平均响应时间: {report['overall_metrics']['average_response_time']:.2f}秒")
                print(f"   最大并发Agent: {report['overall_metrics']['max_concurrent_agents']}")

                if report['agent_performance']:
                    print("\n   Agent性能:")
                    for agent, perf in report['agent_performance'].items():
                        print(
                            f"     {agent}: {perf['success_rate']:.1f}% 成功率, 平均 {perf['average_execution_time']:.2f}秒")
                continue
            elif user_input.lower() == 'agents':
                status = system.get_system_status()
                print("🤖 已注册Agent:")
                for agent in status['registered_agents']:
                    print(f"   • {agent}")
                continue
            elif user_input.lower() == 'clear':
                system.coordinator.conversation_memory.clear()
                print("🗑️  对话历史已清除")
                continue

            if not user_input:
                continue

            print("🔄 多轮迭代规划中...")
            response = await system.process_query(user_input)

            print(f"\n🎯 最终回答:")
            print(f"{response.content}")

            print(f"\n📈 执行统计:")
            print(f"• 迭代轮次: {response.metadata.get('iterations')}")
            print(f"• 完成原因: {response.metadata.get('completion_reason')}")
            print(f"• 整体置信度: {response.confidence:.2f}")
            print(f"• 使用Agent: {', '.join(response.data.get('agent_registry', []))}")

        except KeyboardInterrupt:
            print("\n\n👋 程序被用户中断")
            break
        except Exception as e:
            print(f"❌ 系统错误: {e}")

    await system.shutdown_system()


if __name__ == "__main__":
    asyncio.run(interactive_demo())