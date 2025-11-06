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

    # 确保在规划节点输出中包含missing_resources信息
    result = {
        "subtasks": plan_result.get("subtasks", []),
        "plan": plan_result,
        "execution_path": state["execution_path"] + ["planning"],
        "missing_resources": plan_result.get("missing_resources", {
            "agents": [],
            "tools": [],
            "errors": []
        })
    }
    
    # 如果有缺少的资源，记录日志提醒
    missing_agents = result["missing_resources"]["agents"]
    missing_tools = result["missing_resources"]["tools"]
    missing_errors = result["missing_resources"]["errors"]
    if missing_agents or missing_tools or missing_errors:
        logger.info(f"Missing resources identified: agents={missing_agents}, tools={missing_tools}, errors={missing_errors}")
        logger.info("建议补充这些资源以提高任务执行效果")
    
    return result