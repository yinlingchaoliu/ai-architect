from .base_expert import BaseExpertAgent
from ..core.base_agent import AgentResponse
from typing import Dict, Any, List
import asyncio


class BusinessExpertAgent(BaseExpertAgent):
    def __init__(self):
        super().__init__("商业专家", "商业分析和市场策略专家", "business")
        self.business_domains = ["市场分析", "商业模式", "成本效益", "竞争优势", "风险管理"]

    async def _generate_expert_response(self, input_text: str, knowledge: Dict, discussion_history: List[Dict]) -> str:
        """生成商业专家响应"""

        business_aspects = self._extract_business_aspects(input_text, discussion_history)

        analysis_prompt = f"""
        作为商业专家，请对以下问题进行商业分析：

        问题：{input_text}

        商业方面：{business_aspects}
        市场数据：{knowledge.get('results', {})}

        请从以下角度提供专业分析：
        1. 市场机会和规模
        2. 商业模式可行性
        3. 成本效益分析
        4. 竞争优势构建
        5. 风险和应对策略

        请结合市场数据和商业逻辑进行回应。
        """

        response = await self._call_business_llm(analysis_prompt)
        return response

    def _extract_business_aspects(self, text: str, history: List[Dict]) -> List[str]:
        """提取商业相关方面"""
        aspects = []
        business_keywords = ["市场", "商业", "成本", "收益", "竞争", "客户", "价值"]

        for keyword in business_keywords:
            if keyword in text:
                aspects.append(keyword)

        # 检查历史中的商业考量
        for entry in history[-3:]:
            content = entry.get('content', '')
            if any(keyword in content for keyword in business_keywords):
                aspects.append("历史商业讨论")
                break

        return aspects if aspects else ["通用商业考量"]

    async def _call_business_llm(self, prompt: str) -> str:
        """调用商业专用LLM"""
        await asyncio.sleep(0.1)

        business_responses = [
            "从市场角度看，这个方向具有巨大的潜力，目标市场规模预计...",
            "商业模式方面，建议采用SaaS订阅模式，因为...",
            "成本效益分析显示，初期投入需要X万元，预计ROI在Y年内达到Z%...",
            "竞争优势可以通过以下方式构建：1. 技术壁垒 2. 网络效应 3. 品牌建设...",
            "主要商业风险包括市场竞争、用户获取成本和盈利周期..."
        ]

        return business_responses[len(prompt) % len(business_responses)]

    def _check_reflection_need(self, response: str, discussion_history: List[Dict]) -> bool:
        """检查是否需要反思"""
        # 如果与技术要求有冲突，需要反思
        recent_tech_comments = [
            entry['content'] for entry in discussion_history[-5:]
            if '技术' in entry.get('speaker', '')
        ]

        conflict_terms = ["成本过高", "市场不接受", "商业模式不成立", "盈利困难"]
        if any(conflict_term in response for conflict_term in conflict_terms) and recent_tech_comments:
            return True

        # 如果包含模糊的商业判断
        vague_indicators = ["可能有机会", "需要验证", "取决于市场", "不太确定"]
        if any(indicator in response for indicator in vague_indicators):
            return True

        return False