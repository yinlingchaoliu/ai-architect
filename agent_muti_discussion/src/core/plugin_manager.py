from typing import Dict, Any, List, Optional
from ..plugins.web_search import WebSearchPlugin
from ..plugins.knowledge_base import KnowledgeBasePlugin
from ..plugins.reflection_tool import ReflectionToolPlugin
from ..utils.logger import logger


class PluginManager:
    """插件管理器"""

    def __init__(self):
        self.plugins: Dict[str, Any] = {}
        self._initialize_plugins()

    def _initialize_plugins(self):
        """初始化所有插件"""
        # 核心插件
        self.register_plugin("web_search", WebSearchPlugin())
        self.register_plugin("knowledge_base", KnowledgeBasePlugin())
        self.register_plugin("reflection_tool", ReflectionToolPlugin())

        logger.info("插件管理器初始化完成")

    def register_plugin(self, name: str, plugin_instance: Any):
        """注册插件"""
        self.plugins[name] = plugin_instance
        logger.info(f"注册插件: {name}")

    def get_plugin(self, name: str) -> Optional[Any]:
        """获取插件实例"""
        return self.plugins.get(name)

    def execute_plugin(self, plugin_name: str, action: str, **kwargs) -> Dict[str, Any]:
        """执行插件操作"""
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            return {"success": False, "error": f"插件 {plugin_name} 不存在"}

        try:
            if hasattr(plugin, action):
                method = getattr(plugin, action)
                result = method(**kwargs)
                logger.info(f"执行插件 {plugin_name}.{action} 成功")
                return result
            else:
                return {"success": False, "error": f"插件 {plugin_name} 没有方法 {action}"}
        except Exception as e:
            logger.error(f"执行插件 {plugin_name}.{action} 异常: {str(e)}")
            return {"success": False, "error": f"执行异常: {str(e)}"}

    def list_plugins(self) -> List[Dict[str, str]]:
        """列出所有可用插件"""
        plugins_info = []
        for name, plugin in self.plugins.items():
            plugins_info.append({
                "name": name,
                "description": getattr(plugin, 'description', 'No description'),
                "available_actions": self._get_plugin_actions(plugin)
            })
        return plugins_info

    def _get_plugin_actions(self, plugin: Any) -> List[str]:
        """获取插件可用操作"""
        actions = []
        for attr_name in dir(plugin):
            if not attr_name.startswith('_') and callable(getattr(plugin, attr_name)):
                actions.append(attr_name)
        return actions