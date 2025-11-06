# src/main.py
import asyncio
import logging
from typing import Dict, Any
from .graph.workflow import workflow
from .utils.config import ConfigManager
from .llm.manager import LLMManager
from .agents.agent_pool import AgentPool
from .tools.tool_registry import tool_registry

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultiAgentSystem:
    """多智能体系统主类"""

    def __init__(self, config_path: str = "config/config.toml"):
        self.config_manager = ConfigManager(config_path)
        self.llm_manager = LLMManager(self.config_manager.get_llm_config())
        self.agent_pool = AgentPool(self.config_manager.get_agents_config())
        self.workflow = workflow

    async def initialize(self):
        """初始化系统"""
        logger.info("Initializing Multi-Agent System...")

        # 注册工具
        await self._register_tools()

        # 设置LLM管理器到智能体池
        self.agent_pool.llm_manager = self.llm_manager

        # 初始化智能体池
        await self.agent_pool.initialize()

        logger.info("Multi-Agent System initialized successfully")

    async def _register_tools(self):
        """注册工具"""
        from .tools.python_tool import PythonExecuteTool
        from .tools.file_tool import FileTool
        from .tools.search_tool import SearchTool

        # 注册内置工具
        tool_registry.register_tool(PythonExecuteTool())
        tool_registry.register_tool(FileTool())
        tool_registry.register_tool(SearchTool())

        logger.info(f"Registered {len(tool_registry.list_tools())} tools")

    async def run(self, task: str) -> Dict[str, Any]:
        """运行任务"""
        logger.info(f"Running task: {task}")

        # 准备初始状态
        initial_state = {
            "messages": [],
            "current_task": task,
            "subtasks": [],
            "current_agent": "",
            "tool_results": [],
            "execution_path": [],
            "is_complete": False,
            "plan": None
        }

        # 执行工作流
        final_state = await self.workflow.ainvoke(initial_state)

        logger.info(f"Task completed. Execution path: {final_state['execution_path']}")

        return {
            "result": final_state["tool_results"],
            "execution_path": final_state["execution_path"],
            "plan": final_state.get("plan"),
            "usage": self.llm_manager.get_total_usage()
        }


# 命令行入口
async def main():
    """主函数"""
    system = MultiAgentSystem()
    await system.initialize()

    print("Multi-Agent System Ready!")
    print("Enter your task (or 'quit' to exit):")

    while True:
        try:
            task = input("> ").strip()
            if task.lower() in ['quit', 'exit', 'q']:
                break

            if task:
                result = await system.run(task)
                print(f"Result: {result}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
