# 需求分析智能体
from .base_agent import BaseAgent
from typing import Dict, Any

class RequirementAnalyst(BaseAgent):
    """需求分析智能体"""
    
    def __init__(self):
        super().__init__("RequirementAnalyst", "需求分析师", "green")
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """分析用户需求"""
        user_query = state["user_query"]
        
        self.log(f"开始分析用户需求: {user_query}")
        
        prompt = f"""作为需求分析师，请分析以下用户提问，确定：
1. 核心需求和目标
2. 需要讨论的关键主题
3. 需要哪些领域的专家参与

用户提问：{user_query}

请按以下格式回复：
【需求分析】
[详细的需求分析]

【讨论主题】
1. 主题1
2. 主题2
3. 主题3

【所需专家】
- 技术专家
- 商业专家
- 研究专家

请确保分析全面准确："""
        
        analysis_result = self.call_llm(prompt)
        self.log(f"需求分析完成: {analysis_result[:100]}...")
        
        # 解析结果
        topics = self._extract_topics(analysis_result)
        experts = self._extract_experts(analysis_result)
        
        return {
            "requirement_analysis": analysis_result,
            "discussion_topics": topics,
            "required_experts": experts
        }
    
    def _extract_topics(self, analysis: str) -> list:
        """提取讨论主题"""
        # 简化提取逻辑，实际可以更复杂
        lines = analysis.split('\n')
        topics = []
        in_topics = False
        
        for line in lines:
            if "【讨论主题】" in line or "讨论主题" in line:
                in_topics = True
                continue
            if in_topics and ("【" in line or "---" in line):
                break
            if in_topics and line.strip() and any(c.isdigit() for c in line):
                topic = line.split('.', 1)[-1].strip()
                if topic:
                    topics.append(topic)
        
        return topics if topics else ["技术可行性", "商业价值", "研究方向"]
    
    def _extract_experts(self, analysis: str) -> list:
        """提取所需专家"""
        experts = []
        if "技术" in analysis:
            experts.append("技术专家")
        if "商业" in analysis or "市场" in analysis:
            experts.append("商业专家") 
        if "研究" in analysis or "学术" in analysis:
            experts.append("研究专家")
        
        return experts if experts else ["技术专家", "商业专家", "研究专家"]