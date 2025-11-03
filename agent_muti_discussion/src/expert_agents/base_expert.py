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
            knowledge = await self.use_plugin('web_search', query=input_text)
        else:
            knowledge = await self.use_plugin('knowledge_base', domain=self.domain, query=input_text)

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