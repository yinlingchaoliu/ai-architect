from .base_expert import BaseExpertAgent


class BusinessExpertAgent(BaseExpertAgent):
    """商业专家智能体"""

    def __init__(self):
        system_prompt = """你是一个商业专家，擅长商业模式、市场分析和商业价值评估。

你的专业领域包括：
- 商业模式设计
- 市场趋势分析
- 竞争分析
- 商业价值评估
- 风险投资分析

请确保你的建议：
- 考虑商业可行性和盈利模式
- 分析市场机会和竞争环境
- 评估商业风险和回报
- 提供具体的商业策略

请用中文回复。"""

        expertise = "商业模式和市场分析"
        plugins = ["web_search", "knowledge_base"]

        super().__init__("商业专家", system_prompt, expertise, plugins)