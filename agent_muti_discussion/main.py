#!/usr/bin/env python3
"""
多智能体讨论决策系统主程序
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.session_manager import DiscussionSession
from src.agents.analyzer_agent import AnalyzerAgent
from src.agents.moderator_agent import ModeratorAgent
from src.expert_agents.tech_expert import TechExpertAgent
from src.expert_agents.business_expert import BusinessExpertAgent
from src.expert_agents.research_expert import ResearchExpertAgent
from src.core.plugin_manager import PluginManager
from src.plugins.web_search import WebSearchPlugin
from src.plugins.knowledge_base import KnowledgeBasePlugin
from src.plugins.reflection_tool import ReflectionToolPlugin
from src.utils.config import ConfigLoader
from src.utils.logger import setup_logger

class MultiAgentSystem:
    def __init__(self, config_path: str = None):
        self.config_loader = ConfigLoader(config_path)
        self.logger = setup_logger('MultiAgentSystem')
        self.plugin_manager = PluginManager()
        self.agents = {}
        self._setup_plugins()
        self._setup_agents()

    def _setup_plugins(self):
        """设置插件"""
        try:
            # 注册插件
            self.plugin_manager.register_plugin("web_search", WebSearchPlugin)
            self.plugin_manager.register_plugin("knowledge_base", KnowledgeBasePlugin)
            self.plugin_manager.register_plugin("reflection_tool", ReflectionToolPlugin)

            # 加载插件配置并实例化
            web_search_config = self.config_loader.get_plugin_config('web_search')
            knowledge_base_config = self.config_loader.get_plugin_config('knowledge_base')
            reflection_tool_config = self.config_loader.get_plugin_config('reflection_tool')

            self.web_search_plugin = self.plugin_manager.load_plugin("web_search", web_search_config)
            self.knowledge_base_plugin = self.plugin_manager.load_plugin("knowledge_base", knowledge_base_config)
            self.reflection_tool_plugin = self.plugin_manager.load_plugin("reflection_tool", reflection_tool_config)

            self.logger.info("插件初始化完成")

        except Exception as e:
            self.logger.error(f"插件初始化失败: {e}")

    def _setup_agents(self):
        """设置智能体"""
        try:
            # 创建智能体
            self.analyzer_agent = AnalyzerAgent()
            self.moderator_agent = ModeratorAgent()

            # 创建专家智能体
            self.tech_expert = TechExpertAgent()
            self.business_expert = BusinessExpertAgent()
            self.research_expert = ResearchExpertAgent()

            # 为智能体配置插件
            experts = [self.tech_expert, self.business_expert, self.research_expert]
            for expert in experts:
                expert.add_plugin("web_search", self.web_search_plugin)
                expert.add_plugin("knowledge_base", self.knowledge_base_plugin)
                expert.add_plugin("reflection_tool", self.reflection_tool_plugin)

            self.moderator_agent.add_plugin("reflection_tool", self.reflection_tool_plugin)

            self.logger.info("智能体初始化完成")

        except Exception as e:
            self.logger.error(f"智能体初始化失败: {e}")

    async def run_discussion(self, user_prompt: str, session_id: str = None):
        """运行讨论会话"""
        try:
            # 创建讨论会话
            session = DiscussionSession(
                session_id=session_id or "default_session",
                moderator=self.moderator_agent,
                experts=[self.tech_expert, self.business_expert, self.research_expert]
            )

            self.logger.info(f"开始讨论会话: {session_id}")
            self.logger.info(f"用户问题: {user_prompt}")

            # 执行讨论
            result = await session.start_discussion(
                user_prompt,
                max_rounds=self.config_loader.get('discussion.max_rounds', 10)
            )

            self.logger.info("讨论完成")
            return result

        except Exception as e:
            self.logger.error(f"讨论过程出错: {e}")
            return f"讨论过程中出现错误: {e}"

    async def close(self):
        """关闭系统资源"""
        await self.plugin_manager.close_all_plugins()


async def main():
    """主函数"""
    if len(sys.argv) > 1:
        user_prompt = " ".join(sys.argv[1:])
    else:
        # 示例问题
        user_prompt = "我们应该如何设计一个面向中小企业的AI客服解决方案？"

    system = MultiAgentSystem()

    try:
        result = await system.run_discussion(user_prompt, "session_001")
        print("\n" + "=" * 50)
        print("最终决策结果：")
        print("=" * 50)
        print(result)
        print("=" * 50)

    finally:
        await system.close()


if __name__ == "__main__":
    asyncio.run(main())