#!/usr/bin/env python3
"""
性能测试
"""

import asyncio
import time
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ..core.session_manager import DiscussionSession
from ..agents.moderator_agent import ModeratorAgent
from ..expert_agents.tech_expert import TechExpertAgent
from ..expert_agents.business_expert import BusinessExpertAgent


async def performance_test():
    """性能测试"""
    print("开始性能测试...")

    test_cases = [
        {"experts": 2, "rounds": 3, "description": "小型讨论"},
        {"experts": 3, "rounds": 5, "description": "中型讨论"},
        {"experts": 4, "rounds": 8, "description": "大型讨论"}
    ]

    for test_case in test_cases:
        print(f"\n测试: {test_case['description']}")
        print(f"专家数: {test_case['experts']}, 轮次: {test_case['rounds']}")

        # 创建智能体
        moderator = ModeratorAgent()
        experts = [TechExpertAgent() for _ in range(test_case['experts'])]

        session = DiscussionSession(
            session_id=f"perf_test_{test_case['experts']}",
            moderator=moderator,
            experts=experts
        )

        start_time = time.time()

        # 运行讨论
        result = await session.start_discussion(
            "测试性能问题",
            max_rounds=test_case['rounds']
        )

        end_time = time.time()
        duration = end_time - start_time

        stats = session.get_session_stats()

        print(f"耗时: {duration:.2f}秒")
        print(f"讨论条目: {stats['total_entries']}")
        print(f"平均响应时间: {duration / max(stats['total_entries'], 1):.2f}秒/条")


if __name__ == "__main__":
    asyncio.run(performance_test())