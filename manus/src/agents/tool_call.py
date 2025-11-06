# src/agents/tool_call.py
import json
import re
from typing import Dict, Any, List, Optional
from .react import ReActAgent
from src.tools.tool_registry import tool_registry

class ToolCallAgent(ReActAgent):
    """工具调用智能体"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.available_tools = config.get("tools", [])
        self.tool_registry = tool_registry
    
    async def think(self) -> str:
        """思考阶段 - 增强工具调用能力"""
        self.state.status = "thinking"
        
        # 构建包含工具信息的提示
        prompt = self._build_tool_aware_prompt()
        
        response = await self.llm_manager.generate(
            messages=[{"role": "user", "content": prompt}],
            tools=self._get_available_tools_schemas(),
            tool_choice="auto"
        )
        
        # 检查是否有工具调用
        if hasattr(response, 'tool_calls') and response.tool_calls:
            self.state.current_tool = response.tool_calls[0]['name']
            self.state.tool_arguments = response.tool_calls[0]['arguments']
        
        self.state.messages.append({
            "role": "assistant",
            "content": response.content if hasattr(response, 'content') else str(response),
            "tool_calls": getattr(response, 'tool_calls', None)
        })
        
        return response.content if hasattr(response, 'content') else str(response)
    
    async def act(self) -> Any:
        """行动阶段 - 执行工具调用"""
        self.state.status = "acting"
        
        if self.state.current_tool:
            # 执行工具调用
            tool_name = self.state.current_tool
            tool_args = self.state.tool_arguments
            
            try:
                if isinstance(tool_args, str):
                    tool_args = json.loads(tool_args)
                
                result = await self.tool_registry.execute_tool(tool_name, **tool_args)
                
                # 记录工具执行结果
                self.state.messages.append({
                    "role": "tool",
                    "content": str(result),
                    "tool_name": tool_name,
                    "tool_result": result
                })
                
                self.state.tool_result = result
                self.state.current_tool = None
                self.state.tool_arguments = None
                
                return result
                
            except Exception as e:
                error_result = {
                    "success": False,
                    "error": f"Tool execution failed: {str(e)}"
                }
                self.state.messages.append({
                    "role": "tool", 
                    "content": str(error_result),
                    "tool_name": tool_name,
                    "tool_result": error_result
                })
                return error_result
        else:
            # 没有工具调用，检查是否是最终答案
            last_message = self.state.messages[-1]
            if "final_answer" in last_message.get("content", "").lower():
                self.state.status = "completed"
                return {"action": "final_answer", "result": last_message["content"]}
        
        return None
    
    def _build_tool_aware_prompt(self) -> str:
        """构建包含工具信息的提示"""
        base_prompt = self.thinking_prompt
        
        # 添加可用工具信息
        tools_info = "Available tools:\n"
        for tool_schema in self._get_available_tools_schemas():
            func = tool_schema['function']
            tools_info += f"- {func['name']}: {func['description']}\n"
            if 'parameters' in func:
                tools_info += f"  Parameters: {func['parameters']}\n"
        
        return f"{base_prompt}\n\n{tools_info}"
    
    def _get_available_tools_schemas(self) -> List[Dict[str, Any]]:
        """获取可用工具的模式"""
        if not self.available_tools:
            return tool_registry.get_tools_schemas()
        
        schemas = []
        for tool_name in self.available_tools:
            tool = tool_registry.get_tool(tool_name)
            if tool:
                schemas.append(tool.get_schema())
        
        return schemas