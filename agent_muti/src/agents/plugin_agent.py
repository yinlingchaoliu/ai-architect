# multi_agent_system/agents/plugin_agent.py
import inspect
from typing import Dict, List, Any, Callable
from .base_agent import BaseAgent
from ..models.agent_models import AgentType, AgentResponse, AgentCapability


class PluginAgent(BaseAgent):
    """插件化 Agent 基类"""

    def __init__(self, agent_type: AgentType, name: str, description: str):
        super().__init__(agent_type, name, description)
        self.plugins: Dict[str, Callable] = {}

    def register_plugin(self, name: str, function: Callable, capability: AgentCapability):
        """注册插件函数"""
        self.plugins[name] = function
        self.register_capability(capability)

    async def execute_plugin(self, plugin_name: str, **kwargs) -> Any:
        """执行插件函数"""
        if plugin_name not in self.plugins:
            raise ValueError(f"插件 '{plugin_name}' 不存在")

        plugin_func = self.plugins[plugin_name]

        # 检查是否是异步函数
        if inspect.iscoroutinefunction(plugin_func):
            return await plugin_func(**kwargs)
        else:
            return plugin_func(**kwargs)

    def list_plugins(self) -> List[str]:
        """列出所有插件"""
        return list(self.plugins.keys())