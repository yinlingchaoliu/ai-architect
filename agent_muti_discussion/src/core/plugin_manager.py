from typing import Optional, Any


class PluginManager:
    def __init__(self):
        self.available_plugins = {}
        self.loaded_plugins = {}

    def register_plugin(self, plugin_name: str, plugin_class):
        """注册插件"""
        self.available_plugins[plugin_name] = plugin_class

    def load_plugin(self, plugin_name: str, config: Dict = None) -> Any:
        """加载插件实例"""
        if plugin_name in self.available_plugins:
            plugin_instance = self.available_plugins[plugin_name](config or {})
            self.loaded_plugins[plugin_name] = plugin_instance
            return plugin_instance
        return None

    def unload_plugin(self, plugin_name: str):
        """卸载插件"""
        self.loaded_plugins.pop(plugin_name, None)

    def get_plugin(self, plugin_name: str) -> Optional[Any]:
        """获取插件实例"""
        return self.loaded_plugins.get(plugin_name)