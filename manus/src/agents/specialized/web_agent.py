# src/agents/specialized/web_agent.py
from ..tool_call import ToolCallAgent

class WebAgent(ToolCallAgent):
    """网络操作智能体"""

    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self.available_tools = [
            "web_search",
            "file_operations"
        ]