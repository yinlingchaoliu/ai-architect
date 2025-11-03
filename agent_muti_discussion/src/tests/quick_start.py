#!/usr/bin/env python3
"""
快速开始示例
"""

import asyncio
import sys
import os

# sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ..core.session_manager import DiscussionSession
from ..agents.analyzer_agent import AnalyzerAgent
from ..agents.moderator_agent import ModeratorAgent
from ..expert_agents.tech_expert import TechExpertAgent
from ..expert_agents.business_expert import BusinessExpertAgent


async def quick_start_example():
    """快速开始示例"""
    print("多智能体讨论系统 - 快速开始")
    print("=" * 50)

    # 1. 创建智能体
    print("创建智能体...")
    moderator = ModeratorAgent()
    tech_expert = TechExpertAgent()
    business_expert = BusinessExpertAgent()

    # 2. 创建讨论会话
    session = DiscussionSession(
        session_id="quick_start",
        moderator=moderator,
        experts=[tech_expert, business_expert]
    )

    # 3. 提出问题并开始讨论
    user_question = "我们应该如何设计一个在线教育平台？"
    print(f"用户问题: {user_question}")
    print("开始讨论...")

    result = await session.start_discussion(user_question, max_rounds=4)

    # 4. 显示结果
    print("\n讨论完成!")
    print("=" * 50)
    print(result)

    # 5. 显示统计信息
    stats = session.get_session_stats()
    print(f"\n会话统计:")
    print(f"- 总讨论条目: {stats['total_entries']}")
    print(f"- 专家贡献: {stats['expert_contributions']}")
    print(f"- 总耗时: {stats['duration_seconds']:.2f}秒")


if __name__ == "__main__":
    asyncio.run(quick_start_example())