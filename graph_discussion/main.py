# 主程序入口
import asyncio
import os
# 尝试使用绝对导入
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph_discussion.utils.logger import get_logger
from dotenv import load_dotenv, find_dotenv
import os

# 首先创建logger
logger = get_logger("Main")

# 尝试找到并加载.env文件
logger.info("尝试加载环境变量...")
env_path = find_dotenv()
if env_path:
    logger.info(f"找到.env文件: {env_path}")
    load_dotenv(env_path)
    logger.info("环境变量加载成功")
else:
    # 尝试在项目根目录查找.env文件
    root_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(root_env_path):
        logger.info(f"在项目根目录找到.env文件: {root_env_path}")
        load_dotenv(root_env_path)
        logger.info("环境变量加载成功")
    else:
        logger.warning("未找到.env文件，请确保已设置必要的环境变量")

from graph_discussion.graph import create_conference_graph
from graph_discussion.state import ConferenceState

def main():
    """主函数"""
    # 检查API Key
    if not os.getenv("OPENAI_API_KEY"):
        logger.info("请设置OPENAI_API_KEY环境变量", "red")
        return
    
    # 创建图
    graph = create_conference_graph()
    
    # 用户输入
    user_query = input("请输入您的问题或需求: ")
    
    # 初始状态
    initial_state: ConferenceState = {
        "user_query": user_query,
        "current_round": 0,
        "requirement_analysis": "",
        "discussion_topics": [],
        "required_experts": [],
        "moderator_questions": [],
        "expert_discussions": [],
        "current_question": "",
        "round_summaries": [],
        "final_summary": "",
        "implementation_plans": {},
        "should_continue": False,
        "max_rounds": 1
    }

    graph_png=graph.get_graph().draw_mermaid_png()
    with open("graph_discussion.png", "wb") as f:
        f.write(graph_png)
    # 执行图
    logger.info("开始多智能体讨论决策...", "red")
    final_state = graph.invoke(initial_state)

    # 输出结果
    logger.info("\n\n=== 最终结果 ===", "red")
    logger.info(f"最终总结: {final_state['final_summary']}", "white")

    logger.info("\n=== 各专家落地方案 ===", "red")
    for expert, plan in final_state['implementation_plans'].items():
        logger.info(f"{expert}: {plan}", "white")

if __name__ == "__main__":
    main()