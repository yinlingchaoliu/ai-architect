# src/agents/agent_pool.py
from typing import Dict, Any, List, Optional
import asyncio
from .base import BaseAgent
from .tool_call import ToolCallAgent
from .planning_agent import PlanningAgent


class AgentPool:
    """智能体池 - 管理多个智能体的生命周期"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._agents: Dict[str, BaseAgent] = {}
        self._agent_configs = config.get("agents", {})
        self.llm_manager = None

    async def initialize(self) -> None:
        """初始化智能体池"""
        # 初始化规划智能体
        planning_config = self._agent_configs.get("planning_agent", {})
        planning_agent = PlanningAgent("planning_agent", planning_config)
        planning_agent.llm_manager = self.llm_manager
        # 设置agent_pool引用到planning_agent
        planning_agent._agent_pool = self
        await planning_agent.initialize()
        self._agents["planning_agent"] = planning_agent

        # 初始化专用智能体
        specialized_agents = self._agent_configs.get("specialized_agents", {})
        for agent_name, agent_config in specialized_agents.items():
            agent = await self._create_agent(agent_name, agent_config)
            if agent:
                self._agents[agent_name] = agent

    async def _create_agent(self, name: str, config: Dict[str, Any]) -> Optional[BaseAgent]:
        """创建智能体实例"""
        agent_type = config.get("type", "tool_call")

        if agent_type == "tool_call":
            agent = ToolCallAgent(name, config)
        elif agent_type == "planning":
            agent = PlanningAgent(name, config)
        else:
            # 默认使用 ToolCallAgent
            agent = ToolCallAgent(name, config)

        agent.llm_manager = self.llm_manager
        # 设置agent_pool引用到智能体
        if hasattr(agent, '_agent_pool'):
            agent._agent_pool = self
        await agent.initialize()
        return agent

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """获取智能体"""
        return self._agents.get(name)

    async def execute_with_agent(self, agent_name: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """使用指定智能体执行任务"""
        agent = self.get_agent(agent_name)
        if not agent:
            return {"error": f"Agent not found: {agent_name}"}

        return await agent.run(task)

    def list_agents(self) -> List[Dict[str, Any]]:
        """列出所有可用智能体"""
        agents_info = []
        for name, agent in self._agents.items():
            agents_info.append({
                "name": name,
                "type": agent.__class__.__name__,
                "status": agent.state.status,
                "capabilities": getattr(agent, 'available_tools', [])
            })
        return agents_info

    async def route_task(self, task: str, context: Dict[str, Any] = None) -> str:
        """路由任务到合适的智能体"""
        # 使用规划智能体进行路由决策
        planning_agent = self.get_agent("planning_agent")
        if planning_agent:
            plan_result = await planning_agent.run({
                "task": task,
                "context": context or {}
            })

            # 返回推荐的主要智能体
            if plan_result.get("subtasks"):
                return plan_result["subtasks"][0].get("recommended_agent", "tool_call_agent")

        # 默认回退到工具调用智能体
        return "tool_call_agent"

    async def close(self):
        """关闭所有智能体"""
        for agent in self._agents.values():
            if hasattr(agent, 'close'):
                await agent.close()