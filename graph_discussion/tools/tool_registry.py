# 基础工具类
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from .base_tool import BaseTool
from ..utils.logger import get_logger

class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self._tools = {}

    def register(self, tool: BaseTool):
        """注册工具"""
        self._tools[tool.name] = tool
        tool.logger.info(f"工具 {tool.name} 已注册", "green")

    def unregister(self, tool_name: str):
        """注销工具"""
        if tool_name in self._tools:
            del self._tools[tool_name]
            get_logger("ToolRegistry").info(f"工具 {tool_name} 已注销", "yellow")

    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self._tools.get(tool_name)

    def list_tools(self) -> Dict[str, str]:
        """列出所有工具"""
        return {name: tool.description for name, tool in self._tools.items()}

    def execute_tool(self, tool_name: str, query: str, **kwargs) -> Any:
        """执行指定工具"""
        tool = self.get_tool(tool_name)
        if tool:
            return tool(query, **kwargs)
        else:
            get_logger("ToolRegistry").error(f"工具 {tool_name} 未找到", "red")
            return f"工具 {tool_name} 未注册"


# 创建全局工具注册表实例
tool_registry = ToolRegistry()