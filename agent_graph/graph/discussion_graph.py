# graph/discussion_graph.py
from langgraph.graph import StateGraph
from typing import Dict, Any, List
import asyncio
from colorama import Fore, Style, init

init(autoreset=True)  # 初始化colorama


class DiscussionGraph:
    def __init__(self):
        self.graph = StateGraph(dict)  # 使用StateGraph并指定状态类型
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
        # 定义流程：分析 -> 主持 -> 专家讨论(通过专家节点) -> 总结
        self.graph.add_edge("analyzer", "moderator")
        # 将专家节点连接起来形成讨论环节
        self.graph.add_edge("moderator", "technical_expert")
        self.graph.add_edge("technical_expert", "business_expert")
        self.graph.add_edge("business_expert", "research_expert")
        # 从最后一个专家节点进行条件判断
        self.graph.add_conditional_edges(
            "research_expert",
            self._should_continue_discussion,
            {
                "continue": "moderator",  # 继续讨论
                "end": "summary"  # 结束讨论
            }
        )
        # 注册summary节点（简单的总结功能）
        self.graph.add_node("summary", self._generate_summary)
        self.graph.add_edge("summary", "__end__")

        self.graph.set_entry_point("analyzer")
        
    def _generate_summary(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """生成讨论总结"""
        # 简单实现，实际项目中可以用更复杂的逻辑
        state["final_summary"] = "根据专家讨论，我们得到了关于问题的综合分析。"
        return state

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