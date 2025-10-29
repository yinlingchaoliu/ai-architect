# main.py
import asyncio
import sys
from typing import Dict, Any

from config.config import MCP_SERVERS
from core.mcp_client import MCPProtocolClient

class MCPManager:
    """基于MCP协议的智能应用 - 完全解耦架构"""

    def __init__(self):
        self.mcp_client = MCPProtocolClient()

    async def initialize(self):
        """通过MCP协议初始化所有服务器"""
        print("🚀 初始化MCP协议系统...")

        # 通过协议注册所有服务器
        for server_name, server_url in MCP_SERVERS.items():
            await self.mcp_client.register_server(server_name, server_url)

        # 显示通过协议发现的所有工具
        tools = self.mcp_client.get_all_tool_schemas()
        print(f"✅ 系统初始化完成! 通过MCP协议发现 {len(tools)} 个工具")

        for tool in tools:
            function_info = tool["function"]
            print(f"   📌 {function_info['name']}: {function_info['description']}")

    async def register_server(self,server_name, server_url):
        await self.mcp_client.register_server(server_name, server_url)

    def get_all_tool_schemas(self):
        return self.mcp_client.get_all_tool_schemas()

    async def call_tool(self, tool_key: str, arguments: Dict[str, Any]) -> str:
        return await self.mcp_client.call_tool(tool_key,arguments)

    async def cleanup(self):
        """清理协议连接"""
        await self.mcp_client.close_all()