# src/agents/planning_agent.py
from typing import Dict, Any, List, Set
import json
from .base import BaseAgent
from src.tools.tool_registry import tool_registry
import re

class PlanningAgent(BaseAgent):
    """规划智能体 - 负责任务拆解和路由"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.available_agents = config.get("available_agents", [])
        self.planning_prompt = config.get("planning_prompt", "")
        self.agent_pool = None  # 将在初始化后设置
    
    async def initialize(self):
        """初始化规划智能体"""
        # 设置初始状态
        self.state.status = "initialized"
        # 确保llm_manager被正确设置
        if not self.llm_manager:
            raise ValueError("LLM manager not set for planning agent")
        
        # 从llm_manager尝试获取agent_pool引用
        # 注意：这需要在agent_pool设置llm_manager后进行
        if hasattr(self, '_agent_pool'):
            self.agent_pool = self._agent_pool
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """运行规划过程"""
        task = input_data.get("task", "")
        user_context = input_data.get("context", {})
        
        # 生成任务计划
        plan = await self._generate_plan(task, user_context)
        
        return {
            "original_task": task,
            "plan": plan,
            "subtasks": plan.get("subtasks", []),
            "recommended_agents": plan.get("recommended_agents", []),
            "dependencies": plan.get("dependencies", [])
        }
    
    async def _generate_plan(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """生成任务计划"""
        prompt = self._build_planning_prompt(task, context)
        
        response = await self.llm_manager.generate(
            messages=[{"role": "user", "content": prompt}],
            model=self.config.get("model", "default")
        )
        
        # 解析响应为结构化计划 - 从LLMResponse对象中提取content属性
        return self._parse_plan_response(response.content)
    
    def _get_available_agents_info(self) -> List[Dict[str, Any]]:
        """获取当前系统中实际可用的智能体信息"""
        # 优先从agent_pool获取实际注册的智能体
        if hasattr(self, 'agent_pool') and self.agent_pool and hasattr(self.agent_pool, 'list_agents'):
            return self.agent_pool.list_agents()
        
        # 如果没有agent_pool引用，回退到配置中的智能体
        if self.available_agents:
            return self.available_agents
        
        # 默认返回基础智能体信息
        return [
            {
                "name": "tool_call_agent",
                "description": "通用工具调用智能体，可以执行基本任务",
                "capabilities": ["execute_python", "file_operations", "web_search"]
            }
        ]
    
    def _get_available_tools_info(self) -> List[Dict[str, Any]]:
        """获取当前系统中实际可用的工具信息"""
        # 从工具注册表获取实际注册的工具
        return tool_registry.list_tools()
    
    def _build_planning_prompt(self, task: str, context: Dict[str, Any]) -> str:
        """构建规划提示"""
        base_prompt = self.planning_prompt
        
        # 获取可用智能体信息
        agents_info = self._get_available_agents_info()
        # 获取可用工具信息
        tools_info = self._get_available_tools_info()
        
        # 格式化智能体信息
        agents_text = "Available specialized agents:\n"
        for agent in agents_info:
            agents_text += f"- {agent['name']}: {agent.get('description', 'No description available')}\n"
            capabilities = agent.get('capabilities', [])
            if capabilities:
                agents_text += f"  Capabilities: {', '.join(capabilities)}\n"
        
        # 格式化工具信息
        tools_text = "Available tools:\n"
        for tool in tools_info:
            tools_text += f"- {tool.get('name', 'Unknown')}: {tool.get('description', 'No description available')}\n"
        
        # 构建提示词
        return f"""{base_prompt}

Task to plan: {task}

{agents_text}

{tools_text}

Please analyze this task and create a detailed execution plan with the following structure:
1. Break down the main task into clear, actionable subtasks
2. For each subtask, recommend the most suitable agent from the available agents list
3. Identify any dependencies between subtasks
4. Estimate the complexity of each subtask
5. If the task requires capabilities not available in the current agents/tools, identify what additional agents or tools would be needed

Return your response as a JSON object with this structure:
{{
    "subtasks": [
        {{
            "id": 1,
            "description": "clear description of the subtask",
            "expected_output": "what should be produced",
            "recommended_agent": "agent_name",
            "complexity": "low/medium/high",
            "dependencies": [list of subtask ids this depends on]
        }}
    ],
    "overall_complexity": "assessment of overall task complexity",
    "estimated_steps": "estimated number of steps needed",
    "missing_resources": {{
        "agents": ["list of additional agent names that would help"],
        "tools": ["list of additional tool names that would help"]
    }}
}}"""

    
    def _parse_plan_response(self, response: str) -> Dict[str, Any]:
        """解析规划响应字符串"""
        try:
            # 尝试从响应中提取JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # 如果无法解析JSON，创建基本结构
                return {
                    "subtasks": [
                        {
                            "id": 1,
                            "description": "Execute the complete task",
                            "expected_output": "Task completion result",
                            "recommended_agent": "tool_call_agent",
                            "complexity": "medium",
                            "dependencies": []
                        }
                    ],
                    "overall_complexity": "medium",
                    "estimated_steps": 1
                }
        except json.JSONDecodeError:
            # 如果JSON解析失败，返回默认计划
            return {
                "subtasks": [
                    {
                        "id": 1,
                        "description": response[:200],  # 使用响应前200字符作为描述
                        "expected_output": "Task completion",
                        "recommended_agent": "tool_call_agent", 
                        "complexity": "medium",
                        "dependencies": []
                    }
                ],
                "overall_complexity": "medium",
                "estimated_steps": 1
            }
    
    async def step(self) -> str:
        """规划智能体的单步执行"""
        # 规划智能体通常一次性完成规划
        return "planning_completed"