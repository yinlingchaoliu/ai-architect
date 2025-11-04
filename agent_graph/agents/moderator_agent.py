# agents/moderator_agent.py
from .base_agent import BaseAgent, AgentResponse
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

import os
from typing import List, Dict, Any


class ModeratorAgent(BaseAgent):
    def __init__(self):
        system_prompt = """你是一个专业的会议主持人。你的职责是：
        1. 主持会议流程，确保讨论有序进行
        2. 邀请相关专家发言，平衡各方观点
        3. 提出引导性问题，促进深度讨论
        4. 识别共识和分歧，推动达成一致
        5. 在适当时机总结讨论成果

        请保持中立、专业，确保每个专家都有充分表达的机会。"""

        super().__init__("主持人", "会议主持", system_prompt)
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.3,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.discussion_rounds = 0
        self.max_rounds = 5

    async def generate_response(self, context: Dict[str, Any]) -> AgentResponse:
        discussion_history = context.get("discussion_history", [])
        current_speaker = context.get("current_speaker", "")
        analyzed_requirements = context.get("analyzed_requirements", "")

        self.discussion_rounds += 1

        # 构建讨论上下文
        discussion_context = self._build_discussion_context(discussion_history, analyzed_requirements)

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""
            当前讨论状态：
            {discussion_context}

            请根据以上讨论：
            1. 评估讨论进展
            2. 决定下一步行动（继续讨论/总结）
            3. 提出引导性问题或总结观点
            """)
        ]

        response = self.llm(messages)

        # 判断是否需要结束讨论
        should_conclude = self._should_conclude_discussion(discussion_history)

        return AgentResponse(
            content=response.content,
            reasoning=f"主持了第{self.discussion_rounds}轮讨论，评估了进展",
            tools_used=[],
            needs_reflection=should_conclude
        )

    def _build_discussion_context(self, history: List[Dict], requirements: str) -> str:
        context = f"需求分析结果：\n{requirements}\n\n讨论历史：\n"
        for i, turn in enumerate(history, 1):
            context += f"第{i}轮 - {turn['speaker']}: {turn['content']}\n"
        return context

    def _should_conclude_discussion(self, history: List[Dict]) -> bool:
        if self.discussion_rounds >= self.max_rounds:
            return True

        if len(history) < 3:
            return False

        # 简单的共识检测逻辑
        recent_turns = history[-3:]
        contents = [turn['content'].lower() for turn in recent_turns]

        # 如果最近几轮内容相似，可能达成共识
        consensus_keywords = ["同意", "赞同", "共识", "一致", "支持"]
        consensus_count = sum(1 for content in contents
                              if any(keyword in content for keyword in consensus_keywords))

        return consensus_count >= 2

    async def reflect(self, discussion_history: List[Dict], moderator_guidance: str) -> AgentResponse:
        # 主持人的反思主要是调整主持策略
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""
            基于之前的讨论和引导，请反思：
            1. 讨论是否有效推进？
            2. 是否需要调整主持策略？
            3. 如何更好地促进专家达成共识？

            讨论历史：{discussion_history}
            之前的引导：{moderator_guidance}
            """)
        ]

        response = self.llm(messages)

        return AgentResponse(
            content=response.content,
            reasoning="反思了主持效果和讨论进展",
            tools_used=[],
            needs_reflection=False
        )