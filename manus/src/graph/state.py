# src/graph/state.py
from typing import TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """智能体工作流状态"""
    # 消息历史
    messages: List[BaseMessage]
    # 当前任务
    current_task: str
    # 子任务列表
    subtasks: List[Dict[str, Any]]
    # 当前执行的智能体
    current_agent: str
    # 工具执行结果
    tool_results: List[Dict[str, Any]]
    # 执行路径记录
    execution_path: List[str]
    # 是否完成
    is_complete: bool
    # 规划结果
    plan: Optional[Dict[str, Any]]