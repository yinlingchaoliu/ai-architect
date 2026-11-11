"""core模块初始化 - 包含系统核心组件"""

# 基础组件
from .base_agent import BaseAgent, AgentResponse

# SessionManager imports concrete agents, which also import this package.
# Load it on demand so either import order works.
def __getattr__(name):
    if name == "SessionManager":
        from .session_manager import SessionManager
        return SessionManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

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
