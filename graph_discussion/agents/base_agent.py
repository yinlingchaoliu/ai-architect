# 基础智能体类
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from ..config import config
from ..tools.tool_registry import tool_registry
from ..utils.logger import get_logger

class BaseAgent(ABC):
    """基础智能体类"""
    
    def __init__(self, name: str, role: str, color: str = "white"):
        self.name = name
        self.role = role
        self.color = color
        self.logger = get_logger(name)
        self.llm = ChatOpenAI(
            model=config.model_name,
            openai_api_key=config.openai_api_key,
            temperature=0.7
        )
        self.registered_tools = []  # 注册的工具名称列表

    # @abstractmethod
    # def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
    #     """处理状态并返回更新"""
    #     pass
    
    def log(self, message: str):
        """记录日志"""
        self.logger.info(f"[{self.role}] \n {message}", self.color)
    
    def call_llm(self, prompt: str) -> str:
        """调用大模型"""
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            self.log(f"调用大模型失败: {str(e)}")
            return f"思考中... ({str(e)})"

    def register_tool(self, tool_name: str):
        """注册工具名称"""
        self.registered_tools.append(tool_name)
        self.logger.info(f"注册工具: {tool_name}", self.color)

    def use_tool(self, tool_name: str, query: str, **kwargs) -> str:
        """使用注册的工具"""
        if tool_name in self.registered_tools:
            return tool_registry.execute_tool(tool_name, query, **kwargs)
        else:
            self.logger.warning(f"工具 {tool_name} 未注册到该智能体", self.color)
            return f"无法使用工具 {tool_name}"

    def get_available_tools_info(self) -> str:
        """获取可用工具信息"""
        if not self.registered_tools:
            return "当前无可用工具"

        info = "可用工具:\n"
        for tool_name in self.registered_tools:
            tool = tool_registry.get_tool(tool_name)
            if tool:
                info += f"- {tool.name}: {tool.description}\n"
        return info