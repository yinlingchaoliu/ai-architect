# 基础智能体类
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from ..config import config
from ..utils.logger import get_logger

class BaseAgent(ABC):
    """基础智能体类"""
    
    def __init__(self, name: str, role: str, color: str = "white"):
        self.name = name
        self.role = role
        self.color = color
        self.logger = get_logger(name)
        self.llm = ChatOpenAI(
            model=config.model_name,
            openai_api_key=config.openai_api_key,
            temperature=0.7
        )
        self.tools = []
    
    def add_tool(self, tool):
        """添加工具"""
        self.tools.append(tool)
    
    @abstractmethod
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """处理状态并返回更新"""
        pass
    
    def log(self, message: str):
        """记录日志"""
        self.logger.info(f"[{self.role}] {message}", self.color)
    
    def call_llm(self, prompt: str) -> str:
        """调用大模型"""
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            self.log(f"调用大模型失败: {str(e)}")
            return f"思考中... ({str(e)})"