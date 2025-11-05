# 图结构定义
from langgraph.graph import StateGraph, END
from graph_discussion.state import ConferenceState
from graph_discussion.agents.requirement_analyst import RequirementAnalyst
from graph_discussion.agents.moderator import Moderator
from graph_discussion.agents.summary_expert import SummaryExpert
from graph_discussion.agents.experts.tech_expert import TechExpert
from graph_discussion.agents.experts.business_expert import BusinessExpert
from graph_discussion.agents.experts.research_expert import ResearchExpert
from graph_discussion.utils.logger import get_logger

logger = get_logger("ConferenceGraph")

def create_conference_graph():
    """创建会议讨论图"""
    builder = StateGraph(ConferenceState)
    
    # 初始化智能体
    requirement_analyst = RequirementAnalyst()
    moderator = Moderator()
    summary_expert = SummaryExpert()
    
    # 专家注册
    experts = {
        "技术专家": TechExpert(),
        "商业专家": BusinessExpert(), 
        "研究专家": ResearchExpert()
    }
    
    # 添加节点
    def requirement_analysis_node(state: ConferenceState) -> ConferenceState:
        """需求分析节点"""
        result = requirement_analyst.process(state)
        return {**state, **result}
    
    def moderator_start_node(state: ConferenceState) -> ConferenceState:
        """主持人召开会议节点"""
        result = moderator.start_conference(state)
        return {**state, **result}
    
    def expert_speak_node(state: ConferenceState) -> ConferenceState:
        """专家发言节点"""
        current_question = state["current_question"]
        required_experts = state["required_experts"]
        previous_discussions = state.get("expert_discussions", [])
        
        # 当前轮次专家发言
        current_discussion = {}
        for expert_name in required_experts:
            if expert_name in experts:
                expert = experts[expert_name]
                # 获取当前专家之前的发言上下文（最近两轮）
                context = previous_discussions[-2:] if len(previous_discussions) >= 2 else previous_discussions
                response = expert.speak(current_question, context)
                current_discussion[expert_name] = response
            else:
                current_discussion[expert_name] = "该专家暂未注册"
        
        # 更新讨论记录
        expert_discussions = state.get("expert_discussions", [])
        expert_discussions.append(current_discussion)
        
        return {**state, "expert_discussions": expert_discussions}
    
    def summary_expert_node(state: ConferenceState) -> ConferenceState:
        """总结专家节点"""
        result = summary_expert.process(state)
        return {**state, **result}
    
    def moderator_judge_node(state: ConferenceState) -> ConferenceState:
        """主持人判断节点"""
        result = moderator.judge_discussion(state)
        return {**state, **result}
    
    def final_summary_node(state: ConferenceState) -> ConferenceState:
        """最终总结节点"""
        moderator_questions = state["moderator_questions"]
        expert_discussions = state["expert_discussions"]
        round_summaries = state["round_summaries"]
        
        logger.info("开始最终总结", "red")
        
        prompt = f"""请对整场会议进行最终总结，包括：
        
会议讨论过程：
主持人问题：{moderator_questions}
专家讨论记录：{expert_discussions}
各轮总结：{round_summaries}

请生成：
1. 整体会议总结
2. 各专家领域的落地方案

格式要求：
【会议总览】
[整体总结]

【技术落地方案】
[技术专家提出的具体实施方案]

【商业落地方案】 
[商业专家提出的商业计划]

【研究落地方案】
[研究专家提出的研究计划]"""
        
        final_summary = moderator.call_llm(prompt)
        
        # 提取各专家方案（简化处理，实际可以更精细）
        implementation_plans = {}
        if "【技术落地方案】" in final_summary:
            parts = final_summary.split("【技术落地方案】")
            if len(parts) > 1:
                tech_part = parts[1].split("【商业落地方案】")[0]
                implementation_plans["技术专家"] = tech_part.strip()
        
        if "【商业落地方案】" in final_summary:
            parts = final_summary.split("【商业落地方案】")
            if len(parts) > 1:
                business_part = parts[1].split("【研究落地方案】")[0]
                implementation_plans["商业专家"] = business_part.strip()
        
        if "【研究落地方案】" in final_summary:
            parts = final_summary.split("【研究落地方案】")
            if len(parts) > 1:
                research_part = parts[1]
                implementation_plans["研究专家"] = research_part.strip()
        
        logger.info("最终总结完成", "red")
        
        return {
            **state, 
            "final_summary": final_summary,
            "implementation_plans": implementation_plans
        }
    
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
            "end": "final_summary"       # 进入最终总结
        }
    )
    
    builder.add_edge("final_summary", END)
    
    return builder.compile()