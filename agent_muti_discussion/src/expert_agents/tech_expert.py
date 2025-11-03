from .base_expert import BaseExpertAgent


class TechExpertAgent(BaseExpertAgent):
    """技术专家智能体"""

    def __init__(self):
        system_prompt = """你是一个技术专家，擅长技术架构、系统设计和实现方案。

你的专业领域包括：
- 软件架构设计
- 技术选型和评估
- 系统实现方案
- 性能优化
- 技术风险评估

请确保你的建议：
- 具有技术可行性和先进性
- 考虑系统的可扩展性和维护性
- 评估技术实现的风险
- 提供具体的技术方案

请用中文回复。"""

        expertise = "技术架构和系统设计"
        plugins = ["web_search", "knowledge_base"]

        super().__init__("技术专家", system_prompt, expertise, plugins)