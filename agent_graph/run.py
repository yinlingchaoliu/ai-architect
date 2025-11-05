from typing import Dict, List, Any, TypedDict
from langgraph.graph import StateGraph, END


# 定义状态结构
class ConferenceState(TypedDict):
    user_question: str
    requirement_analysis: str
    expert_opinions: Dict[str, str]  # 专家观点存储
    current_expert: str
    discussion_round: int
    should_continue: bool
    expert_summaries: Dict[str, str]
    final_summary: str
    meeting_output: str


# 角色定义和功能实现
class RequirementAnalyst:
    def analyze(self, question: str) -> str:
        """需求分析师分析用户问题"""
        return f"需求分析：基于'{question}'，明确会议需要讨论的技术可行性、商业价值和研究方向。"


class Moderator:
    def __init__(self):
        self.experts = ["技术专家", "商业专家", "研究专家"]
        self.current_expert_index = 0

    def start_meeting(self, requirement: str) -> str:
        """召开会议"""
        return f"主持人：会议开始。基于需求分析：{requirement}，请各位专家依次发言。"

    def ask_question(self, requirement: str, current_expert: str) -> str:
        """向特定专家提问"""
        expert_questions = {
            "技术专家": f"从技术实现角度，如何看待'{requirement}'？",
            "商业专家": f"从商业价值角度，'{requirement}'有哪些机会和风险？",
            "研究专家": f"从研究视角，'{requirement}'有哪些创新点和研究价值？"
        }
        return f"主持人提问{current_expert}：{expert_questions.get(current_expert, '请发表您的观点')}"

    def judge_should_continue(self, expert_opinions: Dict[str, str], round: int) -> bool:
        """判断是否需要继续讨论"""
        if round >= 2:  # 最多进行2轮讨论
            return False

        # 简单的判断逻辑：如果所有专家都有充分发言，则结束
        opinions_count = sum(1 for opinion in expert_opinions.values() if len(opinion) > 50)
        return opinions_count < len(expert_opinions)

    def summarize_meeting(self, expert_summaries: Dict[str, str], final_summary: str) -> str:
        """总结会议"""
        summary_parts = ["主持人总结会议："]
        for expert, summary in expert_summaries.items():
            summary_parts.append(f"{summary}")
        summary_parts.append(f"整体结论：{final_summary}")
        return "\n".join(summary_parts)


class TechnicalExpert:
    def speak(self, question: str) -> str:
        return f"技术专家：从技术架构、实现难度、技术风险等方面分析。建议采用分层架构，预计开发周期3个月。"


class BusinessExpert:
    def speak(self, question: str) -> str:
        return f"商业专家：市场潜力巨大，预计ROI在200%以上。需要注意竞争对手反应和市场接受度。"


class ResearchExpert:
    def speak(self, question: str) -> str:
        return f"研究专家：该方向具有学术创新性，建议申请相关专利，可发表高水平论文2-3篇。"


class SummaryExpert:
    def summarize_expert(self, expert: str, opinion: str) -> str:
        """总结单个专家的发言"""
        summaries = {
            "技术专家": f"技术总结：{opinion}。重点评估了技术可行性和实施路径。",
            "商业专家": f"商业总结：{opinion}。明确了商业价值和风险控制。",
            "研究专家": f"研究总结：{opinion}。指出了创新点和学术价值。"
        }
        return summaries.get(expert, f"{expert}观点总结：{opinion}")

    def summarize_meeting(self, expert_summaries: Dict[str, str]) -> str:
        """总结整个会议"""
        return "会议整体总结：综合技术、商业、研究三个维度，项目具有较高可行性，建议分阶段实施。"


# 节点函数定义
def requirement_analysis_node(state: ConferenceState) -> ConferenceState:
    """需求分析节点"""
    analyst = RequirementAnalyst()
    state["requirement_analysis"] = analyst.analyze(state["user_question"])
    return state


def moderator_start_node(state: ConferenceState) -> ConferenceState:
    """主持人召开会议节点"""
    moderator = Moderator()
    state["expert_opinions"] = {}
    state["expert_summaries"] = {}
    state["discussion_round"] = 1
    state["current_expert"] = moderator.experts[0]
    return state


