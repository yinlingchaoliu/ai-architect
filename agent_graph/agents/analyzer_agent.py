# agents/analyzer_agent.py
from typing import Dict, Any, List

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from .base_agent import BaseAgent, AgentResponse

import os


class AnalyzerAgent(BaseAgent):
    def __init__(self):
        system_prompt = """你是一个专业的需求分析师。你的职责是：
        1. 分析用户提出的问题，理解核心需求
        2. 完善和澄清需求，确保需求明确具体
        3. 识别需求中的潜在风险和挑战
        4. 将分析结果提交给会议主持人

        请确保你的分析全面、专业，为后续专家讨论提供清晰的基础。"""

        super().__init__("需求分析师", "需求分析专家", system_prompt)
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

    async def generate_response(self, context: Dict[str, Any]) -> AgentResponse:
        user_query = context.get("user_query", "")

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"请分析以下用户需求：\n\n{user_query}")
        ]

        response = self.llm.invoke(messages)

        return AgentResponse(
            content=response.content,
            reasoning="分析了用户需求，识别了核心要点和潜在问题",
            tools_used=[],
            needs_reflection=False
        )

    async def reflect(self, discussion_history: List[Dict], moderator_guidance: str) -> AgentResponse:
        # 需求分析师通常不需要深度反思
        return AgentResponse(
            content="需求分析已完成，等待专家讨论结果",
            reasoning="作为需求分析师，主要职责在前期已完成",
            tools_used=[],
            needs_reflection=False
        )