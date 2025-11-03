from typing import Dict, Any

from ..core.base_agent import BaseAgent, AgentResponse


class ModeratorAgent(BaseAgent):
    def __init__(self):
        super().__init__("Moderator", "会议主持和流程控制专家")
        self.reflection_triggers = ["矛盾", "不确定", "需要澄清", "意见分歧"]

    async def process(self, input_text: str, context: Dict[str, Any] = None) -> AgentResponse:
        discussion_history = context.get('discussion_history', [])
        current_speaker = context.get('current_speaker')

        # 分析当前讨论状态
        analysis = await self._analyze_discussion_state(discussion_history)

        if analysis.get('needs_intervention'):
            # 提出反思问题
            reflection_question = self._generate_reflection_question(
                current_speaker, analysis['issue_type']
            )
            return AgentResponse(
                content=reflection_question,
                metadata={"action": "request_reflection", "target_agent": current_speaker},
                requires_reflection=True
            )

        # 正常推进讨论
        if self._is_consensus_reached(discussion_history):
            summary = await self._generate_summary(discussion_history)
            return AgentResponse(
                content=summary,
                metadata={"action": "conclude_discussion"}
            )
        else:
            # 指定下一个发言者或提出新问题
            next_action = await self._determine_next_action(discussion_history)
            return AgentResponse(
                content=next_action,
                metadata={"action": "continue_discussion"}
            )