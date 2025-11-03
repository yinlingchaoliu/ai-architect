from typing import Dict, Any

from ..core.base_agent import BaseAgent, AgentResponse


# from core.base_agent import AgentResponse,BaseAgent

class AnalyzerAgent(BaseAgent):
    def __init__(self):
        super().__init__("Analyzer", "问题分析和需求提炼专家")

    async def process(self, input_text: str, context: Dict[str, Any] = None) -> AgentResponse:
        # 分析用户问题，完善需求描述
        analysis_prompt = f"""
        请对以下用户问题进行深入分析：

        原始问题：{input_text}

        请完成：
        1. 完善问题描述，使其更清晰具体
        2. 分析任务的基本需求和隐含需求
        3. 识别需要哪些领域的专家参与讨论
        4. 提出讨论的关键要点

        请以结构化的方式输出分析结果。
        """

        # 这里可以集成大模型调用
        analyzed_content = await self._call_llm(analysis_prompt)

        return AgentResponse(
            content=analyzed_content,
            metadata={
                "task_requirements": "提取的需求列表",
                "needed_experts": ["技术", "商业", "研究"],
                "key_points": ["要点1", "要点2"]
            }
        )