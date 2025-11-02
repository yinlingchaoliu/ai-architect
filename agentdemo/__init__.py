# agentdemo/__init__.py
"""
多 Agent 智能系统 - 增强版
专注于超时处理和日志记录的健壮系统

版本: 1.0.0
作者: AI Architect
"""

__version__ = "1.0.0"
__author__ = "AI Architect"
__description__ = "专注于超时处理和日志记录的多 Agent 智能系统"

from .src.core.agent_system import EnhancedDynamicAgentSystem
from .src.utils.logger_manager import logger_manager

# 导出主要类
__all__ = [
    "EnhancedDynamicAgentSystem",
    "logger_manager"
]
