# src/graph/workflow.py
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Any
from langchain_core.messages import BaseMessage
from src.graph.state import AgentState
from src.graph.nodes.plan_node import plan_node
from src.graph.nodes.route_node import route_node
from src.graph.nodes.execute_node import execute_node
from src.graph.nodes.check_node import check_node
import logging

logger = logging.getLogger(__name__)


# AgentState is imported from src.graph.state

def create_workflow() -> StateGraph:
    """创建智能体工作流"""
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("plan", plan_node)
    workflow.add_node("route", route_node)
    workflow.add_node("execute", execute_node)
    workflow.add_node("check", check_node)

    # 设置入口点
    workflow.set_entry_point("plan")

    # 添加边
    workflow.add_edge("plan", "route")
    workflow.add_edge("route", "execute")
    workflow.add_edge("execute", "check")

    # 条件边 - 根据检查结果决定是否继续
    workflow.add_conditional_edges(
        "check",
        lambda state: "end" if state.get("is_complete", False) else "continue",
        {
            "end": END,
            "continue": "route"  # 回到路由节点继续执行下一个任务
        }
    )

    logger.info("Workflow created successfully")
    return workflow


# 全局工作流实例
workflow = create_workflow().compile()
