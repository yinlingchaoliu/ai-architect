# multi_agent_system/core/plugin_manager.py
import importlib
import pkgutil
import inspect
import os
from typing import Dict, List, Type
from pathlib import Path
from ..agents.base_agent import BaseAgent


class AgentPluginManager:
    """Agent 插件管理器"""

    def __init__(self):
        self.plugin_directory = "agent_plugins"
        self.loaded_plugins: Dict[str, Type[BaseAgent]] = {}

    def discover_plugins(self, package_path: str):
        """发现并加载插件"""
        try:
            package = importlib.import_module(package_path)
            for _, name, is_pkg in pkgutil.iter_modules(package.__path__):
                if not is_pkg:
                    plugin_module = importlib.import_module(f"{package_path}.{name}")
                    self._load_plugins_from_module(plugin_module)
        except ImportError as e:
            print(f"⚠️  插件发现失败: {e}")

    def scan_plugin_directory(self, directory: str):
        """扫描插件目录"""
        if not os.path.exists(directory):
            print(f"⚠️  插件目录不存在: {directory}")
            return

        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('_agent.py') or file.endswith('_plugin.py'):
                    file_path = os.path.join(root, file)
                    try:
                        # 动态导入插件文件
                        spec = importlib.util.spec_from_file_location(file[:-3], file_path)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        self._load_plugins_from_module(module)
                    except Exception as e:
                        print(f"⚠️  加载插件文件失败 {file}: {e}")

    def _load_plugins_from_module(self, module):
        """从模块加载插件"""
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and
                    issubclass(obj, BaseAgent) and
                    obj != BaseAgent):
                self.loaded_plugins[name] = obj
                print(f"🔌 加载插件: {name}")

    def create_agent_instance(self, plugin_name: str, *args, **kwargs) -> BaseAgent:
        """创建插件实例"""
        if plugin_name not in self.loaded_plugins:
            raise ValueError(f"插件 '{plugin_name}' 未找到")

        plugin_class = self.loaded_plugins[plugin_name]
        return plugin_class(*args, **kwargs)

    def get_available_plugins(self) -> List[str]:
        """获取可用插件列表"""
        return list(self.loaded_plugins.keys())