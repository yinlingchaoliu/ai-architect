# agents/experts/base_expert.py
from ..base_agent import BaseAgent, AgentResponse
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

import os
from typing import List, Dict, Any


class BaseExpert(BaseAgent):
    def __init__(self, name: str, role: str, system_prompt: str, expertise: str):
        super().__init__(name, role, system_prompt)
        self.expertise = expertise
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.8,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.previous_responses = []

    async def generate_response(self, context: Dict[str, Any]) -> AgentResponse:
        discussion_history = context.get("discussion_history", [])
        requirements = context.get("analyzed_requirements", "")
        moderator_guidance = context.get("moderator_guidance", "")

        # 使用工具获取额外信息
        external_info = await self._gather_external_info(requirements)

        prompt = self._build_expert_prompt(
            requirements, discussion_history, moderator_guidance, external_info
        )

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]

        response = self.llm(messages)

        agent_response = AgentResponse(
            content=response.content,
            reasoning=f"基于{self.expertise}专业知识进行分析",
            tools_used=list(self.tools.keys()),
            needs_reflection=True
        )

        self.previous_responses.append(agent_response.content)
        return agent_response

    async def reflect(self, discussion_history: List[Dict], moderator_guidance: str) -> AgentResponse:
        # 专家的反思：基于新信息调整观点
        recent_discussion = discussion_history[-5:]  # 只看最近5轮

        reflection_prompt = f"""
        基于以下讨论和主持人引导，请反思你之前的观点：

        讨论历史：
        {recent_discussion}

        主持人引导：
        {moderator_guidance}

        请思考：
        1. 是否需要修正之前的观点？
        2. 是否有新的信息改变了你的看法？
        3. 如何更好地与其他专家达成共识？

        请给出反思后的观点：
        """

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=reflection_prompt)
        ]

        response = self.llm(messages)

        return AgentResponse(
            content=response.content,
            reasoning="基于新讨论进行了深度反思",
            tools_used=[],
            needs_reflection=False
        )

    def _build_expert_prompt(self, requirements: str, history: List[Dict],
                             guidance: str, external_info: str) -> str:
        return f"""
        需求分析：{requirements}

        讨论历史：
        {self._format_discussion_history(history)}

        主持人引导：{guidance}

        相关外部信息：{external_info}

        请基于你的{self.expertise}专业知识：
        1. 分析问题并提出专业见解
        2. 回应其他专家的观点
        3. 提出具体建议或解决方案
        4. 考虑实际可行性和影响
        """

    def _format_discussion_history(self, history: List[Dict]) -> str:
        formatted = ""
        for turn in history[-10:]:  # 只看最近10轮
            formatted += f"{turn['speaker']}: {turn['content']}\n\n"
        return formatted

    async def _gather_external_info(self, requirements: str) -> str:
        info = ""
        # 使用注册的工具收集信息
        if "web_search" in self.tools:
            search_results = await self.tools["web_search"](requirements)
            info += f"网络搜索信息：{search_results}\n"

        if "rag_search" in self.tools:
            rag_results = await self.tools["rag_search"](requirements)
            info += f"知识库信息：{rag_results}\n"

        return info