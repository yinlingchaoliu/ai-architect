import sys
from pathlib import Path
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# multi_agent_system/main.py
# !/usr/bin/env python3
"""
多 Agent 智能系统 - 主程序入口
支持动态插件扩展和多轮迭代的智能规划系统
"""

import asyncio
import sys
import os
import argparse
from pathlib import Path

# 添加当前目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_muti.src.core.agent_system import EnhancedDynamicAgentSystem
from agent_muti.src.examples.demo import demo_enhanced_system, demo_iteration_process
from agent_muti.src.examples.interactive_demo import interactive_demo


def setup_environment():
    """设置运行环境"""
    # 确保配置文件存在
    config_path = Path("config.yaml")
    if not config_path.exists():
        print("⚠️  配置文件 config.yaml 不存在，使用默认配置")

    # 检查依赖
    try:
        import openai
        import yaml
        print("✅ 依赖检查通过")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        sys.exit(1)


def print_banner():
    """打印程序横幅"""
    banner = """
    🚀 多 Agent 智能系统 v2.0
    ============================
    特性:
    • 多轮迭代思考 (Think-Plan-Action-Next)
    • 动态插件扩展架构
    • 智能规划策略选择
    • 并行执行优化
    • 完整的监控和诊断
    ============================
    """
    print(banner)


async def run_system(api_key: str, mode: str = "interactive"):
    """运行系统"""
    if not api_key or api_key == "your_openai_api_key_here":
        print("❌ 请设置有效的 OpenAI API 密钥")
        print("使用方法:")
        print("  1. 在 main.py 中直接设置 api_key")
        print("  2. 通过命令行参数: python main.py --api-key YOUR_KEY")
        print("  3. 设置环境变量: MAAS_API_KEY=YOUR_KEY")
        return

    print("🔧 初始化系统...")
    system = EnhancedDynamicAgentSystem(api_key)
    await system.initialize_system()

    try:
        if mode == "demo":
            print("🎬 运行演示模式...")
            await demo_enhanced_system()
        elif mode == "iteration":
            print("🔄 运行迭代演示...")
            await demo_iteration_process()
        elif mode == "interactive":
            print("💬 运行交互模式...")
            await interactive_demo()
        else:
            print(f"❌ 未知模式: {mode}")

    except Exception as e:
        print(f"❌ 系统运行错误: {e}")

    finally:
        print("🔚 关闭系统...")
        await system.shutdown_system()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="多 Agent 智能系统")
    parser.add_argument("--api-key", help="OpenAI API 密钥")
    parser.add_argument("--mode", choices=["demo", "interactive", "iteration"],
                        default="demo", help="运行模式")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径")

    args = parser.parse_args()

    # 设置环境
    setup_environment()
    print_banner()

    # 获取 API 密钥 (按优先级)
    api_key = None
    if args.api_key:
        api_key = args.api_key
    elif os.environ.get("MAAS_API_KEY"):
        api_key = os.environ.get("MAAS_API_KEY")
    else:
        # 尝试从配置文件读取
        try:
            import yaml
            print(args.config)
            with open(args.config, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                api_key = config.get('api').get('openai').get('key')
                print(api_key)
        except:
            pass

    # 运行系统
    asyncio.run(run_system(api_key, args.mode))


if __name__ == "__main__":
    main()