# 状态管理
from typing import TypedDict, List, Dict, Any, Optional
from typing_extensions import Annotated
import operator

class ConferenceState(TypedDict):
    """会议状态定义"""
    # 输入和基础信息
    user_query: str  # 用户原始提问
    current_round: int  # 当前讨论轮次
    
    # 需求分析结果
    requirement_analysis: str  # 需求分析结果
    discussion_topics: List[str]  # 讨论主题列表
    required_experts: List[str]  # 需要的专家类型
    
    # 讨论过程
    moderator_questions: List[str]  # 主持人提问记录
    expert_discussions: List[Dict[str, Any]]  # 专家讨论记录
    current_question: str  # 当前讨论问题
    
    # 总结和输出
    round_summaries: List[str]  # 每轮总结
    final_summary: str  # 最终总结
    implementation_plans: Dict[str, str]  # 各专家落地方案
    
    # 控制标志
    should_continue: bool  # 是否继续讨论
    max_rounds: int  # 最大轮次