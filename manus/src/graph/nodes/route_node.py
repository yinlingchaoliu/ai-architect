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

    # 获取推荐的智能体
    recommended_agent = current_subtask.get("recommended_agent")
    
    # 避免将任务路由回planning_agent，这会导致无限递归
    if recommended_agent == "planning_agent":
        # 尝试优先使用code_agent，因为它最通用且可能存在
        recommended_agent = "code_agent"
        logger.warning(f"Avoiding recursion: Changed planning_agent to {recommended_agent} for subtask execution")
    
    # 如果推荐的智能体不是code_agent，且系统中可能存在code_agent，优先使用code_agent
    if recommended_agent not in ["planning_agent", "code_agent"]:
        # 优先使用code_agent来执行代码相关任务
        if "code" in current_subtask.get("description", "").lower() or "python" in current_subtask.get("description", "").lower():
            recommended_agent = "code_agent"
            logger.info(f"Prioritizing code_agent for code-related task")

    logger.info(f"Routed to agent: {recommended_agent} for subtask: {current_subtask['description']}")

    return {
        "current_agent": recommended_agent,
        "current_subtask": current_subtask,
        "execution_path": state["execution_path"] + [f"routing:{recommended_agent}"]
    }