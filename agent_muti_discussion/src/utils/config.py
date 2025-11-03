import yaml
import os
from typing import Dict, Any, Optional


class Config:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), '../config/agent_config.yaml')
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            print(f"配置文件未找到: {self.config_path}")
            return self._get_default_config()
        except Exception as e:
            print(f"加载配置文件错误: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'discussion': {
                'max_rounds': 8,
                'consensus_threshold': 0.75,
                'enable_reflection': True
            },
            'agents': {
                'moderator': {
                    'reflection_sensitivity': 0.7
                }
            },
            'plugins': {
                'web_search': {
                    'max_results': 5
                }
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value


# 全局配置实例
global_config = Config()


class ConfigLoader:
    """配置加载器类 - 为main.py提供配置管理功能"""
    def __init__(self, config_path: Optional[str] = None):
        self.config = Config(config_path)
        # 添加插件配置获取方法
        self._setup_plugin_configs()
    
    def _setup_plugin_configs(self):
        """初始化默认的插件配置"""
        self._plugin_configs = {
            'web_search': {'max_results': 5},
            'knowledge_base': {'db_path': None},
            'reflection_tool': {'enabled': True}
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)
    
    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """获取插件配置"""
        # 尝试从配置文件获取
        config_value = self.config.get(f'plugins.{plugin_name}', {})
        # 如果没有，返回默认配置
        return {**self._plugin_configs.get(plugin_name, {}), **config_value}
    
    def set_plugin_config(self, plugin_name: str, config: Dict[str, Any]):
        """设置插件配置"""
        if plugin_name not in self._plugin_configs:
            self._plugin_configs[plugin_name] = {}
        self._plugin_configs[plugin_name].update(config)
        self.config.set(f'plugins.{plugin_name}', self._plugin_configs[plugin_name])