from typing import Dict, Any, List
# from langchain.schema import HumanMessage

from ..core.base_agent import BaseAgent
from ..utils.logger import logger


class ModeratorAgent(BaseAgent):
    """会议主持人智能体"""

    def __init__(self, max_rounds: int = 3):
        system_prompt = """你是一个专业的会议主持人，擅长组织和引导专家讨论。

你的职责：
1. 主持会议进程，确保讨论有序进行
2. 邀请合适的专家参与讨论
3. 在适当时机提出问题，引导讨论方向
4. 总结讨论成果，形成最终结论
5. 处理专家间的分歧，促进共识达成

请确保：
- 讨论保持专业和高效
- 每个专家都有充分表达机会
- 讨论不偏离主题
- 及时总结关键观点

请用中文回复。"""

        super().__init__("会议主持人", system_prompt)
        self.max_rounds = max_rounds
        self.current_round = 0

    def process(self, analyzed_requirement: str, expert_opinions: List[Dict] = None, **kwargs) -> Dict[str, Any]:
        """主持会议讨论"""
        logger.info("主持人开始主持会议")

        self.current_round += 1

        # 构建主持提示
        moderation_prompt = self._build_moderation_prompt(analyzed_requirement, expert_opinions)

        # 生成主持响应
        moderation_response = self.generate_response(moderation_prompt)

        # 判断是否继续讨论
        should_continue = self._should_continue_discussion(moderation_response, expert_opinions)

        result = {
            "moderator_decision": moderation_response,
            "current_round": self.current_round,
            "max_rounds": self.max_rounds,
            "should_continue": should_continue,
            "discussion_complete": not should_continue or self.current_round >= self.max_rounds
        }

        logger.info(f"主持人处理完成，轮次: {self.current_round}/{self.max_rounds}")
        return result

    def _build_moderation_prompt(self, requirement: str, expert_opinions: List[Dict] = None) -> str:
        """构建主持提示"""
        prompt = f"""
当前讨论需求：{requirement}

"""

        if expert_opinions:
            prompt += "专家意见汇总：\n"
            for i, opinion in enumerate(expert_opinions):
                prompt += f"\n{opinion.get('expert_name', f'专家{i + 1}')}：{opinion.get('opinion', '')}\n"

            prompt += f"\n当前是第 {self.current_round} 轮讨论。"

            if self.current_round == 1:
                prompt += "\n\n作为主持人，请：\n1. 欢迎各位专家并介绍讨论主题\n2. 提出引导性问题开始讨论\n3. 明确讨论目标和期望成果"
            else:
                prompt += "\n\n作为主持人，请：\n1. 总结当前讨论进展\n2. 指出存在的分歧或共识\n3. 提出引导性问题促进深入讨论\n4. 判断是否需要进行下一轮讨论"
        else:
            prompt += "\n这是首次讨论，请：\n1. 介绍讨论主题和参与专家\n2. 提出引导性问题开始讨论\n3. 明确讨论规则和期望"

        prompt += "\n\n请输出你的主持决策："

        return prompt

    def _should_continue_discussion(self, moderation_response: str, expert_opinions: List[Dict] = None) -> bool:
        """判断是否继续讨论"""
        if self.current_round >= self.max_rounds:
            return False

        if not expert_opinions:
            return True

        # 基于主持人响应内容判断
        continue_keywords = ["继续", "下一轮", "进一步", "深入讨论", "尚未达成"]
        stop_keywords = ["总结", "结束", "达成共识", "结论", "完成"]

        response_lower = moderation_response.lower()

        continue_count = sum(1 for keyword in continue_keywords if keyword in response_lower)
        stop_count = sum(1 for keyword in stop_keywords if keyword in response_lower)

        return continue_count > stop_count

    def reset_rounds(self):
        """重置讨论轮次"""
        self.current_round = 0
        logger.info("主持人轮次已重置")