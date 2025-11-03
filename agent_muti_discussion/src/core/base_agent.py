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
    
    async def _call_llm(self, prompt: str, **kwargs) -> str:
        """调用大语言模型 - 提供简单的模拟实现"""
        # 这是一个模拟实现，在实际应用中应该替换为真实的LLM API调用
        # 根据不同类型的代理返回不同的模拟响应
        if self.role == "分析器":
            return f"分析结果: 问题 '{prompt}' 需要进一步探讨和专家意见。"
        elif self.role == "主持人":
            return f"主持响应: 感谢您的输入，我会协调专家们讨论 '{prompt}' 这个问题。"
        elif "专家" in self.role:
            return f"{self.role}意见: 关于 '{prompt}'，我认为这需要从多个角度考虑，包括技术可行性、商业价值和实施策略。"
        else:
            return f"模拟响应: 这是对 '{prompt}' 的响应，由 {self.role} 提供。"