# src/utils/config.py
import toml
import os
from typing import Dict, Any


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: str = "config/config.toml"):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载TOML配置"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            return toml.load(f)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            value = value.get(k, {})
        return value if value != {} else default

    def get_llm_config(self) -> Dict[str, Any]:
        """获取LLM配置"""
        return self.config.get("llm", {})

    def get_agents_config(self) -> Dict[str, Any]:
        """获取智能体配置"""
        return self.config.get("agents", {})

    def get_tools_config(self) -> Dict[str, Any]:
        """获取工具配置"""
        return self.config.get("tools", {})