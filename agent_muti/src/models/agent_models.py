# multi_agent_system/models/agent_models.py
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Any, Optional
import json
from datetime import datetime


class AgentType(Enum):
    """Agent 类型枚举"""
    COORDINATOR = "coordinator"
    WEATHER = "weather"
    TRANSPORT = "transport"
    BUDGET = "budget"
    HOTEL = "hotel"
    ATTRACTION = "attraction"
    CUSTOM = "custom"


@dataclass
class AgentResponse:
    """Agent 响应数据结构"""
    agent_type: AgentType
    content: str
    data: Dict[str, Any]
    confidence: float
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "agent_type": self.agent_type.value,
            "content": self.content,
            "data": self.data,
            "confidence": self.confidence,
            "metadata": self.metadata or {}
        }

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)


@dataclass
class AgentCapability:
    """Agent 能力描述"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class IterationStep:
    """迭代步骤记录"""
    state: str  # think, plan, action, next
    data: Dict[str, Any]
    timestamp: float
    agent_responses: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "state": self.state,
            "data": self.data,
            "timestamp": self.timestamp,
            "agent_responses": self.agent_responses
        }