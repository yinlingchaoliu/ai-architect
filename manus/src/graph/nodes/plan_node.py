# src/graph/nodes/plan_node.py
from typing import Dict, Any
import logging
from src.agents import AgentPool
from src.utils.config import ConfigManager
from src.graph.state import AgentState

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