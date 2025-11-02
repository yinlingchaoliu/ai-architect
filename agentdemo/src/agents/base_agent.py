# agentdemo/src/agents/base_agent.py
import asyncio
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from openai import OpenAI
from openai import APITimeoutError, APIError, RateLimitError

from ..models.agent_models import AgentType, AgentResponse, AgentCapability, AgentStatus
from ..utils.logger_manager import logger_manager


class BaseAgent(ABC):
    """增强的基础 Agent 类 - 专注于超时处理和日志记录"""

    def __init__(self, agent_type: AgentType, name: str, description: str):
        self.agent_type = agent_type
        self.name = name
        self.description = description
        self.capabilities: List[AgentCapability] = []
        self.llm_client: Optional[OpenAI] = None
        self._initialized = False
        self.status = AgentStatus.INITIALIZING
        
        # 增强的超时配置
        self.model = "gpt-3.5-turbo"
        self.timeout = 30  # 默认超时时间
        self.max_retries = 3  # 最大重试次数
        self.retry_delay = 1  # 重试延迟（秒）
        self.exponential_backoff = True  # 指数退避
        self.max_retry_delay = 10  # 最大重试延迟
        
        # 性能监控
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.timeout_requests = 0
        self.total_retries = 0

    def initialize(self, api_key: str, model: str = "gpt-3.5-turbo", timeout: int = 30):
        """初始化 Agent"""
        logger_manager.log_agent_operation(
            self.name, 
            f"初始化Agent - 模型: {model}, 超时: {timeout}s",
            level="INFO"
        )
        
        try:
            self.llm_client = OpenAI(api_key=api_key, timeout=timeout)
            self.model = model
            self.timeout = timeout
            self._initialized = True
            self.status = AgentStatus.READY
            
            logger_manager.log_agent_operation(
                self.name, 
                "Agent初始化成功",
                level="INFO"
            )
        except Exception as e:
            self.status = AgentStatus.ERROR
            logger_manager.log_agent_operation(
                self.name, 
                f"Agent初始化失败: {e}",
                level="ERROR"
            )
            raise

    @abstractmethod
    async def process_request(self, query: str, context: Dict[str, Any] = None) -> AgentResponse:
        """处理请求的抽象方法"""
        pass

    def register_capability(self, capability: AgentCapability):
        """注册 Agent 能力"""
        self.capabilities.append(capability)
        logger_manager.log_agent_operation(
            self.name,
            f"注册能力: {capability.name}",
            level="DEBUG"
        )

    def get_capabilities(self) -> List[AgentCapability]:
        """获取 Agent 能力列表"""
        return self.capabilities

    async def _call_llm(self, messages: List[Dict], **kwargs) -> str:
        """增强的 LLM 调用方法 - 包含动态超时调整和详细日志"""
        if not self._initialized:
            error_msg = "Agent 未初始化，请先调用 initialize() 方法"
            logger_manager.log_agent_operation(
                self.name,
                error_msg,
                level="ERROR"
            )
            raise RuntimeError(error_msg)

        # 记录请求开始
        start_time = time.time()
        self.total_requests += 1
        
        # 确保messages是可序列化的
        try:
            json.dumps(messages, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            error_msg = f"消息序列化错误: {e}"
            logger_manager.log_agent_operation(
                self.name,
                error_msg,
                level="ERROR"
            )
            # 返回一个默认响应而不是抛出异常
            return "{\"core_requirements\":[],\"acquired_info\":{},\"missing_info\":[],\"confidence_level\":0.5,\"should_complete\":false}"

        # 动态超时调整
        temperature = kwargs.get('temperature', 0.1)
        max_tokens = kwargs.get('max_tokens', 1000)
        base_timeout = kwargs.get('timeout', self.timeout)
        
        # 根据消息复杂度动态调整超时时间
        message_length = len(str(messages))
        adjusted_timeout = self._calculate_dynamic_timeout(base_timeout, message_length)
        
        logger_manager.log_agent_operation(
            self.name,
            f"LLM调用开始 - 消息长度: {message_length}, 超时: {adjusted_timeout}s",
            level="DEBUG"
        )

        last_exception = None
        retry_count = 0

        for attempt in range(self.max_retries):
            retry_count = attempt
            current_timeout = adjusted_timeout
            
            # 指数退避：每次重试增加超时时间
            if self.exponential_backoff and attempt > 0:
                current_timeout = min(current_timeout * (1.5 ** attempt), self.max_retry_delay)
            
            try:
                logger_manager.log_retry_attempt(
                    self.name,
                    "LLM调用",
                    attempt + 1,
                    self.max_retries,
                    reason=str(last_exception) if last_exception else "首次尝试"
                )

                # 配置请求参数
                llm_params = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "timeout": current_timeout
                }

                # 使用run_in_executor执行同步的LLM调用
                loop = asyncio.get_event_loop()
                
                def sync_llm_call():
                    try:
                        response = self.llm_client.chat.completions.create(**llm_params)
                        return response.choices[0].message.content
                    except Exception as e:
                        logger_manager.log_agent_operation(
                            self.name,
                            f"LLM调用失败: {str(e)}",
                            level="ERROR"
                        )
                        raise

                # 调用LLM并设置整体超时，增加缓冲时间
                response_content = await asyncio.wait_for(
                    loop.run_in_executor(None, sync_llm_call),
                    timeout=current_timeout + 10  # 增加缓冲时间
                )

                # 验证响应内容
                if not response_content or not isinstance(response_content, str):
                    raise ValueError(f"无效的LLM响应: {response_content}")

                # 记录成功请求
                execution_time = time.time() - start_time
                self.successful_requests += 1
                
                logger_manager.log_agent_operation(
                    self.name,
                    f"LLM调用成功 - 执行时间: {execution_time:.2f}s",
                    level="INFO",
                    execution_time=execution_time,
                    retry_count=retry_count
                )

                return response_content

            except asyncio.TimeoutError:
                last_exception = f"LLM 请求超时 (尝试 {attempt + 1}/{self.max_retries})"
                self.timeout_requests += 1
                
                logger_manager.log_timeout_event(
                    self.name,
                    "LLM调用",
                    current_timeout,
                    retry_count=attempt + 1
                )
                
                # 超时情况下，使用指数退避
                if self.exponential_backoff:
                    current_timeout = min(current_timeout * 1.5, self.max_retry_delay)

            except APITimeoutError:
                last_exception = f"API 超时 (尝试 {attempt + 1}/{self.max_retries})"
                self.timeout_requests += 1
                
                logger_manager.log_timeout_event(
                    self.name,
                    "LLM调用",
                    current_timeout,
                    retry_count=attempt + 1
                )

            except RateLimitError:
                last_exception = f"速率限制 (尝试 {attempt + 1}/{self.max_retries})"
                
                logger_manager.log_agent_operation(
                    self.name,
                    f"速率限制 - 等待后重试",
                    level="WARNING"
                )
                
                # 速率限制时增加等待时间
                wait_time = self.retry_delay * (attempt + 1) * 2
                logger_manager.log_agent_operation(
                    self.name,
                    f"等待 {wait_time} 秒后重试...",
                    level="INFO"
                )
                await asyncio.sleep(wait_time)
                continue

            except APIError as e:
                last_exception = f"API 错误: {e} (尝试 {attempt + 1}/{self.max_retries})"
                self.failed_requests += 1
                
                logger_manager.log_agent_operation(
                    self.name,
                    f"API错误: {e}",
                    level="ERROR"
                )

            except Exception as e:
                last_exception = f"未知错误: {e} (尝试 {attempt + 1}/{self.max_retries})"
                self.failed_requests += 1
                
                logger_manager.log_agent_operation(
                    self.name,
                    f"未知错误: {e}",
                    level="ERROR"
                )

            # 如果不是最后一次尝试，等待后重试
            if attempt < self.max_retries - 1:
                wait_time = self.retry_delay * (attempt + 1)
                logger_manager.log_agent_operation(
                    self.name,
                    f"等待 {wait_time} 秒后重试...",
                    level="INFO"
                )
                await asyncio.sleep(wait_time)

        # 所有重试都失败，但不抛出异常而是返回一个默认的JSON响应
        execution_time = time.time() - start_time
        self.total_retries += retry_count
        self.failed_requests += 1
        
        logger_manager.log_agent_operation(
            self.name,
            f"LLM调用最终失败: {last_exception}",
            level="ERROR",
            execution_time=execution_time,
            timeout_occurred=True,
            retry_count=retry_count
        )
        
        # 返回一个默认的JSON响应，确保可以被解析
        return "{\"core_requirements\":[],\"acquired_info\":{},\"missing_info\":[],\"confidence_level\":0.5,\"should_complete\":false}"

    def _calculate_dynamic_timeout(self, base_timeout: int, message_length: int) -> int:
        """计算动态超时时间"""
        # 基础超时
        timeout = base_timeout
        
        # 根据消息长度调整
        if message_length > 2000:  # 复杂提示
            timeout = min(timeout * 2, 90)  # 最多90秒
        elif message_length > 1000:  # 中等复杂度
            timeout = min(timeout * 1.5, 60)  # 最多60秒
        
        return timeout

    def get_agent_info(self) -> Dict[str, Any]:
        """获取 Agent 信息"""
        return {
            "name": self.name,
            "type": self.agent_type.value,
            "description": self.description,
            "status": self.status.value,
            "capabilities": [cap.to_dict() for cap in self.capabilities],
            "initialized": self._initialized,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "performance": {
                "total_requests": self.total_requests,
                "successful_requests": self.successful_requests,
                "failed_requests": self.failed_requests,
                "timeout_requests": self.timeout_requests,
                "total_retries": self.total_retries
            }
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        success_rate = (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0
        timeout_rate = (self.timeout_requests / self.total_requests * 100) if self.total_requests > 0 else 0
        
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "timeout_requests": self.timeout_requests,
            "total_retries": self.total_retries,
            "success_rate": round(success_rate, 2),
            "timeout_rate": round(timeout_rate, 2),
            "status": self.status.value
        }
