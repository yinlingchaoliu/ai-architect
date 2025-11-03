import os
from typing import Dict, Any
import yaml


class Config:
    """配置管理类"""

    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.model_name = os.getenv("MODEL_NAME", "gpt-4")
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("MAX_TOKENS", "2000"))

        # 加载agent配置
        self.agent_config = self._load_agent_config()

    def _load_agent_config(self) -> Dict[str, Any]:
        """加载agent配置文件"""
        try:
            with open('config/agent_config.yaml', 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # 返回默认配置
            return {
                'analyzer': {
                    'system_prompt': '你是一个专业的需求分析师，擅长分析和完善用户需求。'
                },
                'moderator': {
                    'system_prompt': '你是一个专业的会议主持人，擅长组织和引导专家讨论。',
                    'max_rounds': 3
                },
                'experts': {
                    'tech_expert': {
                        'system_prompt': '你是一个技术专家，擅长技术架构、系统设计和实现方案。',
                        'tools': ['web_search', 'code_analysis']
                    },
                    'business_expert': {
                        'system_prompt': '你是一个商业专家，擅长商业模式、市场分析和商业价值评估。',
                        'tools': ['market_analysis', 'financial_analysis']
                    },
                    'research_expert': {
                        'system_prompt': '你是一个研究专家，擅长技术趋势、学术研究和创新方法。',
                        'tools': ['academic_search', 'trend_analysis']
                    }
                }
            }


config = Config()