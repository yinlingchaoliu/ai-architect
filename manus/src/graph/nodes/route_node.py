# src/graph/nodes/route_node.py
from ..state import AgentState
from typing import Dict, Any
import logging
logger = logging.getLogger(__name__)


async def route_node(state: AgentState) -> Dict[str, Any]:
    """路由节点 - 选择执行智能体"""


    logger.info("Routing node started")

    if not state["subtasks"]:
        # 如果没有子任务，直接使用默认智能体
        return {
            "current_agent": "tool_call_agent",
            "execution_path": state["execution_path"] + ["routing:default"]
        }

    # 获取第一个未完成的子任务
    current_subtask = None
    for subtask in state["subtasks"]:
        if not subtask.get("completed", False):
            current_subtask = subtask
            break

    if not current_subtask:
        # 所有任务已完成
        return {
            "is_complete": True,
            "execution_path": state["execution_path"] + ["routing:complete"]
        }

    recommended_agent = current_subtask.get("recommended_agent", "tool_call_agent")

    logger.info(f"Routed to agent: {recommended_agent} for subtask: {current_subtask['description']}")

    return {
        "current_agent": recommended_agent,
        "current_subtask": current_subtask,
        "execution_path": state["execution_path"] + [f"routing:{recommended_agent}"]
    }