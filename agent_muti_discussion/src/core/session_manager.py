from typing import Dict, Any, List, Optional
from ..agents.analyzer_agent import AnalyzerAgent
from ..agents.moderator_agent import ModeratorAgent
from ..expert_agents.tech_expert import TechExpertAgent
from ..expert_agents.business_expert import BusinessExpertAgent
from ..expert_agents.research_expert import ResearchExpertAgent
from ..core.consensus_checker import ConsensusChecker
from ..utils.logger import logger

# 颜色常量定义
class Colors:
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'


class SessionManager:
    """会话管理器"""

    def __init__(self, max_rounds: int = 10):
        self.analyzer = AnalyzerAgent()
        self.moderator = ModeratorAgent()
        self.consensus_checker = ConsensusChecker()

        # 初始化专家池
        self.experts = {
            "tech_expert": TechExpertAgent(),
            "business_expert": BusinessExpertAgent(),
            "research_expert": ResearchExpertAgent()
        }

        # 讨论状态和配置
        self.discussion_history: List[Dict[str, Any]] = []
        self.current_round = 0
        self.is_completed = False
        self.max_rounds = max_rounds  # 最大讨论轮数，默认10次

    def process_user_input(self, user_input: str) -> Dict[str, Any]:
        """处理用户输入，启动多轮讨论"""
        logger.info("开始处理用户输入")

        # 重置状态
        self._reset_session()

        # 步骤1: 需求分析
        analysis_result = self.analyzer.process(user_input)
        analyzed_requirement = analysis_result["analyzed_requirement"]

        # 步骤2: 开始多轮讨论
        final_result = self._conduct_discussion(analyzed_requirement)

        # 组合最终结果
        result = {
            "original_question": user_input,
            "analyzed_requirement": analyzed_requirement,
            "discussion_rounds": self.current_round,
            "final_summary": final_result,
            "discussion_history": self.discussion_history
        }

        logger.info("用户输入处理完成")
        return result

    def _conduct_discussion(self, analyzed_requirement: str) -> Dict[str, Any]:
        """执行多轮讨论"""
        expert_opinions = []
        moderator_decision = None

        while not self.is_completed:
            self.current_round += 1
            logger.info(f"开始第 {self.current_round} 轮讨论")
            
            # 检查是否达到最大轮数
            if self.current_round >= self.max_rounds:
                logger.info(f"已达到最大讨论轮数 {self.max_rounds}，讨论结束")
                self.is_completed = True
                break

            # 邀请专家发言
            round_opinions = self._invite_experts(analyzed_requirement, expert_opinions)
            expert_opinions.extend(round_opinions)
            
            # 打印专家意见（蓝色）
            for opinion in round_opinions:
                logger.warning(f"{opinion['expert_name']} 思考/提示词: {opinion['expert_logic']}")
                logger.warning(f"{opinion['expert_name']} 发言: {opinion['opinion']}")

            # 主持人引导
            moderator_result = self.moderator.process(
                analyzed_requirement,
                expert_opinions=round_opinions
            )
            moderator_decision = moderator_result["moderator_decision"]
            
            # 打印主持人决策（红色）
            print(f"\n{Colors.RED}主持人 需求专家 思考/提示词: ...{Colors.RESET}")
            print(f"{Colors.RED}主持人 需求专家 发言: {moderator_decision}{Colors.RESET}")

            # 记录本轮讨论
            round_record = {
                "round": self.current_round,
                "expert_opinions": round_opinions,
                "moderator_decision": moderator_decision
            }
            self.discussion_history.append(round_record)

            # 检查是否结束讨论
            if moderator_result["discussion_complete"]:
                self.is_completed = True
                logger.info("讨论结束")
                break

        # 生成最终总结
        final_summary = self._generate_final_summary(analyzed_requirement, expert_opinions)
        return final_summary

    def _invite_experts(self, requirement: str, previous_opinions: List[Dict] = None) -> List[Dict[str, Any]]:
        """邀请专家发言"""
        opinions = []

        # 构建讨论上下文
        context = {
            "requirement": requirement,
            "previous_rounds": len(previous_opinions) // len(self.experts) if previous_opinions else 0
        }

        # 如果是第一轮，所有专家都发言
        if not previous_opinions:
            for expert_id, expert in self.experts.items():
                opinion = expert.process(requirement, context=context)
                opinions.append(opinion)
        else:
            # 后续轮次，专家可以参考之前的意见
            context["previous_opinions"] = previous_opinions
            for expert_id, expert in self.experts.items():
                # 可以在这里添加逻辑，让专家参考其他专家的意见进行反思
                # 暂时简单处理：直接再次邀请发言
                opinion = expert.process(requirement, context=context)
                opinions.append(opinion)

        return opinions

    def _generate_final_summary(self, requirement: str, expert_opinions: List[Dict]) -> Dict[str, Any]:
        """生成最终总结"""
        # 使用一致性检查器
        consensus_result = self.consensus_checker.check_consensus(expert_opinions)

        # 构建总结提示
        summary_prompt = f"""
基于以下需求和专家讨论，生成最终总结：

需求：{requirement}

专家意见汇总：
"""
        for opinion in expert_opinions:
            summary_prompt += f"\n{opinion['expert_name']}：{opinion['opinion']}\n"

        summary_prompt += f"\n一致性检查结果：{'达成共识' if consensus_result['consensus_achieved'] else '未完全达成共识'}"
        summary_prompt += "\n\n请生成一个全面的总结，包括：\n1. 主要观点和结论\n2. 共识领域\n3. 分歧点（如果有）\n4. 最终建议"

        # 使用主持人来生成总结
        final_summary = self.moderator.generate_response(summary_prompt)

        return {
            "summary": final_summary,
            "consensus_result": consensus_result,
            "total_opinions": len(expert_opinions)
        }

    def _reset_session(self):
        """重置会话状态"""
        self.discussion_history = []
        self.current_round = 0
        self.is_completed = False
        self.moderator.reset_rounds()

        # 清空所有智能体的历史
        self.analyzer.clear_history()
        self.moderator.clear_history()
        for expert in self.experts.values():
            expert.clear_history()

        logger.info("会话状态已重置")

    def get_discussion_status(self) -> Dict[str, Any]:
        """获取当前讨论状态"""
        return {
            "current_round": self.current_round,
            "is_completed": self.is_completed,
            "total_rounds": len(self.discussion_history)
        }