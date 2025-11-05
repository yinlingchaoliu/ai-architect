# 配置管理
import os
from typing import Dict, Any

class Config:
    """配置类"""
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.model_name = "gpt-4"
        self.max_rounds = 3  # 最大讨论轮次
        
        # 专家配置
        self.expert_configs = {
            "技术专家": {
                "color": "blue",
                "description": "负责技术可行性分析和实施方案设计"
            },
            "商业专家": {
                "color": "green", 
                "description": "负责商业模式、市场分析和商业价值评估"
            },
            "研究专家": {
                "color": "magenta",
                "description": "负责研究趋势、创新点和学术支持"
            }
        }

config = Config()