# 商业专家
from .base_expert import BaseExpert
from typing import Dict, Any, List

class BusinessExpert(BaseExpert):
    """商业专家"""
    
    def __init__(self):
        super().__init__("BusinessExpert", "商业专家", "green", "商业")
        # 添加工具
        from ...tools.web_search import WebSearchTool
        from ...tools.rag_tool import RAGTool
        self.add_tool(WebSearchTool())
        self.add_tool(RAGTool())
    
    def speak(self, question: str, context: List[Dict]) -> str:
        """商业专家发言"""
        self.log(f"回答问题: {question}")
        
        context_str = self._build_context(context)
        
        # 使用工具获取信息
        tool_insights = []
        for tool in self.tools:
            try:
                insight = tool.execute(question, domain="商业")
                tool_insights.append(insight)
            except Exception as e:
                self.log(f"工具 {tool.name} 执行失败: {str(e)}")
        
        tools_info = "\n".join(tool_insights) if tool_insights else "暂无工具信息"
        
        prompt = f"""你是一名资深商业专家，负责从商业模式、市场前景、盈利能力、商业风险等角度进行分析。

当前讨论问题：{question}

历史讨论上下文：
{context_str}

工具获取的信息：
{tools_info}

请从商业角度进行专业分析，要求：
1. 分析商业模式和盈利点
2. 评估市场前景和竞争环境
3. 分析商业风险和机遇
4. 给出商业建议

请用专业且易懂的语言回答："""
        
        response = self.call_llm(prompt)
        self.log(f"发言完成: {response[:100]}...")
        return response
    
    def _build_context(self, context: List[Dict]) -> str:
        """构建上下文字符串"""
        if not context:
            return "无历史讨论"
        
        context_str = ""
        for i, discussion in enumerate(context[-3:]):
            context_str += f"第{i+1}轮讨论：\n"
            for expert_name, content in discussion.items():
                context_str += f"{expert_name}: {content}\n"
        
        return context_str