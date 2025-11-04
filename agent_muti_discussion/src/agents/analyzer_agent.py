from typing import Dict, Any
# from langchain.schema import HumanMessage

from ..core.base_agent import BaseAgent
from ..utils.logger import logger, Logger


class AnalyzerAgent(BaseAgent):
    """分析智能体"""

    def __init__(self):
        system_prompt = """你是一个专业的需求分析师，擅长分析和完善用户需求。

你的任务：
1. 仔细分析用户提出的问题，理解其核心需求
2. 完善和澄清需求，使其更加明确和具体
3. 描述任务的基本需求和背景
4. 将完善后的问题提交给会议主持人

请确保你的分析：
- 准确理解用户意图
- 识别潜在的需求和约束
- 为后续专家讨论提供清晰的基础

请用中文回复。"""

        super().__init__("需求分析师", system_prompt)

    def process(self, input_data: str, **kwargs) -> Dict[str, Any]:
        """处理用户输入，进行分析"""
        logger.info(f"分析智能体开始处理: {input_data}")

        # 生成分析提示
        analysis_prompt = f"""
请对以下用户问题进行需求分析：

用户问题：{input_data}

请从以下方面进行分析：
1. 核心需求：用户真正想要什么？
2. 背景信息：问题发生的背景是什么？
3. 约束条件：有哪些限制或要求？
4. 完善建议：如何使需求更清晰？

请输出完善后的需求描述：
"""
        logger.info(f"{self.name}思考 {analysis_prompt}", color=Logger.RED)
        # 调用大模型进行分析
        analyzed_requirement = self.generate_response(analysis_prompt)
        logger.info(f"{self.name}发言 \n{analyzed_requirement}", color=Logger.RED)

        result = {
            "original_question": input_data,
            "analyzed_requirement": analyzed_requirement,
            "status": "completed"
        }

        logger.info("分析智能体处理完成")
        return result