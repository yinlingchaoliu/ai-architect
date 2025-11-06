# src/agents/specialized/data_agent.py
from ..tool_call import ToolCallAgent


class DataAnalysisAgent(ToolCallAgent):
    """数据分析智能体"""

    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        # 专门为数据分析配置的工具
        self.available_tools = [
            "execute_python",
            "file_operations",
            # 可以添加数据分析专用工具
        ]
