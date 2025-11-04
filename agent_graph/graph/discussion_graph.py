# graph/discussion_graph.py
# from langgraph.graph import Graph
from typing import Dict, Any, List
import asyncio
from colorama import Fore, Style, init
from langchain_core.runnables.graph import Graph

init(autoreset=True)  # 初始化colorama


class DiscussionGraph:
    def __init__(self):
        self.graph = Graph()
        self.agents = {}
        self.logger = self._setup_logger()

    def _setup_logger(self):
        """设置彩色日志"""
        import logging
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger("discussion")

    def register_agent(self, agent_name: str, agent):
        """注册智能体"""
        self.agents[agent_name] = agent
        self.graph.add_node(agent_name, agent.generate_response)

    def build_graph(self):
        """构建讨论流程图"""
        # 定义流程：分析 -> 主持 -> 专家讨论 -> 总结
        self.graph.add_edge("analyzer", "moderator")
        self.graph.add_edge("moderator", "expert_discussion")
        self.graph.add_conditional_edges(
            "expert_discussion",
            self._should_continue_discussion,
            {
                "continue": "moderator",
                "end": "summary"
            }
        )
        self.graph.add_edge("summary", "__end__")

        self.graph.set_entry_point("analyzer")

    def _should_continue_discussion(self, state: Dict[str, Any]) -> str:
        """判断是否继续讨论"""
        discussion_rounds = state.get("discussion_rounds", 0)
        max_rounds = state.get("max_rounds", 5)
        consensus_reached = state.get("consensus_reached", False)

        if consensus_reached or discussion_rounds >= max_rounds:
            return "end"
        return "continue"

    async def run_discussion(self, user_query: str) -> Dict[str, Any]:
        """运行讨论流程"""
        state = {
            "user_query": user_query,
            "discussion_history": [],
            "discussion_rounds": 0,
            "max_rounds": 5,
            "consensus_reached": False,
            "final_summary": "",
            "expert_contributions": {}
        }

        # 运行图
        compiled_graph = self.graph.compile()

        # 执行流程
        result = await compiled_graph.ainvoke(state)

        return result