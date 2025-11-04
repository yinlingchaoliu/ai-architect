# main.py
import asyncio
import os
from agents.analyzer_agent import AnalyzerAgent
from agents.moderator_agent import ModeratorAgent
from agents.experts.technical_expert import TechnicalExpert
from agents.experts.business_expert import BusinessExpert
from agents.experts.research_expert import ResearchExpert
# from tools.web_search import WebSearchTool
# from tools.rag_system import RAGSystem
from graph.discussion_graph import DiscussionGraph
from colorama import Fore, Style


class MultiAgentDiscussionSystem:
    def __init__(self):
        self.discussion_graph = DiscussionGraph()
        self._setup_agents()
        self._setup_tools()

    def _setup_agents(self):
        """设置所有智能体"""
        # 核心角色
        analyzer = AnalyzerAgent()
        moderator = ModeratorAgent()

        # 专家角色（可插拔）
        technical_expert = TechnicalExpert()
        business_expert = BusinessExpert()
        research_expert = ResearchExpert()

        # 注册智能体
        self.discussion_graph.register_agent("analyzer", analyzer)
        self.discussion_graph.register_agent("moderator", moderator)
        self.discussion_graph.register_agent("technical_expert", technical_expert)
        self.discussion_graph.register_agent("business_expert", business_expert)
        self.discussion_graph.register_agent("research_expert", research_expert)

        # 构建图
        self.discussion_graph.build_graph()

    def _setup_tools(self):
        """设置工具系统"""
        # web_search = WebSearchTool()
        # rag_system = RAGSystem()

        # 为专家注册工具
        experts = ["technical_expert", "business_expert", "research_expert"]
        for expert_name in experts:
            expert = self.discussion_graph.agents[expert_name]
            # expert.register_tool("web_search", web_search.search)
            # expert.register_tool("rag_search", rag_system.search)

    async def run(self, user_query: str):
        """运行多智能体讨论"""
        print(f"\n{Fore.CYAN}=== 多智能体讨论系统启动 ==={Style.RESET_ALL}")
        print(f"{Fore.YELLOW}用户问题: {user_query}{Style.RESET_ALL}\n")

        result = await self.discussion_graph.run_discussion(user_query)

        print(f"\n{Fore.GREEN}=== 讨论完成 ==={Style.RESET_ALL}")
        print(f"{Fore.CYAN}最终总结: {result.get('final_summary', '')}{Style.RESET_ALL}")

        return result


async def main():
    # 设置API密钥
    os.environ["OPENAI_API_KEY"] = "your-openai-api-key"
    os.environ["SERPAPI_KEY"] = "your-serpapi-key"

    system = MultiAgentDiscussionSystem()

    # 示例问题
    user_query = "我们应该如何设计一个面向中小企业的AI客服系统？请考虑技术实现、商业价值和用户体验。"

    await system.run(user_query)


if __name__ == "__main__":
    asyncio.run(main())