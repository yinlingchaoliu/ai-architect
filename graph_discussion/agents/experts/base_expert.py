# 专家基类
from abc import ABC, abstractmethod
from typing import Dict, List

# 尝试直接导入BaseAgent，如果路径有问题可能需要调整
from ..base_agent import BaseAgent


class BaseExpert(BaseAgent):
    """专家基类"""
    
    def __init__(self, name: str, role: str, color: str, domain: str):
        super().__init__(name, role, color)
        self.domain = domain
    
    @abstractmethod
    def speak(self, question: str, context: List[Dict]) -> str:
        """专家发言"""
        pass