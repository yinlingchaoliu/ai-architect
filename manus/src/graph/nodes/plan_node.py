# src/graph/nodes/plan_node.py
from typing import Dict, Any
import logging
from src.graph.state import AgentState

logger = logging.getLogger(__name__)

# 全局agent_pool引用，将在main.py中初始化
global_agent_pool = None


def set_agent_pool(agent_pool):
    """设置全局agent_pool引用"""
    global global_agent_pool
    global_agent_pool = agent_pool


async def plan_node(state: AgentState) -> Dict[str, Any]:
    logger.info("Planning node started")

    # 获取规划智能体
    if not global_agent_pool:
        raise ValueError("Global agent pool not initialized")
        
    planning_agent = global_agent_pool.get_agent("planning_agent")
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