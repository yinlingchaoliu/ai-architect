# multi_agent_system/agents/base_agent.py
import asyncio
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from openai import OpenAI
from openai import APITimeoutError, APIError, RateLimitError

from ..models.agent_models import AgentType, AgentResponse, AgentCapability


class BaseAgent(ABC):
    """抽象基础 Agent 类"""

    def __init__(self, agent_type: AgentType, name: str, description: str):
        self.agent_type = agent_type
        self.name = name
        self.description = description
        self.capabilities: List[AgentCapability] = []
        self.llm_client: Optional[OpenAI] = None
        self._initialized = False
        self.model = "gpt-3.5-turbo"
        self.timeout = 30  # 默认超时时间
        self.max_retries = 3  # 最大重试次数
        self.retry_delay = 1  # 重试延迟（秒）

    def initialize(self, api_key: str, model: str = "gpt-3.5-turbo", timeout: int = 30):
        """初始化 Agent"""
        self.llm_client = OpenAI(api_key=api_key, timeout=timeout)
        self.model = model
        self.timeout = timeout
        self._initialized = True

    @abstractmethod
    async def process_request(self, query: str, context: Dict[str, Any] = None) -> AgentResponse:
        """处理请求的抽象方法"""
        pass

    def register_capability(self, capability: AgentCapability):
        """注册 Agent 能力"""
        self.capabilities.append(capability)

    def get_capabilities(self) -> List[AgentCapability]:
        """获取 Agent 能力列表"""
        return self.capabilities

    async def _call_llm(self, messages: List[Dict], **kwargs) -> str:
        """调用 LLM 的通用方法，包含重试机制"""
        if not self._initialized:
            raise RuntimeError("Agent 未初始化，请先调用 initialize() 方法")

        temperature = kwargs.get('temperature', 0.1)
        max_tokens = kwargs.get('max_tokens', 1000)
        timeout = kwargs.get('timeout', self.timeout)

        last_exception = None

        for attempt in range(self.max_retries):
            try:
                print(f"🔄 [{self.name}] LLM 调用尝试 {attempt + 1}/{self.max_retries}")

                # 使用 asyncio 来包装同步调用，并设置超时
                response = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self.llm_client.chat.completions.create(
                            model=self.model,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens
                        )
                    ),
                    timeout=timeout
                )
                print(response)
                return response.choices[0].message.content

            except asyncio.TimeoutError:
                last_exception = f"LLM 请求超时 (尝试 {attempt + 1}/{self.max_retries})"
                print(f"⏰ {last_exception}")

            except APITimeoutError:
                last_exception = f"API 超时 (尝试 {attempt + 1}/{self.max_retries})"
                print(f"⏰ {last_exception}")

            except RateLimitError:
                last_exception = f"速率限制 (尝试 {attempt + 1}/{self.max_retries})"
                print(f"🚫 {last_exception}")
                # 速率限制时增加等待时间
                await asyncio.sleep(self.retry_delay * (attempt + 1) * 2)
                continue

            except APIError as e:
                last_exception = f"API 错误: {e} (尝试 {attempt + 1}/{self.max_retries})"
                print(f"❌ {last_exception}")

            except Exception as e:
                last_exception = f"未知错误: {e} (尝试 {attempt + 1}/{self.max_retries})"
                print(f"❌ {last_exception}")

            # 如果不是最后一次尝试，等待后重试
            if attempt < self.max_retries - 1:
                wait_time = self.retry_delay * (attempt + 1)
                print(f"⏳ 等待 {wait_time} 秒后重试...")
                await asyncio.sleep(wait_time)

        # 所有重试都失败
        error_msg = f"LLM 调用失败: {last_exception}"
        print(f"💥 {error_msg}")
        raise Exception(error_msg)

    def get_agent_info(self) -> Dict[str, Any]:
        """获取 Agent 信息"""
        return {
            "name": self.name,
            "type": self.agent_type.value,
            "description": self.description,
            "capabilities": [cap.to_dict() for cap in self.capabilities],
            "initialized": self._initialized,
            "timeout": self.timeout,
            "max_retries": self.max_retries
        }