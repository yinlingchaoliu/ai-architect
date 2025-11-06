# src/graph/nodes/execute_node.py
from typing import Dict, Any
import logging

from src.graph.state import AgentState

"""执行节点 - 智能体执行任务"""

logger = logging.getLogger(__name__)

# 全局agent_pool引用，将在main.py中初始化
global_agent_pool = None

def set_agent_pool(agent_pool):
    """设置全局agent_pool引用"""
    global global_agent_pool
    global_agent_pool = agent_pool


async def execute_node(state: AgentState) -> Dict[str, Any]:


    logger.info(f"Execute node started with agent: {state['current_agent']}")

    # 使用全局agent_pool引用
    if not global_agent_pool:
        raise ValueError("Global agent pool not initialized")
    
    agent_pool = global_agent_pool

    current_agent = agent_pool.get_agent(state["current_agent"])
    
    # 智能体降级机制：当请求的智能体不存在时，尝试使用可用的智能体
    if not current_agent:
        logger.warning(f"Agent not found: {state['current_agent']}, attempting to fall back to an available agent")
        
        # 尝试使用code_agent作为首选替代
        fallback_agent = agent_pool.get_agent("code_agent")
        
        # 如果code_agent也不存在，尝试获取第一个可用的智能体
        if not fallback_agent and hasattr(agent_pool, 'list_agents'):
            available_agents = agent_pool.list_agents()
            if available_agents:
                # 获取第一个可用智能体的名称
                first_agent_name = available_agents[0].get('name')
                fallback_agent = agent_pool.get_agent(first_agent_name)
                logger.info(f"Using first available agent: {first_agent_name} as fallback")
        
        # 如果找到了替代智能体，使用它
        if fallback_agent:
            current_agent = fallback_agent
            logger.info(f"Fallback to agent: {getattr(current_agent, 'name', 'unknown')}")
        else:
            # 如果仍然没有找到智能体，抛出错误
            raise ValueError(f"Agent not found: {state['current_agent']}, and no fallback agent available")
    
    # 确保agent有llm_manager
    if not hasattr(current_agent, 'llm_manager') or current_agent.llm_manager is None:
        current_agent.llm_manager = agent_pool.llm_manager

    # 准备任务输入
    task_description = state["current_subtask"]["description"] if state.get("current_subtask") else state[
        "current_task"]

    try:
        # 执行智能体
        result = await current_agent.run({
            "task": task_description,
            "context": {
                "original_task": state["current_task"],
                "subtask_id": state["current_subtask"]["id"] if state.get("current_subtask") else None
            }
        })
        
        # 确保结果包含必要的字段
        if not isinstance(result, dict):
            result = {"status": "unknown", "content": str(result)}
            
        # 添加缺失信息标记
        result["missing_info_captured"] = True
        
    except Exception as e:
        # 捕获所有异常，作为降级处理
        error_message = str(e)
        logger.error(f"Error during agent execution: {error_message}")
        
        # 创建降级结果，包含错误信息和缺失信息
        result = {
            "status": "failed",
            "error": error_message,
            "missing_info": {
                "error_type": type(e).__name__,
                "message": error_message,
                "original_task": state["current_task"],
                "target_agent": state["current_agent"],
                "fallback_agent": getattr(current_agent, 'name', 'unknown')
            },
            "missing_info_captured": True
        }

    # 标记子任务完成
    updated_subtasks = state["subtasks"]
    if state.get("current_subtask"):
        for subtask in updated_subtasks:
            if subtask["id"] == state["current_subtask"]["id"]:
                subtask["completed"] = True
                subtask["result"] = result
                # 添加缺失信息标记到子任务
                if "missing_info" in result:
                    subtask["missing_info"] = result["missing_info"]
                break

    logger.info(f"Execution completed: {result.get('status', 'unknown')}")

    return {
        "tool_results": state["tool_results"] + [result],
        "subtasks": updated_subtasks,
        "execution_path": state["execution_path"] + [f"execute:{state['current_agent']}"]
    }