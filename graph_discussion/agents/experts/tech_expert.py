# 技术专家
from .base_expert import BaseExpert
from typing import Dict, Any, List

from ...tools.tool_registry import tool_registry
from ...tools.web_search import WebSearchTool
from ...tools.rag_tool import RAGTool

class TechExpert(BaseExpert):
    """技术专家"""
    
    def __init__(self):
        super().__init__("TechExpert", "技术专家", "blue", "技术")
        # 添加工具

        tool_registry.register(WebSearchTool())
        tool_registry.register(RAGTool())
        # 智能体注册工具名称
        self.register_tool("web_search")
        self.register_tool("rag_tool")
    
    def speak(self, question: str, context: List[Dict]) -> str:
        """技术专家发言"""
        self.log(f"回答问题: {question}")
        
        # 构建上下文
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
        
        prompt = f"""你是一名资深技术专家，负责从技术可行性、架构设计、实现方案等角度进行分析。

当前讨论问题：{question}

历史讨论上下文：
{context_str}

工具获取的信息：
{tools_info}

请从技术角度进行专业分析，要求：
1. 分析技术可行性
2. 提出技术实现方案
3. 评估技术风险和挑战
4. 给出技术建议

请用专业且易懂的语言回答："""
        
        response = self.call_llm(prompt)
        self.log(f"发言完成: {response}...")
        return response
    
    def _build_context(self, context: List[Dict]) -> str:
        """构建上下文字符串"""
        if not context:
            return "无历史讨论"
        
        context_str = ""
        for i, discussion in enumerate(context[-3:]):  # 最近3轮讨论
            context_str += f"第{i+1}轮讨论：\n"
            for expert_name, content in discussion.items():
                context_str += f"{expert_name}: {content}\n"
        
        return context_str