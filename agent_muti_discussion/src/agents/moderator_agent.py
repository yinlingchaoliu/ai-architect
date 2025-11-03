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
    
    async def _analyze_discussion_state(self, discussion_history: list) -> dict:
        """分析讨论状态"""
        # 简单实现：如果讨论历史太短，不需要干预
        if len(discussion_history) < 2:
            return {"needs_intervention": False}
        
        # 检查是否包含反思触发词
        for message in discussion_history[-2:]:  # 检查最近两条消息
            if any(trigger in message.get('content', '') for trigger in self.reflection_triggers):
                return {
                    "needs_intervention": True,
                    "issue_type": "conflict",
                    "trigger_message": message.get('content', '')
                }
        
        return {"needs_intervention": False}
    
    def _generate_reflection_question(self, speaker: str, issue_type: str) -> str:
        """生成反思问题"""
        if issue_type == "conflict":
            return f"{speaker}，我注意到您的观点可能与之前的讨论存在一些不一致。能否进一步澄清您的立场？"
        else:
            return f"{speaker}，为了更好地推进讨论，请您再详细解释一下这个观点。"
    
    def _is_consensus_reached(self, discussion_history: list) -> bool:
        """判断是否达成共识"""
        # 简单实现：如果讨论轮数达到5轮，就认为可以总结了
        return len(discussion_history) >= 5
    
    async def _generate_summary(self, discussion_history: list) -> str:
        """生成讨论总结"""
        # 简单实现：调用LLM生成总结
        summary_prompt = "请总结以下讨论内容：\n" + "\n".join(
            [f"{msg.get('role', 'Unknown')}: {msg.get('content', '')}" for msg in discussion_history]
        )
        return await self._call_llm(summary_prompt)
    
    async def _determine_next_action(self, discussion_history: list) -> str:
        """确定下一步行动"""
        # 简单实现：调用LLM确定下一步
        prompt = f"根据以下讨论历史，确定下一步讨论方向或提出下一个问题：\n"
        prompt += "\n".join([f"{msg.get('role', 'Unknown')}: {msg.get('content', '')}" for msg in discussion_history[-3:]])
        return await self._call_llm(prompt)