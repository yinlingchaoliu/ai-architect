# 主持人智能体
from .base_agent import BaseAgent
from typing import Dict, Any, List

class Moderator(BaseAgent):
    """主持人智能体"""
    
    def __init__(self):
        super().__init__("Moderator", "主持人", "yellow")
        
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """处理状态 - 实现基类抽象方法"""
        # 主持人智能体在图中通过特定方法调用，这里返回空状态更新
        return {}

    def start_conference(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """召开会议"""
        topics = state["discussion_topics"]
        experts = state["required_experts"]
        
        self.log(f"召开会议，主题: {topics}，参与专家: {experts}")
        
        prompt = f"""作为会议主持人，你需要：
1. 拆解会议主题为具体讨论要点
2. 制定第一轮讨论问题
3. 明确讨论规则和目标

会议主题：{', '.join(topics)}
参与专家：{', '.join(experts)}

请生成第一轮讨论问题和会议安排："""
        
        start_result = self.call_llm(prompt)
        self.log(f"会议召开完成，第一轮问题已生成")
        
        return {
            "moderator_questions": [start_result],
            "current_question": start_result,
            "current_round": 1,
            "should_continue": True
        }
    
    def ask_question(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """主持人提问"""
        current_round = state["current_round"]
        previous_discussions = state.get("expert_discussions", [])
        
        self.log(f"第{current_round}轮提问")
        
        if current_round == 1:
            question = state["current_question"]
        else:
            # 基于之前的讨论生成新问题
            prompt = f"""基于前{current_round-1}轮讨论，生成第{current_round}轮深入讨论问题。
前轮讨论摘要：{str(previous_discussions[-3:])}

请提出能够深化讨论、解决未决问题的新问题："""
            
            question = self.call_llm(prompt)
        
        return {
            "current_question": question,
            "moderator_questions": state["moderator_questions"] + [question]
        }
    
    def judge_discussion(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """判断是否结束会议"""
        current_round = state["current_round"]
        max_rounds = state.get("max_rounds", 3)
        discussions = state.get("expert_discussions", [])
        
        self.log(f"判断讨论状态，当前轮次: {current_round}/{max_rounds}")
        
        # 基于轮次和讨论质量判断
        should_continue = current_round < max_rounds
        
        if current_round >= max_rounds:
            self.log("已达到最大讨论轮次，结束会议")
            return {"should_continue": False}
        
        # 分析讨论质量
        prompt = f"""判断当前讨论是否充分，是否需要继续：
当前轮次：{current_round}/{max_rounds}
讨论记录：{str(discussions[-len(state['required_experts']):])}

请分析讨论是否深入、问题是否解决，给出是否继续的判断（只需回答"继续"或"结束"）："""
        
        judgment = self.call_llm(prompt)
        self.log(f"判断结果: {judgment}")
        
        # 解析判断结果
        if "继续" in judgment:
            should_continue = True
        elif "结束" in judgment:
            should_continue = False
        
        # 更新轮次
        if should_continue:
            current_round += 1
        
        return {
            "should_continue": should_continue,
            "current_round": current_round
        }