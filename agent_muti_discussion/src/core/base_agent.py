from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import uuid


@dataclass
class AgentResponse:
    content: str
    metadata: Dict[str, Any]
    requires_reflection: bool = False


class BaseAgent(ABC):
    def __init__(self, name: str, role: str, capabilities: List[str] = None):
        self.agent_id = str(uuid.uuid4())
        self.name = name
        self.role = role
        self.capabilities = capabilities or []
        self.plugins = {}

    def add_plugin(self, plugin_name: str, plugin_instance):
        """添加功能插件"""
        self.plugins[plugin_name] = plugin_instance

    def remove_plugin(self, plugin_name: str):
        """移除功能插件"""
        self.plugins.pop(plugin_name, None)

    def use_plugin(self, plugin_name: str, *args, **kwargs):
        """使用插件"""
        if plugin_name in self.plugins:
            return self.plugins[plugin_name].execute(*args, **kwargs)
        return None

    @abstractmethod
    async def process(self, input_text: str, context: Dict[str, Any] = None) -> AgentResponse:
        """处理输入并返回响应"""
        pass

    def should_reflect(self, response: AgentResponse, discussion_history: List[Dict]) -> bool:
        """判断是否需要反思"""
        return response.requires_reflection