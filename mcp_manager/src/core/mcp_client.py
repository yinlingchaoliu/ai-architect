# mcp_client.py
import asyncio
import json
from typing import Dict, List, Any, Optional
from fastmcp import Client


class MCPProtocolClient:
    """纯协议驱动的MCP客户端，完全通过协议与服务器交互"""

    def __init__(self):
        self.servers: Dict[str, Dict] = {}
        self.available_tools: Dict[str, Any] = {}

    async def register_server(self, server_name: str, server_url: str):
        """通过MCP协议注册服务器"""
        try:
            print(server_url)
            # 创建客户端连接
            client = Client(server_url)
            await client.__aenter__()

            # 通过MCP协议获取工具列表
            tools = await client.list_tools()

            server_info = {
                "client": client,
                "url": server_url,
                "tools": {}
            }

            # 通过协议获取工具定义
            for tool in tools:
                tool_key = f"{server_name}_{tool.name}"

                # 构建标准化的工具描述（用于LLM注册）
                tool_schema = {
                    "type": "function",
                    "function": {
                        "name": tool_key,
                        "description": tool.description,
                        "parameters": self._parse_parameters_schema(tool.inputSchema)
                    }
                }

                server_info["tools"][tool_key] = {
                    "tool_def": tool,
                    "schema": tool_schema
                }

                self.available_tools[tool_key] = {
                    "server_name": server_name,
                    "tool_name": tool.name,
                    "client": client,
                    "schema": tool_schema
                }

            self.servers[server_name] = server_info
            print(f"✅ 注册服务器: {server_name} ({len(tools)} 个工具)")

        except Exception as e:
            print(f"❌ 注册服务器 {server_name} 失败: {e}")

    def _parse_parameters_schema(self, input_schema: Dict) -> Dict:
        """解析MCP协议中的参数模式"""
        if not input_schema:
            return {"type": "object", "properties": {}}

        return {
            "type": "object",
            "properties": input_schema.get("properties", {}),
            "required": input_schema.get("required", []),
            "additionalProperties": False
        }

    def get_all_tool_schemas(self) -> List[Dict]:
        """获取所有工具的LLM注册模式"""
        return [
            tool_info["schema"]
            for tool_info in self.available_tools.values()
        ]

    async def call_tool(self, tool_key: str, arguments: Dict[str, Any]) -> str:
        """通过MCP协议调用工具"""
        if tool_key not in self.available_tools:
            return f"错误: 工具 '{tool_key}' 未找到"

        try:
            tool_info = self.available_tools[tool_key]
            client = tool_info["client"]
            actual_tool_name = tool_info["tool_name"]

            # 通过MCP协议执行工具调用
            result = await client.call_tool(actual_tool_name, arguments)

            # 解析协议返回的结果
            if hasattr(result, 'content') and result.content:
                content = result.content[0]
                if hasattr(content, 'text'):
                    return content.text
            return str(result)

        except Exception as e:
            return f"协议调用错误: {str(e)}"

    async def close_all(self):
        """关闭所有协议连接"""
        for server_info in self.servers.values():
            await server_info["client"].__aexit__(None, None, None)