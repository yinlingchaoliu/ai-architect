# src/utils/config.py
from copy import deepcopy
from pathlib import Path
from dotenv import load_dotenv
import toml
import os
from typing import Dict, Any


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: str = "config/config.toml"):
        load_dotenv(Path(__file__).resolve().parents[3] / ".env.local")
        load_dotenv(Path(__file__).resolve().parents[3] / ".env")
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
        config = deepcopy(self.config.get("llm", {}))
        models = config.get("models", {})
        entries = [models] if "model_name" in models else models.values()
        for model in entries:
            if model.get("provider") == "openai":
                for env_name, field in [("OPENAI_MODEL", "model_name"),
                                        ("OPENAI_API_KEY", "api_key"),
                                        ("OPENAI_BASE_URL", "base_url")]:
                    if os.getenv(env_name):
                        model[field] = os.environ[env_name]
        return config

    def get_agents_config(self) -> Dict[str, Any]:
        """获取智能体配置"""
        return self.config.get("agents", {})

    def get_tools_config(self) -> Dict[str, Any]:
        """获取工具配置"""
        return self.config.get("tools", {})