# src/graph/nodes/check_node.py
from ..state import AgentState
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


async def check_node(state: AgentState) -> Dict[str, Any]:
    """检查节点 - 验证任务完成度"""
    logger.info("Check node started")

    if not state["subtasks"]:
        # 没有子任务，直接完成
        return {
            "is_complete": True,
            "execution_path": state["execution_path"] + ["check:complete_no_subtasks"]
        }

    # 检查是否所有子任务都完成
    all_completed = all(subtask.get("completed", False) for subtask in state["subtasks"])

    if all_completed:
        logger.info("All subtasks completed")
        return {
            "is_complete": True,
            "execution_path": state["execution_path"] + ["check:complete_all_subtasks"]
        }
    else:
        # 还有未完成的任务，继续执行
        remaining = [subtask for subtask in state["subtasks"] if not subtask.get("completed", False)]
        logger.info(f"Remaining subtasks: {len(remaining)}")
        return {
            "is_complete": False,
            "execution_path": state["execution_path"] + ["check:incomplete"]
        }