def expert_speak_node(state: ConferenceState) -> ConferenceState:
    """专家发言节点"""
    moderator = Moderator()
    current_expert = state["current_expert"]

    # 根据当前专家选择对应的专家类
    experts = {
        "技术专家": TechnicalExpert(),
        "商业专家": BusinessExpert(),
        "研究专家": ResearchExpert()
    }

    question = moderator.ask_question(state["requirement_analysis"], current_expert)
    opinion = experts[current_expert].speak(question)

    # 存储专家观点
    state["expert_opinions"][current_expert] = opinion
    return state


def summary_expert_node(state: ConferenceState) -> ConferenceState:
    """总结专家节点"""
    summary_expert = SummaryExpert()
    current_expert = state["current_expert"]

    # 总结当前专家发言
    if current_expert in state["expert_opinions"]:
        expert_summary = summary_expert.summarize_expert(
            current_expert, state["expert_opinions"][current_expert]
        )
        state["expert_summaries"][current_expert] = expert_summary

    return state


def moderator_judge_node(state: ConferenceState) -> ConferenceState:
    """主持人判断节点"""
    moderator = Moderator()

    # 判断是否所有专家都已发言
    current_expert_index = moderator.experts.index(state["current_expert"])
    if current_expert_index < len(moderator.experts) - 1:
        # 还有专家未发言，继续下一个专家
        state["current_expert"] = moderator.experts[current_expert_index + 1]
        state["should_continue"] = True
    else:
        # 所有专家已发言，判断是否需要新一轮讨论
        state["should_continue"] = moderator.judge_should_continue(
            state["expert_opinions"], state["discussion_round"]
        )
        if state["should_continue"]:
            state["discussion_round"] += 1
            state["current_expert"] = moderator.experts[0]  # 重新开始新一轮

    return state


def final_summary_node(state: ConferenceState) -> ConferenceState:
    """最终总结节点"""
    summary_expert = SummaryExpert()
    moderator = Moderator()

    # 总结专家做整体总结
    state["final_summary"] = summary_expert.summarize_meeting(state["expert_summaries"])

    # 主持人总结会议
    state["meeting_output"] = moderator.summarize_meeting(
        state["expert_summaries"], state["final_summary"]
    )

    return state


# 构建LangGraph
def create_conference_graph():
    """创建会议讨论图"""
    builder = StateGraph(ConferenceState)

    # 添加节点
    builder.add_node("requirement_analysis", requirement_analysis_node)
    builder.add_node("moderator_start", moderator_start_node)
    builder.add_node("expert_speak", expert_speak_node)
    builder.add_node("summary_expert", summary_expert_node)
    builder.add_node("moderator_judge", moderator_judge_node)
    builder.add_node("final_summary", final_summary_node)

    # 设置流程
    builder.set_entry_point("requirement_analysis")
    builder.add_edge("requirement_analysis", "moderator_start")
    builder.add_edge("moderator_start", "expert_speak")
    builder.add_edge("expert_speak", "summary_expert")
    builder.add_edge("summary_expert", "moderator_judge")

    # 条件边：判断是否继续讨论
    def should_continue(state: ConferenceState) -> str:
        return "continue" if state.get("should_continue", False) else "end"

    builder.add_conditional_edges(
        "moderator_judge",
        should_continue,
        {
            "continue": "expert_speak",  # 继续专家发言
            "end": "final_summary"  # 进入最终总结
        }
    )

    builder.add_edge("final_summary", END)

    return builder.compile()


# 使用示例
if __name__ == "__main__":
    # 创建会议图
    conference_graph = create_conference_graph()

    # 初始化状态
    initial_state = {
        "user_question": "如何开发一个智能会议辅助系统？",
        "requirement_analysis": "",
        "expert_opinions": {},
        "current_expert": "",
        "discussion_round": 0,
        "should_continue": True,
        "expert_summaries": {},
        "final_summary": "",
        "meeting_output": ""
    }

    # 执行会议流程
    result = conference_graph.invoke(initial_state)
    print("=== 会议输出 ===")
    print(result["meeting_output"])