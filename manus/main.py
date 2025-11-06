# src/main.py
import asyncio
import logging
from typing import Dict, Any

# from agents import AgentPool
from src.agents import AgentPool
from src.graph.workflow import workflow
from src.utils.config import ConfigManager
from src.llm.manager import LLMManager
from src.tools.tool_registry import tool_registry

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
        
        # 设置全局agent_pool引用到plan_node和execute_node
        from src.graph.nodes.plan_node import set_agent_pool as set_plan_node_agent_pool
        from src.graph.nodes.execute_node import set_agent_pool as set_execute_node_agent_pool
        set_plan_node_agent_pool(self.agent_pool)
        set_execute_node_agent_pool(self.agent_pool)

        logger.info("Multi-Agent System initialized successfully")

    async def _register_tools(self):
        """注册工具"""
        from src.tools.python_tool import PythonExecuteTool
        from src.tools.file_tool import FileTool
        from src.tools.search_tool import SearchTool

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
                
                # 提取并展示缺失的信息
                print("\n=== 任务执行结果 ===")
                
                # 检查并显示规划阶段识别的缺失资源
                if result.get('plan') and result['plan'].get('missing_resources'):
                    missing_resources = result['plan']['missing_resources']
                    
                    if any(missing_resources.values()):
                        print("\n发现缺失的资源:")
                        
                        if missing_resources.get('agents'):
                            print(f"  - 智能体: {', '.join(missing_resources['agents'])}")
                        
                        if missing_resources.get('tools'):
                            print(f"  - 工具: {', '.join(missing_resources['tools'])}")
                        
                        if missing_resources.get('errors'):
                            print(f"  - 错误: {', '.join(missing_resources['errors'])}")
                
                # 检查并显示执行过程中的降级信息
                fallback_info_found = False
                if result.get('result'):
                    for tool_result in result['result']:
                        if isinstance(tool_result, dict):
                            # 检查是否有缺失信息
                            if tool_result.get('missing_info'):
                                missing_info = tool_result['missing_info']
                                if not fallback_info_found:
                                    print("\n执行过程中的降级信息:")
                                    fallback_info_found = True
                                
                                print(f"  - 原始任务: {missing_info.get('original_task', 'N/A')}")
                                print(f"    目标智能体: {missing_info.get('target_agent', 'N/A')}")
                                print(f"    降级智能体: {missing_info.get('fallback_agent', 'N/A')}")
                                print(f"    错误类型: {missing_info.get('error_type', 'N/A')}")
                                print(f"    错误信息: {missing_info.get('message', 'N/A')}")
                
                # 如果有子任务，检查子任务中的缺失信息
                if result.get('plan') and result['plan'].get('subtasks'):
                    for subtask in result['plan']['subtasks']:
                        if subtask.get('missing_info'):
                            if not fallback_info_found:
                                print("\n执行过程中的降级信息:")
                                fallback_info_found = True
                            
                            missing_info = subtask['missing_info']
                            print(f"  - 子任务: {subtask.get('description', 'N/A')}")
                            print(f"    错误类型: {missing_info.get('error_type', 'N/A')}")
                            print(f"    错误信息: {missing_info.get('message', 'N/A')}")
                
                # 如果没有发现任何缺失信息，显示任务执行成功
                if not (result.get('plan') and any(result['plan']['missing_resources'].values())) and not fallback_info_found:
                    print("\n任务执行成功，没有发现缺失的资源或降级情况。")
                
                # 提供完整结果的简要总结
                print("\n=== 结果总结 ===")
                if result.get('plan'):
                    subtasks = result['plan'].get('subtasks', [])
                    print(f"执行了 {len(subtasks)} 个子任务")
                    completed_count = sum(1 for t in subtasks if t.get('completed', False))
                    print(f"成功完成: {completed_count}")
                    
                # 建议补充缺失的资源
                if result.get('plan') and result['plan'].get('missing_resources'):
                    missing_resources = result['plan']['missing_resources']
                    if missing_resources.get('agents'):
                        print(f"\n建议补充以下智能体: {', '.join(missing_resources['agents'])}")
                    if missing_resources.get('tools'):
                        print(f"建议补充以下工具: {', '.join(missing_resources['tools'])}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
