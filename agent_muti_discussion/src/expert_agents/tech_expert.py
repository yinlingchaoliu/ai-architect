from .base_expert import BaseExpertAgent
from ..core.base_agent import AgentResponse
from typing import Dict, Any, List
import asyncio


class TechExpertAgent(BaseExpertAgent):
    def __init__(self):
        super().__init__("技术专家", "技术架构和实现专家", "technology")
        self.technical_domains = ["AI", "机器学习", "软件架构", "系统设计", "编程"]

    async def _generate_expert_response(self, input_text: str, knowledge: Dict, discussion_history: List[Dict]) -> str:
        """生成技术专家响应"""

        # 分析当前讨论的技术方面
        technical_aspects = self._extract_technical_aspects(input_text, discussion_history)

        # 构建技术分析
        analysis_prompt = f"""
        作为技术专家，请对以下问题进行技术分析：

        问题：{input_text}

        技术方面：{technical_aspects}
        相关知识：{knowledge.get('results', {})}

        请从以下角度提供专业分析：
        1. 技术可行性
        2. 实现复杂度
        3. 技术选型建议
        4. 潜在技术风险
        5. 最佳实践建议

        请以专业、客观的语气回应。
        """

        # 模拟调用大模型
        response = await self._call_technical_llm(analysis_prompt)
        return response

    def _extract_technical_aspects(self, text: str, history: List[Dict]) -> List[str]:
        """提取技术相关方面"""
        aspects = []
        tech_keywords = ["系统", "架构", "技术", "实现", "开发", "代码", "算法", "数据"]

        for keyword in tech_keywords:
            if keyword in text:
                aspects.append(keyword)

        # 从历史中提取技术话题
        for entry in history[-3:]:  # 最近3条记录
            if any(keyword in entry.get('content', '') for keyword in tech_keywords):
                aspects.append("历史技术讨论")
                break

        return aspects if aspects else ["通用技术考虑"]

    async def _call_technical_llm(self, prompt: str) -> str:
        """调用技术专用LLM"""
        # 模拟技术专家的专业响应
        await asyncio.sleep(0.1)

        technical_responses = [
            "从技术架构角度看，建议采用微服务架构，因为...",
            "在技术实现上，需要考虑以下关键点：1. 可扩展性 2. 安全性 3. 性能优化...",
            "基于当前技术趋势，我推荐使用以下技术栈：后端使用Python/FastAPI，前端使用React...",
            "技术风险评估：主要风险包括数据安全、系统稳定性和技术债务..."
        ]

        return technical_responses[len(prompt) % len(technical_responses)]

    def _check_reflection_need(self, response: str, discussion_history: List[Dict]) -> bool:
        """检查是否需要反思"""
        # 如果响应中包含不确定词汇或与其他专家观点冲突，需要反思
        uncertainty_indicators = ["可能", "不确定", "需要进一步研究", "取决于"]
        if any(indicator in response for indicator in uncertainty_indicators):
            return True

        # 检查是否与商业专家观点有潜在冲突
        recent_business_comments = [
            entry['content'] for entry in discussion_history[-5:]
            if '商业' in entry.get('speaker', '')
        ]

        if recent_business_comments and any(
                conflict_term in response for conflict_term in ["成本高", "开发周期长", "技术复杂"]
        ):
            return True

        return False