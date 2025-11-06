# src/agents/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class AgentState(BaseModel):
    """智能体状态"""
    status: str = "idle"  # idle, thinking, acting, completed
    messages: List[Dict] = Field(default_factory=list)
    current_tool: Optional[str] = None
    tool_result: Optional[Any] = None
    max_steps: int = 10
    current_step: int = 0

class BaseAgent(ABC):
    """基础智能体抽象类"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.state = AgentState()
        self.llm_manager = None
        
    @abstractmethod
    async def initialize(self):
        """初始化智能体"""
        pass
        
    @abstractmethod  
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """运行智能体"""
        pass
        
    @abstractmethod
    async def step(self) -> str:
        """单步执行"""
        pass
        
    def get_state(self) -> AgentState:
        return self.state
        
    def reset(self):
        """重置状态"""
        self.state = AgentState()