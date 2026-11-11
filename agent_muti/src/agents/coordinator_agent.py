# multi_agent_system/agents/coordinator_agent.py
import asyncio
import json
from typing import Dict, List, Any, Optional, Callable

from .plugin_agent import PluginAgent
from ..models.agent_models import AgentType, AgentResponse
from ..core.iteration_controller import IterationController
from ..prompt.constants import SUMMARY_PROMPT, summary_prompt


class EnhancedCoordinatorAgent(PluginAgent):
    """增强的主协调 Agent - 支持多轮迭代"""

    def __init__(self, name: str = "智能协调器", description: str = "支持多轮迭代的动态协调Agent"):
        super().__init__(AgentType.COORDINATOR, name, description)
        self.agent_registry: Dict[str, PluginAgent] = {}
        self.planning_strategies: Dict[str, Callable] = {}
        self.iteration_controller = IterationController(max_iterations=5)
        self.conversation_memory: List[Dict] = []

    def register_agent(self, agent: PluginAgent):
        """注册 Agent"""
        self.agent_registry[agent.name] = agent
        print(f"✅ 注册 Agent: {agent.name} ({agent.agent_type.value})")

    def unregister_agent(self, agent_name: str):
        """注销 Agent"""
        if agent_name in self.agent_registry:
            del self.agent_registry[agent_name]
            print(f"❌ 注销 Agent: {agent_name}")

    def register_planning_strategy(self, name: str, strategy_func: Callable):
        """注册规划策略"""
        self.planning_strategies[name] = strategy_func

    async def process_request(self, query: str, context: Dict[str, Any] = None) -> AgentResponse:
        """处理请求 - 支持多轮迭代"""
        # 更新对话记忆
        self.conversation_memory.append({
            "role": "user",
            "content": query,
            "timestamp": asyncio.get_event_loop().time()
        })

        # 构建执行上下文
        execution_context = {
            "last_query": query,
            "conversation_history": self.conversation_memory[-10:],  # 最近10轮对话
            "available_agents": list(self.agent_registry.keys()),
            **(context or {})
        }

        print("🚀 开始多轮迭代执行...")
        print(f"可用Agent: {execution_context['available_agents']}")

        # 执行多轮迭代
        iteration_result = await self.iteration_controller.execute_iteration_cycle(
            query, execution_context, self, execution_context['available_agents']
        )

        # 生成最终响应
        final_response = await self._generate_final_response(query, iteration_result)

        # 更新对话记忆
        self.conversation_memory.append({
            "role": "assistant",
            "content": final_response,
            "timestamp": asyncio.get_event_loop().time(),
            "iteration_data": iteration_result
        })

        return AgentResponse(
            agent_type=self.agent_type,
            content=final_response,
            data={
                "query": query,
                "iteration_result": iteration_result,
                "agent_registry": list(self.agent_registry.keys()),
                "conversation_length": len(self.conversation_memory)
            },
            confidence=iteration_result.get("final_result", {}).get("confidence_score", 0.8),
            metadata={
                "iterations": iteration_result["iteration_count"],
                "strategy": "multi_iteration",
                "completion_reason": "normal" if iteration_result["iteration_count"] < 5 else "max_iterations"
            }
        )

    async def _generate_final_response(self, query: str, iteration_result: Dict) -> str:
        """生成最终响应"""
        final_data = iteration_result["final_result"]
        agent_responses = final_data.get("agent_responses", {})

        if not agent_responses:
            return "抱歉，我无法获取足够的信息来回答您的问题。"

        # 构建整合提示
        response_summaries = []
        for agent_name, response in agent_responses.items():
            response_summaries.append(f"## {agent_name}\n{response.content}")
        summaries = "\n".join(response_summaries)

        # 构建整合提示
        prompt = summary_prompt(query, summaries, iteration_result['iteration_count'],
                                                len(agent_responses))        
        messages = [
            {"role": "system",
             "content": SUMMARY_PROMPT},
            {"role": "user", "content": prompt}
        ]
        self.set_step("summary")
        return await self._call_llm(messages)
