# agentdemo/src/models/agent_models.py
import time
import json
from enum import Enum
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
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


class AgentStatus(Enum):
    """Agent 状态枚举"""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    TIMEOUT = "timeout"
    RETRYING = "retrying"


class IterationPhase(Enum):
    """迭代阶段枚举"""
    THINK = "think"
    PLAN = "plan"
    ACTION = "action"
    NEXT = "next"


@dataclass
class AgentCapability:
    """Agent 能力描述"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    timeout: int = 30
    max_retries: int = 3
    requires_auth: bool = False


@dataclass
class AgentResponse:
    """Agent 响应"""
    agent_type: AgentType
    content: str
    data: Dict[str, Any]
    confidence: float
    execution_time: float = 0.0
    retry_count: int = 0
    timeout_occurred: bool = False
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "agent_type": self.agent_type.value,
            "content": self.content,
            "data": self.data,
            "confidence": self.confidence,
            "execution_time": self.execution_time,
            "retry_count": self.retry_count,
            "timeout_occurred": self.timeout_occurred,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "timestamp": datetime.now().isoformat()
        }


@dataclass
class IterationStep:
    """迭代步骤记录"""
    state: str
    data: Dict[str, Any]
    timestamp: float
    agent_responses: Optional[Dict[str, AgentResponse]] = None
    execution_time: float = 0.0
    timeout_warning: bool = False
    phase: Optional[IterationPhase] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "state": self.state,
            "data": self.data,
            "timestamp": self.timestamp,
            "execution_time": self.execution_time,
            "timeout_warning": self.timeout_warning,
            "phase": self.phase.value if self.phase else None
        }
        
        if self.agent_responses:
            result["agent_responses"] = {
                name: response.to_dict() 
                for name, response in self.agent_responses.items()
            }
        
        return result


@dataclass
class TimeoutConfig:
    """超时配置"""
    think_timeout: int = 30
    plan_timeout: int = 30
    action_timeout: int = 60
    next_timeout: int = 15
    agent_timeout: int = 30
    coordinator_timeout: int = 50
    max_timeout: int = 120
    warning_threshold: float = 0.8  # 超时预警阈值


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    retry_delay: float = 1.0
    exponential_backoff: bool = True
    max_retry_delay: float = 10.0
    retry_on_timeout: bool = True


@dataclass
class LogEntry:
    """日志条目"""
    timestamp: datetime
    level: str
    module: str
    message: str
    agent_name: Optional[str] = None
    phase: Optional[IterationPhase] = None
    execution_time: Optional[float] = None
    timeout_occurred: bool = False
    retry_count: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "module": self.module,
            "message": self.message,
            "agent_name": self.agent_name,
            "phase": self.phase.value if self.phase else None,
            "execution_time": self.execution_time,
            "timeout_occurred": self.timeout_occurred,
            "retry_count": self.retry_count,
            "metadata": self.metadata
        }


@dataclass
class PerformanceMetrics:
    """性能指标"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    timeout_requests: int = 0
    average_response_time: float = 0.0
    max_response_time: float = 0.0
    min_response_time: float = 0.0
    total_retries: int = 0
    phase_metrics: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def update_phase_metric(self, phase: str, execution_time: float, success: bool = True):
        """更新阶段指标"""
        if phase not in self.phase_metrics:
            self.phase_metrics[phase] = {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "total_time": 0.0,
                "average_time": 0.0,
                "max_time": 0.0,
                "min_time": float('inf')
            }
        
        metric = self.phase_metrics[phase]
        metric["total_executions"] += 1
        metric["total_time"] += execution_time
        
        if success:
            metric["successful_executions"] += 1
        else:
            metric["failed_executions"] += 1
        
        metric["average_time"] = metric["total_time"] / metric["total_executions"]
        metric["max_time"] = max(metric["max_time"], execution_time)
        metric["min_time"] = min(metric["min_time"], execution_time)


@dataclass
class SystemStatus:
    """系统状态"""
    overall_status: str = "unknown"
    active_agents: int = 0
    total_agents: int = 0
    current_iteration: int = 0
    max_iterations: int = 5
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    recent_timeouts: int = 0
    recent_errors: int = 0
    uptime: float = 0.0
    last_health_check: Optional[datetime] = None
    agent_statuses: Dict[str, str] = field(default_factory=dict)
