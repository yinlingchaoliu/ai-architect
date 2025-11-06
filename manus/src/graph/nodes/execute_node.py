# src/graph/nodes/execute_node.py
from typing import Dict, Any
import logging

from src.agents import AgentPool
from src.graph.state import AgentState
from src.utils.config import ConfigManager

"""执行节点 - 智能体执行任务"""
# from src.agents.agent_pool import AgentPool
# from src.utils.config import ConfigManager

logger = logging.getLogger(__name__)


async def execute_node(state: AgentState) -> Dict[str, Any]:


    logger.info(f"Execute node started with agent: {state['current_agent']}")

    config_manager = ConfigManager()
    agent_pool = AgentPool(config_manager.get_agents_config())
    await agent_pool.initialize()

    current_agent = agent_pool.get_agent(state["current_agent"])
    if not current_agent:
        raise ValueError(f"Agent not found: {state['current_agent']}")

    # 准备任务输入
    task_description = state["current_subtask"]["description"] if state.get("current_subtask") else state[
        "current_task"]

    # 执行智能体
    result = await current_agent.run({
        "task": task_description,
        "context": {
            "original_task": state["current_task"],
            "subtask_id": state["current_subtask"]["id"] if state.get("current_subtask") else None
        }
    })

    # 标记子任务完成
    updated_subtasks = state["subtasks"]
    if state.get("current_subtask"):
        for subtask in updated_subtasks:
            if subtask["id"] == state["current_subtask"]["id"]:
                subtask["completed"] = True
                subtask["result"] = result
                break

    logger.info(f"Execution completed: {result.get('status', 'unknown')}")

    return {
        "tool_results": state["tool_results"] + [result],
        "subtasks": updated_subtasks,
        "execution_path": state["execution_path"] + [f"execute:{state['current_agent']}"]
    }