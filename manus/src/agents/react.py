# src/agents/react.py
from .base import BaseAgent, AgentState
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class ReActAgent(BaseAgent):
    """ReAct模式智能体"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.thinking_prompt = config.get("thinking_prompt", "")
        self.max_react_cycles = config.get("max_react_cycles", 5)
        
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行ReAct循环"""
        self.state.messages.append({
            "role": "user", 
            "content": input_data.get("task", "")
        })
        
        for cycle in range(self.max_react_cycles):
            logger.info(f"ReAct cycle {cycle + 1}")
            
            # Think 阶段
            thought = await self.think()
            if not thought:
                break
                
            # Act 阶段  
            action_result = await self.act()
            if self.state.status == "completed":
                break
                
        return {
            "result": self.state.messages[-1] if self.state.messages else "",
            "steps": self.state.current_step,
            "status": self.state.status
        }
    
    async def think(self) -> str:
        """思考阶段"""
        self.state.status = "thinking"
        
        # 构建思考提示
        prompt = self._build_think_prompt()
        
        # 调用LLM进行思考
        response = await self.llm_manager.generate(
            messages=[{"role": "user", "content": prompt}],
            model=self.config.get("model", "default")
        )
        
        self.state.messages.append({
            "role": "assistant",
            "content": response,
            "type": "thought"
        })
        
        return response
    
    async def act(self) -> Any:
        """行动阶段"""
        self.state.status = "acting"
        
        # 解析思考结果，决定行动
        action_decision = await self._parse_action_decision()
        
        if action_decision.get("action") == "final_answer":
            self.state.status = "completed"
            return action_decision.get("result")
            
        elif action_decision.get("action") == "use_tool":
            tool_result = await self._execute_tool(action_decision)
            self.state.tool_result = tool_result
            return tool_result
            
        return None
    
    async def step(self) -> str:
        """单步执行 - 实现抽象方法"""
        if self.state.status == "completed":
            return "completed"
            
        if self.state.status == "thinking":
            return await self.act()
        else:
            return await self.think()