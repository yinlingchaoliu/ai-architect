from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage

from openai import OpenAI

from ..utils.config import config
from ..utils.logger import logger


@dataclass
class AgentResponse:
    """智能体响应数据类"""
    content: str
    metadata: Dict[str, Any] = None
    requires_reflection: bool = False


class BaseAgent(ABC):
    """智能体基类"""

    def __init__(self, name: str, system_prompt: str, model_name: str = "gpt-3.5-turbo", temperature: float = 0.9):
        self.name = name
        self.system_prompt = system_prompt
        self.model_name = model_name or config.model_name
        self.temperature = temperature or config.temperature

        # 初始化大模型
        self.llm = OpenAI()

        # 消息历史
        self.message_history: List[BaseMessage] = []

        # 初始化系统提示
        self._initialize_system_prompt()

    def _initialize_system_prompt(self):
        """初始化系统提示"""
        if self.system_prompt:
            self.message_history.append(SystemMessage(content=self.system_prompt))

    def add_message(self, message: BaseMessage):
        """添加消息到历史"""
        self.message_history.append(message)

    def clear_history(self):
        """清空消息历史（保留系统提示）"""
        system_msg = None
        if self.message_history and isinstance(self.message_history[0], SystemMessage):
            system_msg = self.message_history[0]

        self.message_history = []
        if system_msg:
            self.message_history.append(system_msg)

    @abstractmethod
    def process(self, input_data: str, **kwargs) -> Dict[str, Any]:
        """处理输入数据，返回结果字典"""
        pass

    def generate_response(self, prompt: str, **kwargs) -> str:
        """生成响应"""
        try:
            # 添加用户消息
            self.add_message(HumanMessage(content=prompt))

            # 将LangChain消息转换为OpenAI消息格式
            messages = []
            for msg in self.message_history:
                if isinstance(msg, SystemMessage):
                    messages.append({"role": "system", "content": msg.content})
                elif isinstance(msg, HumanMessage):
                    messages.append({"role": "user", "content": msg.content})
                else:
                    # 假设其他消息都是助手消息
                    messages.append({"role": "assistant", "content": msg.content})

            # 调用OpenAI API
            response = self.llm.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=kwargs.get('max_tokens', config.max_tokens)
            )
            response_content = response.choices[0].message.content

            # 添加助手消息
            from langchain_core.messages import AIMessage
            self.add_message(AIMessage(content=response_content))

            logger.info(f"Agent {self.name} 生成响应: {response_content}")
            return response_content
        except Exception as e:
            logger.error(f"Agent {self.name} 生成响应异常: {str(e)}")
            return f"错误: {str(e)}"

    def get_history(self) -> List[Dict[str, str]]:
        """获取消息历史（用于显示）"""
        history = []
        for msg in self.message_history:
            if isinstance(msg, SystemMessage):
                role = "system"
            elif isinstance(msg, HumanMessage):
                role = "user"
            else:
                role = "assistant"
            history.append({"role": role, "content": msg.content})
        return history