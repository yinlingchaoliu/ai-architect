from .base_expert import BaseExpertAgent
from ..core.base_agent import AgentResponse
from typing import Dict, Any, List
import asyncio


class ResearchExpertAgent(BaseExpertAgent):
    def __init__(self):
        super().__init__("研究专家", "学术研究和数据分析专家", "research")
        self.research_domains = ["数据分析", "学术研究", "实证验证", "方法论"]

    async def _generate_expert_response(self, input_text: str, knowledge: Dict, discussion_history: List[Dict]) -> str:
        """生成研究专家响应"""

        research_aspects = self._extract_research_aspects(input_text, discussion_history)

        analysis_prompt = f"""
        作为研究专家，请对以下问题进行学术和研究分析：

        问题：{input_text}

        研究方面：{research_aspects}
        相关研究：{knowledge.get('results', {})}

        请从以下角度提供专业分析：
        1. 相关学术研究现状
        2. 数据支持和证据强度
        3. 研究方法和验证方式
        4. 潜在的研究空白
        5. 实证建议和研究方向

        请基于学术严谨性进行回应。
        """

        response = await self._call_research_llm(analysis_prompt)
        return response

    def _extract_research_aspects(self, text: str, history: List[Dict]) -> List[str]:
        """提取研究相关方面"""
        aspects = []
        research_keywords = ["研究", "数据", "验证", "实验", "分析", "证据", "方法论"]

        for keyword in research_keywords:
            if keyword in text:
                aspects.append(keyword)

        return aspects if aspects else ["通用研究考量"]

    async def _call_research_llm(self, prompt: str) -> str:
        """调用研究专用LLM"""
        await asyncio.sleep(0.1)

        research_responses = [
            "根据现有学术研究，这个领域的主要发现包括...",
            "从研究方法论角度，建议采用混合研究方法，结合定量和定性分析...",
            "数据支持方面，需要收集以下类型的数据：用户行为数据、市场数据、实验数据...",
            "研究空白分析显示，当前缺乏关于X的实证研究，这提供了重要的研究机会...",
            "验证策略建议：通过A/B测试、用户调研和数据分析来验证假设..."
        ]

        return research_responses[len(prompt) % len(research_responses)]

    def _check_reflection_need(self, response: str, discussion_history: List[Dict]) -> bool:
        """检查是否需要反思"""
        # 如果缺乏数据支持或方法论不清晰，需要反思
        weak_evidence_indicators = ["缺乏数据", "需要更多研究", "方法论待完善", "证据不足"]
        if any(indicator in response for indicator in weak_evidence_indicators):
            return True

        return False