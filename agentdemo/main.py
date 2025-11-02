#!/usr/bin/env python3
"""
多 Agent 智能系统 - 增强版
专注于超时处理和日志记录的健壮系统
"""

import asyncio
import sys
import os
import argparse
from pathlib import Path
import yaml

# 添加当前目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.agent_system import EnhancedDynamicAgentSystem
from src.utils.logger_manager import logger_manager


def setup_environment():
    """设置运行环境"""
    # 确保配置文件存在
    config_path = Path("config.yaml")
    if not config_path.exists():
        print("⚠️  配置文件 config.yaml 不存在，使用默认配置")
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"❌ 配置文件读取失败: {e}")
        return None


def print_banner():
    """打印程序横幅"""
    banner = """
    🚀 多 Agent 智能系统 - 增强版 v1.0
    ===========================================
    特性:
    • 增强的超时处理机制
    • 动态超时调整和预警
    • 结构化日志记录系统
    • 详细的性能监控
    • 优雅降级和重试机制
    ===========================================
    """
    print(banner)


async def run_system(api_key: str, mode: str = "demo"):
    """运行系统"""
    if not api_key or api_key == "your_openai_api_key_here":
        print("❌ 请设置有效的 OpenAI API 密钥")
        print("使用方法:")
        print("  1. 在 config.yaml 中设置 api.openai.key")
        print("  2. 通过命令行参数: python main.py --api-key YOUR_KEY")
        print("  3. 设置环境变量: AGENTDEMO_API_KEY=YOUR_KEY")
        return

    # 加载配置
    config = setup_environment()
    if not config:
        print("❌ 配置加载失败")
        return

    # 初始化日志系统
    logger_manager.setup_logging(config.get('logging', {}))

    print("🔧 初始化系统...")
    system = EnhancedDynamicAgentSystem(api_key, config)
    await system.initialize_system()

    try:
        if mode == "demo":
            print("🎬 运行演示模式...")
            await run_demo(system)
        elif mode == "interactive":
            print("💬 运行交互模式...")
            await run_interactive(system)
        else:
            print(f"❌ 未知模式: {mode}")

    except Exception as e:
        print(f"❌ 系统运行错误: {e}")
        logger_manager.log_system_event(
            f"系统运行错误: {e}",
            level="ERROR"
        )

    finally:
        print("🔚 关闭系统...")
        await system.shutdown_system()


async def run_demo(system):
    """运行演示"""
    demo_queries = [
        "我想去北京旅游3天，帮我规划一下行程",
        "查询上海明天的天气",
        "从北京到上海有哪些交通方式？预算多少？",
        "帮我找一下杭州的酒店，预算500元一晚"
    ]
    
    for i, query in enumerate(demo_queries, 1):
        print(f"\n{'='*50}")
        print(f"演示 {i}/{len(demo_queries)}: {query}")
        print(f"{'='*50}")
        
        try:
            result = await system.process_query(query)
            
            print(f"\n✅ 处理结果:")
            print(f"   迭代次数: {result.get('iteration_count', 0)}")
            print(f"   最终置信度: {result.get('final_result', {}).get('confidence_score', 0):.2f}")
            print(f"   响应内容: {result.get('final_result', {}).get('content', '')}")
            
            # 显示性能指标
            performance = result.get('performance', {})
            if performance:
                print(f"\n📊 性能指标:")
                print(f"   总超时次数: {performance.get('total_timeouts', 0)}")
                print(f"   总重试次数: {performance.get('total_retries', 0)}")
                
        except Exception as e:
            print(f"❌ 查询处理失败: {e}")
            logger_manager.log_system_event(
                f"演示查询失败: {query} - {e}",
                level="ERROR"
            )
        
        # 等待一下再执行下一个查询
        await asyncio.sleep(2)


async def run_interactive(system):
    """运行交互模式"""
    print("\n💬 交互模式已启动，输入 'quit' 或 'exit' 退出")
    
    while True:
        try:
            query = input("\n🤔 请输入您的问题: ").strip()
            
            if query.lower() in ['quit', 'exit', '退出']:
                print("👋 再见！")
                break
            
            if not query:
                continue
            
            print("🔄 处理中...")
            result = await system.process_query(query)
            
            # 显示结果
            final_result = result.get('final_result', {})
            if final_result.get('error'):
                print(f"❌ 处理失败: {final_result['error']}")
            else:
                print(f"\n✅ 回答: {final_result.get('content', '')}")
                
                # 显示详细信息
                print(f"\n📊 详细信息:")
                print(f"   迭代次数: {result.get('iteration_count', 0)}")
                print(f"   置信度: {final_result.get('confidence_score', 0):.2f}")
                
                # 显示使用的Agent
                agent_responses = final_result.get('agent_responses', {})
                if agent_responses:
                    print(f"   使用的Agent: {', '.join(agent_responses.keys())}")
                
        except KeyboardInterrupt:
            print("\n👋 用户中断，再见！")
            break
        except Exception as e:
            print(f"❌ 处理错误: {e}")
            logger_manager.log_system_event(
                f"交互查询失败: {query} - {e}",
                level="ERROR"
            )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="多 Agent 智能系统 - 增强版")
    parser.add_argument("--api-key", help="OpenAI API 密钥")
    parser.add_argument("--mode", choices=["demo", "interactive"],
                        default="demo", help="运行模式")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径")

    args = parser.parse_args()

    # 设置环境
    config = setup_environment()
    print_banner()

    # 获取 API 密钥 (按优先级)
    api_key = None
    if args.api_key:
        api_key = args.api_key
    elif os.environ.get("AGENTDEMO_API_KEY"):
        api_key = os.environ.get("AGENTDEMO_API_KEY")
    elif config and config.get('api', {}).get('openai', {}).get('key'):
        api_key = config['api']['openai']['key']

    api_key = "hk-fwuzp810000596427a889f4a9def096b062f5a0d01ac0abd"
    # 运行系统
    asyncio.run(run_system(api_key, args.mode))


if __name__ == "__main__":
    main()
