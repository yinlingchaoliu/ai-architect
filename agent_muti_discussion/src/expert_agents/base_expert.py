from typing import Dict, Any

from ..core.base_agent import BaseAgent, AgentResponse


class BaseExpertAgent(BaseAgent):
    def __init__(self, name: str, role: str, domain: str):
        super().__init__(name, role)
        self.domain = domain
        self.knowledge_sources = []

    async def process(self, input_text: str, context: Dict[str, Any] = None) -> AgentResponse:
        discussion_history = context.get('discussion_history', [])

        # 1. 必要时进行知识查询
        if self._needs_knowledge_search(input_text):
            try:
                knowledge = await self.use_plugin('web_search', query=input_text)
                if knowledge is None:
                    knowledge = {}
            except Exception:
                knowledge = {}
        else:
            try:
                knowledge = await self.use_plugin('knowledge_base', domain=self.domain, query=input_text)
                if knowledge is None:
                    knowledge = {}
            except Exception:
                knowledge = {}

        # 2. 基于领域知识生成响应
        expert_response = await self._generate_expert_response(
            input_text, knowledge, discussion_history
        )

        # 3. 判断是否需要反思
        requires_reflection = self._check_reflection_need(expert_response, discussion_history)

        return AgentResponse(
            content=expert_response,
            metadata={
                "domain": self.domain,
                "knowledge_sources": self.knowledge_sources,
                "confidence": 0.8  # 置信度
            },
            requires_reflection=requires_reflection
        )
    
    def _needs_knowledge_search(self, input_text: str) -> bool:
        """判断是否需要进行知识搜索"""
        # 简单实现：检查是否包含需要最新信息的关键词
        recent_knowledge_keywords = ["最新", "最新的", "最近", "现在", "当前", "2024", "2025", "趋势"]
        for keyword in recent_knowledge_keywords:
            if keyword in input_text:
                return True
        return False
    
    async def _generate_expert_response(self, input_text: str, knowledge: Dict, discussion_history: list) -> str:
        """生成专家响应 - 子类应该覆盖这个方法"""
        # 调用LLM生成响应
        return await self._call_llm(input_text)
    
    def _check_reflection_need(self, response: str, discussion_history: list) -> bool:
        """检查是否需要反思"""
        # 简单实现：如果响应中包含不确定性词汇，则需要反思
        uncertainty_keywords = ["可能", "大概", "或许", "不确定", "需要进一步", "有待", "假设"]
        for keyword in uncertainty_keywords:
            if keyword in response:
                return True
        return False