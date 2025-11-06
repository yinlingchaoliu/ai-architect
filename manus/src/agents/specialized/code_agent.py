# src/agents/specialized/code_agent.py
from ..tool_call import ToolCallAgent

class CodeAgent(ToolCallAgent):
    """代码执行智能体"""

    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self.available_tools = [
            "execute_python",
            "file_operations"
        ]
