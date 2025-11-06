# src/tools/tool_registry.py
from typing import Dict, List, Any, Optional
from .base import BaseTool

class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
    
    def register_tool(self, tool: BaseTool) -> None:
        """注册工具"""
        self._tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self._tools.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有工具"""
        return [tool.get_schema() for tool in self._tools.values()]
    
    async def execute_tool(self, name: str, **kwargs) -> Any:
        """执行工具"""
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")
        return await tool.execute(**kwargs)
    
    def get_tools_schemas(self) -> List[Dict[str, Any]]:
        """获取所有工具的模式"""
        return [tool.get_schema() for tool in self._tools.values()]

# 全局工具注册表实例
tool_registry = ToolRegistry()