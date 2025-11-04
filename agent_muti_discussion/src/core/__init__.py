"""core模块初始化 - 包含系统核心组件"""

# 基础组件
from .base_agent import BaseAgent, AgentResponse

# 会话管理
from .session_manager import SessionManager

# 插件管理
from .plugin_manager import PluginManager

# 共识检查
from .consensus_checker import ConsensusChecker

__all__ = [
    # 基础组件
    "BaseAgent",
    "AgentResponse",
    "SessionManager",
    
    # 插件管理
    "PluginManager",
    
    # 共识检查
    "ConsensusChecker"
]