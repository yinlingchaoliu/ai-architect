from typing import Optional, Any, Dict


class PluginManager:
    """插件管理器 - 负责插件的注册和加载"""
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
    
    async def close_all_plugins(self):
        """关闭所有已加载的插件"""
        for plugin_name, plugin in self.loaded_plugins.items():
            # 尝试调用插件的close方法，如果存在的话
            if hasattr(plugin, 'close') and callable(plugin.close):
                try:
                    # 检查是否为异步方法
                    if hasattr(plugin.close, '__await__'):
                        await plugin.close()
                    else:
                        plugin.close()
                except Exception as e:
                    print(f"关闭插件 {plugin_name} 时出错: {e}")
        # 清空已加载的插件
        self.loaded_plugins.clear()