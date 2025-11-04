# agents/base_agent.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import logging


class AgentResponse(BaseModel):
    content: str
    reasoning: str
    tools_used: List[str] = []
    needs_reflection: bool = False


class BaseAgent(ABC):
    def __init__(self, name: str, role: str, system_prompt: str):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.tools = {}
        self.logger = logging.getLogger(f"agent.{name}")

    def register_tool(self, tool_name: str, tool_func):
        self.tools[tool_name] = tool_func

    @abstractmethod
    async def generate_response(self, context: Dict[str, Any]) -> AgentResponse:
        pass

    @abstractmethod
    async def reflect(self, discussion_history: List[Dict], moderator_guidance: str) -> AgentResponse:
        pass