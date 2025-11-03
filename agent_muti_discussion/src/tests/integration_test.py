#!/usr/bin/env python3
"""
集成测试示例
"""

import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ..core.session_manager import DiscussionSession
from ..agents.analyzer_agent import AnalyzerAgent
from ..agents.moderator_agent import ModeratorAgent
from ..expert_agents.tech_expert import TechExpertAgent
from ..expert_agents.business_expert import BusinessExpertAgent
from ..expert_agents.research_expert import ResearchExpertAgent
from ..core.plugin_manager import PluginManager
from ..plugins.web_search import WebSearchPlugin
from ..plugins.knowledge_base import KnowledgeBasePlugin


async def run_integration_test():
    """运行集成测试"""
    print("开始集成测试...")

    # 初始化插件
    plugin_manager = PluginManager()
    web_search_plugin = WebSearchPlugin()
    knowledge_base_plugin = KnowledgeBasePlugin()

    # 创建智能体
    moderator = ModeratorAgent()
    tech_expert = TechExpertAgent()
    business_expert = BusinessExpertAgent()
    research_expert = ResearchExpertAgent()

    # 配置插件
    tech_expert.add_plugin("web_search", web_search_plugin)
    tech_expert.add_plugin("knowledge_base", knowledge_base_plugin)

    business_expert.add_plugin("web_search", web_search_plugin)
    business_expert.add_plugin("knowledge_base", knowledge_base_plugin)

    research_expert.add_plugin("web_search", web_search_plugin)
    research_expert.add_plugin("knowledge_base", knowledge_base_plugin)

    # 创建会话
    session = DiscussionSession(
        session_id="integration_test",
        moderator=moderator,
        experts=[tech_expert, business_expert, research_expert]
    )

    # 测试问题
    test_questions = [
        "如何设计一个智能客服系统？",
        "开发一个移动应用需要考虑哪些因素？",
        "如何评估一个新技术的商业价值？"
    ]

    for i, question in enumerate(test_questions, 1):
        print(f"\n{'=' * 50}")
        print(f"测试问题 {i}: {question}")
        print(f"{'=' * 50}")

        result = await session.start_discussion(question, max_rounds=3)
        print(f"测试结果 {i}:\n{result}")

        # 显示会话统计
        stats = session.get_session_stats()
        print(f"\n会话统计: {stats}")


if __name__ == "__main__":
    asyncio.run(run_integration_test())