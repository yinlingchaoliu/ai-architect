# 研究专家
from .base_expert import BaseExpert
from typing import Dict, Any, List

from ...tools import tool_registry, WebSearchTool, RAGTool


class ResearchExpert(BaseExpert):
    """研究专家"""
    
    def __init__(self):
        super().__init__("ResearchExpert", "研究专家", "magenta", "研究")
        # 添加工具
        tool_registry.register(WebSearchTool())
        tool_registry.register(RAGTool())
        # 智能体注册工具名称
        self.register_tool("web_search")
        self.register_tool("rag_tool")
    
    def speak(self, question: str, context: List[Dict]) -> str:
        """研究专家发言"""
        self.log(f"回答问题: {question}")
        
        context_str = self._build_context(context)
        
        # 使用工具获取信息
        tool_insights = []

        # 使用网页搜索工具
        web_result = self.use_tool("web_search", question, domain="技术")
        if web_result:
            tool_insights.append(f"网页搜索: {web_result}")

        # 使用RAG工具
        rag_result = self.use_tool("rag_tool", question, domain="技术")
        if rag_result:
            tool_insights.append(f"知识库: {rag_result}")

        tools_info = "\n".join(tool_insights) if tool_insights else "暂无工具信息"
        
        prompt = f"""你是一名资深研究专家，负责从学术研究、创新性、理论支撑、研究趋势等角度进行分析。

当前讨论问题：{question}

历史讨论上下文：
{context_str}

工具获取的信息：
{tools_info}

请从研究角度进行专业分析，要求：
1. 分析相关研究现状和趋势
2. 评估创新性和学术价值
3. 提出研究方法和路径
4. 给出研究建议

请用专业且易懂的语言回答："""
        
        response = self.call_llm(prompt)
        self.log(f"发言完成: {response}...")
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