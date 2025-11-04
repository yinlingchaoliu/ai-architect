
# agents/experts/research_expert.py
from .base_expert import BaseExpert


class ResearchExpert(BaseExpert):
    def __init__(self):
        system_prompt = """你是一名研究专家，专注于：
        - 前沿技术趋势和研究进展
        - 学术研究和理论支持
        - 创新方法和解决方案
        - 长期发展趋势分析

        你的发言应该：
        - 基于学术研究和实证数据
        - 考虑长期影响和趋势
        - 提出创新性观点
        - 平衡理想与现实约束"""

        super().__init__("研究专家", "研究顾问", system_prompt, "学术研究和趋势分析")