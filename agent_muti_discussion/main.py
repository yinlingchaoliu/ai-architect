import os
import sys
from logging import Logger
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.session_manager import SessionManager
from src.utils.logger import logger

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

class MultiAgentDiscussionSystem:
    """多智能体讨论系统主类"""

    def __init__(self, max_rounds: int = 10):
        self.session_manager = SessionManager(max_rounds=max_rounds)
        self.max_rounds = max_rounds
        logger.info(f"多智能体讨论系统初始化完成，最大讨论轮数设置为 {max_rounds}")

    def process_query(self, user_query: str) -> Dict[str, Any]:
        """处理用户查询"""
        try:
            logger.debug(f"处理用户查询: {user_query}")
            result = self.session_manager.process_user_input(user_query)
            return result
        except Exception as e:
            logger.error(f"处理用户查询异常: {str(e)}")
            return {
                "error": f"系统处理异常: {str(e)}",
                "discussion_rounds": 0,
                "final_summary": "抱歉，系统处理过程中出现异常。"
            }

    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        return {
            "system_name": "多智能体讨论决策系统",
            "version": "1.0",
            "agents": [
                "需求分析师",
                "会议主持人",
                "技术专家",
                "商业专家",
                "研究专家"
            ],
            "features": [
                "需求分析",
                "多轮专家讨论",
                "一致性检查",
                "自动总结"
            ]
        }


def main():
    """主函数"""
    # 可以在这里修改默认的最大讨论轮数，默认为10次
    max_rounds = 10
    system = MultiAgentDiscussionSystem(max_rounds=max_rounds)

    logger.info("=== 多智能体讨论决策系统 ===",color=logger.RED)
    logger.debug(system.get_system_info())
    logger.critical("\n系统已就绪，请输入您的问题（输入 'quit' 退出）：")

    while True:
        try:
            user_input = input("\n用户问题: ").strip()

            if user_input.lower() in ['quit', 'exit', '退出']:
                print("感谢使用，再见！")
                break

            if not user_input:
                print("问题不能为空，请重新输入。")
                continue

            print("正在处理，请稍候...")
            result = system.process_query(user_input)

            # 显示结果
            print("\n" + "=" * 50)
            print("最终总结:")
            print("=" * 50)
            print(result["final_summary"]["summary"])

            print("\n讨论统计:")
            print(f"- 讨论轮次: {result['discussion_rounds']}")
            print(f"- 专家意见数: {result['final_summary']['total_opinions']}")
            print(f"- 共识达成: {result['final_summary']['consensus_result']['consensus_achieved']}")

        except KeyboardInterrupt:
            print("\n\n用户中断，程序退出。")
            break
        except Exception as e:
            print(f"系统错误: {str(e)}")


if __name__ == "__main__":
    # setup_environment()
    # 创建必要的目录
    os.makedirs('logs', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    main()