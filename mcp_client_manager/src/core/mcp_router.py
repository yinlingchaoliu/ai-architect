# llm_integration.py
import json
import os
from typing import Dict, Any, List
from openai import OpenAI


class LLMProtocolRouter:
    """LLM协议路由器 - 通过LLM决策调用哪个MCP协议工具"""

    def __init__(self, mcp_client, api_key: str = None):
        self.mcp_client = mcp_client
        self.llm_client = OpenAI(api_key=api_key)
        self.model = "gpt-3.5-turbo"

    async def process_user_request(self, user_input: str) -> str:
        """处理用户请求 - 通过LLM决策使用哪个MCP工具"""
        if not self.llm_client:
            return await self._fallback_process(user_input)

        try:
            # 获取所有通过MCP协议注册的工具
            tools = self.mcp_client.get_all_tool_schemas()

            if not tools:
                return "错误: 没有可用的MCP工具"

            print(tools)
            # 使用LLM进行工具调用决策
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "system",
                    "content": "你是一个智能助手，可以调用各种工具。请分析用户请求并选择合适的工具。"
                }, {
                    "role": "user",
                    "content": user_input
                }],
                tools=tools,
                tool_choice="auto"
            )

            message = response.choices[0].message

            if message.tool_calls:
                results = []
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    # 通过MCP协议执行调用
                    result = await self.mcp_client.call_tool(function_name, function_args)
                    results.append({
                        "tool": function_name,
                        "result": result
                    })

                return self._format_results(results)
            else:
                return message.content or "LLM决定直接回应"

        except Exception as e:
            print(f"LLM决策失败: {e}")
            return await self._fallback_process(user_input)

    async def _fallback_process(self, user_input: str) -> str:
        """回退处理 - 基于工具描述的简单匹配"""
        tools = self.mcp_client.get_all_tool_schemas()
        user_input_lower = user_input.lower()

        # 简单的关键词匹配
        for tool in tools:
            function_info = tool["function"]
            tool_name = function_info["name"]
            description = function_info["description"].lower()

        return self._generate_help_response(tools)

    def _format_results(self, results: List[Dict]) -> str:
        """格式化多个工具调用结果"""
        formatted = []
        for result in results:
            formatted.append(f"🔧 {result['tool']}:\n{result['result']}")
        return "\n\n".join(formatted)

    def _generate_help_response(self, tools: List[Dict]) -> str:
        """生成帮助响应"""
        help_lines = ["🤖 可用的MCP工具:"]

        for tool in tools:
            function_info = tool["function"]
            help_lines.append(f"• {function_info['name']}: {function_info['description']}")

            # 显示参数信息
            params = function_info.get("parameters", {}).get("properties", {})
            for param_name, param_info in params.items():
                param_desc = param_info.get("description", "")
                help_lines.append(f"  └─ {param_name}: {param_desc}")

        return "\n".join(help_lines)