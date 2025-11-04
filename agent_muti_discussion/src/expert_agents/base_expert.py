from abc import abstractmethod
from typing import Dict, Any, List

from ..core.base_agent import BaseAgent
from ..core.plugin_manager import PluginManager
from ..utils.logger import logger


class BaseExpertAgent(BaseAgent):
    """专家智能体基类"""

    def __init__(self, name: str, system_prompt: str, expertise: str, plugins: List[str] = None):
        super().__init__(name, system_prompt)
        self.expertise = expertise
        self.plugin_manager = PluginManager()
        self.available_plugins = plugins or []

    def process(self, input_data: str, context: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """处理输入，生成专家意见"""
        logger.info(f"专家 {self.name} 开始处理")

        # 构建专家提示
        expert_prompt = self._build_expert_prompt(input_data, context)

        expert_logic = self._build_expert_prompt(None,context)

        # 如果有可用插件，先使用插件获取信息
        plugin_results = self._use_plugins(input_data, context)

        # 生成专家意见
        opinion = self.generate_response(expert_prompt)

        result = {
            "expert_name": self.name,
            "expertise": self.expertise,
            "expert_logic": expert_logic,
            "opinion": opinion,
            "plugin_results": plugin_results,
            "context_used": context
        }

        logger.info(f"专家 {self.name} 处理完成")
        return result

    def _build_expert_prompt(self, input_data: str, context: Dict[str, Any] = None) -> str:
        """构建专家提示"""
        prompt = f"""
请以{self.expertise}的身份，对以下问题提供专业意见：

问题：{input_data}

"""
        if context:
            prompt += "讨论背景信息：\n"
            for key, value in context.items():
                prompt += f"{key}: {value}\n"

        prompt += f"\n请基于你的专业领域{self.expertise}，提供详细、专业的分析和建议。"

        return prompt

    def _use_plugins(self, input_data: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """使用插件获取信息"""
        results = {}
        for plugin_name in self.available_plugins:
            if plugin_name == "web_search":
                # 使用网页搜索插件
                search_result = self.plugin_manager.execute_plugin(
                    "web_search", "search", query=input_data, max_results=3
                )
                results["web_search"] = search_result
            elif plugin_name == "knowledge_base":
                # 使用知识库插件
                kb_result = self.plugin_manager.execute_plugin(
                    "knowledge_base", "query", question=input_data
                )
                results["knowledge_base"] = kb_result
            # 可以添加其他插件...

        return results