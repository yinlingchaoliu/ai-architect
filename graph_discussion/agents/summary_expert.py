# 总结专家智能体
from .base_agent import BaseAgent
from typing import Dict, Any, List

class SummaryExpert(BaseAgent):
    """总结专家智能体"""
    
    def __init__(self):
        super().__init__("SummaryExpert", "总结专家", "cyan")
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """总结当前轮次讨论"""
        current_round = state["current_round"]
        discussions = state.get("expert_discussions", [])
        
        self.log(f"总结第{current_round}轮讨论")
        
        # 获取当前轮次的讨论（最近一轮）
        current_discussion = discussions[-1] if discussions else {}
        
        prompt = f"""请对第{current_round}轮讨论进行总结，提取关键观点和共识。

讨论记录：
{current_discussion}

请按以下格式总结：
【本轮总结】
- 主要观点
- 达成的共识  
- 存在的分歧
- 下一步建议

确保总结简洁明了："""
        
        summary = self.call_llm(prompt)
        self.log(f"本轮总结完成: {summary[:100]}...")
        
        # 更新轮次总结
        round_summaries = state.get("round_summaries", [])
        round_summaries.append(summary)
        
        return {
            "round_summaries": round_summaries
        }