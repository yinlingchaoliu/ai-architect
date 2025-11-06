# src/graph/nodes/plan_node.py
from ..state import AgentState
from typing import Dict, Any
import logging

"""规划节点 - 任务拆解和路由"""
from manus.src.agents.agent_pool import AgentPool
from manus.src.utils.config import ConfigManager

logger = logging.getLogger(__name__)


async def plan_node(state: AgentState) -> Dict[str, Any]:


    logger.info("Planning node started")

    # 获取规划智能体
    config_manager = ConfigManager()
    agent_pool = AgentPool(config_manager.get_agents_config())
    await agent_pool.initialize()

    planning_agent = agent_pool.get_agent("planning_agent")
    if not planning_agent:
        raise ValueError("Planning agent not found")

    # 执行规划
    plan_result = await planning_agent.run({
        "task": state["current_task"],
        "context": {}
    })

    logger.info(f"Planning completed: {len(plan_result.get('subtasks', []))} subtasks")

    return {
        "subtasks": plan_result.get("subtasks", []),
        "plan": plan_result,
        "execution_path": state["execution_path"] + ["planning"]
    }