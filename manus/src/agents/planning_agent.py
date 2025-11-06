# src/agents/planning_agent.py
from typing import Dict, Any, List
import json
from .base import BaseAgent

import re

class PlanningAgent(BaseAgent):
    """规划智能体 - 负责任务拆解和路由"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.available_agents = config.get("available_agents", [])
        self.planning_prompt = config.get("planning_prompt", "")
    
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
        
        # 解析响应为结构化计划
        return self._parse_plan_response(response)
    
    def _build_planning_prompt(self, task: str, context: Dict[str, Any]) -> str:
        """构建规划提示"""
        base_prompt = self.planning_prompt
        
        # 添加可用智能体信息
        agents_info = "Available specialized agents:\n"
        for agent_info in self.available_agents:
            agents_info += f"- {agent_info['name']}: {agent_info['description']}\n"
            if 'capabilities' in agent_info:
                agents_info += f"  Capabilities: {', '.join(agent_info['capabilities'])}\n"
        
        context_info = f"User context: {json.dumps(context, indent=2)}" if context else ""
        
        return f"""{base_prompt}

Task to plan: {task}

{agents_info}

{context_info}

Please analyze this task and create a detailed execution plan with the following structure:
1. Break down the main task into clear, actionable subtasks
2. For each subtask, recommend the most suitable agent
3. Identify any dependencies between subtasks
4. Estimate the complexity of each subtask

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
    "estimated_steps": "estimated number of steps needed"
}}"""
    
    def _parse_plan_response(self, response: str) -> Dict[str, Any]:
        """解析规划响应"""
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