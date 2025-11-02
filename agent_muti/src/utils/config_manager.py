# multi_agent_system/utils/config_manager.py
import os
import yaml
import json
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from enum import Enum


class ConfigSource(Enum):
    """配置来源枚举"""
    FILE = "file"
    ENVIRONMENT = "environment"
    DATABASE = "database"
    DEFAULT = "default"


@dataclass
class ConfigValue:
    """配置值数据结构"""
    value: Any
    source: ConfigSource
    last_updated: float
    description: str = ""
    validation_rules: List[str] = None


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: str = "config.yaml", env_prefix: str = "MAAS_"):
        self.config_path = Path(config_path)
        self.env_prefix = env_prefix
        self.config_data: Dict[str, ConfigValue] = {}
        self.config_schema: Dict[str, Any] = {}
        self._listeners: Dict[str, List[Callable]] = {}

        # 设置日志
        self.logger = self._setup_logger()

        # 加载配置
        self._load_config()

    def _setup_logger(self) -> logging.Logger:
        """设置日志器"""
        logger = logging.getLogger("ConfigManager")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

        return logger

    def _load_config(self):
        """加载配置"""
        # 1. 加载默认配置
        self._load_default_config()

        # 2. 从文件加载配置
        if self.config_path.exists():
            self._load_from_file()
        else:
            self.logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")

        # 3. 从环境变量加载配置
        self._load_from_environment()

        # 4. 验证配置
        self._validate_config()

        self.logger.info("✅ 配置加载完成")

    def _load_default_config(self):
        """加载默认配置"""
        default_config = {
            "system": {
                "name": "多Agent智能系统",
                "version": "2.0.0",
                "debug": False,
                "log_level": "INFO",
                "max_iterations": 5,
                "enable_monitoring": True,
                "api_timeout": 30
            },
            "agents": {
                "coordinator": {
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.1,
                    "max_tokens": 2000,
                    "enable_memory": True,
                    "memory_size": 10
                },
                "weather": {
                    "enabled": True,
                    "cities": ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安"],
                    "cache_duration": 3600
                },
                "transport": {
                    "enabled": True,
                    "default_from_city": "北京",
                    "transport_types": ["飞机", "高铁", "自驾", "大巴"]
                },
                "budget": {
                    "enabled": True,
                    "currency": "CNY",
                    "default_days": 3,
                    "default_travelers": 2
                }
            },
            "performance": {
                "enable_metrics": True,
                "metrics_port": 9090,
                "collect_interval": 30,
                "enable_tracing": False
            },
            "message_bus": {
                "max_queue_size": 1000,
                "enable_health_monitor": True,
                "health_check_interval": 30
            },
            "security": {
                "enable_encryption": False,
                "api_key_rotation_days": 30,
                "max_request_size": "10MB"
            },
            "plugins": {
                "auto_discover": True,
                "plugin_paths": ["./plugins", "./agent_plugins"],
                "hot_reload": False
            }
        }

        # 转换为ConfigValue对象
        self._flatten_and_convert_config(default_config, ConfigSource.DEFAULT)

    def _flatten_and_convert_config(self, config_dict: Dict, source: ConfigSource, prefix: str = ""):
        """展平配置字典并转换为ConfigValue对象"""
        for key, value in config_dict.items():
            full_key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                self._flatten_and_convert_config(value, source, full_key)
            else:
                self.config_data[full_key] = ConfigValue(
                    value=value,
                    source=source,
                    last_updated=os.path.getctime(__file__),
                    description=f"默认配置: {full_key}"
                )

    def _load_from_file(self):
        """从文件加载配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                if self.config_path.suffix.lower() in ['.yaml', '.yml']:
                    file_config = yaml.safe_load(file)
                elif self.config_path.suffix.lower() == '.json':
                    file_config = json.load(file)
                else:
                    self.logger.error(f"不支持的配置文件格式: {self.config_path.suffix}")
                    return

            # 更新配置
            self._update_config_from_dict(file_config, ConfigSource.FILE)
            self.logger.info(f"✅ 从文件加载配置: {self.config_path}")

        except Exception as e:
            self.logger.error(f"❌ 加载配置文件失败: {e}")

    def _load_from_environment(self):
        """从环境变量加载配置"""
        for env_key, env_value in os.environ.items():
            if env_key.startswith(self.env_prefix):
                # 转换环境变量名为配置键
                config_key = env_key[len(self.env_prefix):].lower()
                config_key = config_key.replace('__', '.')  # 双下划线转换为点

                # 转换值类型
                converted_value = self._convert_value_type(env_value)

                # 更新配置
                self.config_data[config_key] = ConfigValue(
                    value=converted_value,
                    source=ConfigSource.ENVIRONMENT,
                    last_updated=os.path.getctime(__file__),
                    description=f"环境变量: {env_key}"
                )

    def _convert_value_type(self, value: str) -> Any:
        """转换值类型"""
        if value.lower() in ['true', 'yes', 'on']:
            return True
        elif value.lower() in ['false', 'no', 'off']:
            return False
        elif value.isdigit():
            return int(value)
        elif self._is_float(value):
            return float(value)
        elif value.startswith('[') and value.endswith(']'):
            # 尝试解析为列表
            try:
                return json.loads(value.replace("'", '"'))
            except:
                return value
        elif value.startswith('{') and value.endswith('}'):
            # 尝试解析为字典
            try:
                return json.loads(value)
            except:
                return value
        else:
            return value

    def _is_float(self, value: str) -> bool:
        """检查字符串是否可以转换为浮点数"""
        try:
            float(value)
            return True
        except ValueError:
            return False

    def _update_config_from_dict(self, config_dict: Dict, source: ConfigSource, prefix: str = ""):
        """从字典更新配置"""
        for key, value in config_dict.items():
            full_key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                self._update_config_from_dict(value, source, full_key)
            else:
                if full_key in self.config_data:
                    # 更新现有配置
                    old_value = self.config_data[full_key].value
                    self.config_data[full_key].value = value
                    self.config_data[full_key].source = source
                    self.config_data[full_key].last_updated = os.path.getctime(__file__)

                    # 通知监听器
                    self._notify_listeners(full_key, old_value, value)
                else:
                    # 创建新配置
                    self.config_data[full_key] = ConfigValue(
                        value=value,
                        source=source,
                        last_updated=os.path.getctime(__file__),
                        description=f"文件配置: {full_key}"
                    )

    def _validate_config(self):
        """验证配置"""
        validation_errors = []

        # 必需配置项检查
        required_keys = [
            "system.name",
            "system.version",
            "agents.coordinator.model"
        ]

        for key in required_keys:
            if key not in self.config_data:
                validation_errors.append(f"缺少必需配置项: {key}")

        # 类型验证
        type_checks = [
            ("system.max_iterations", int),
            ("system.debug", bool),
            ("agents.coordinator.temperature", float)
        ]

        for key, expected_type in type_checks:
            if key in self.config_data:
                value = self.config_data[key].value
                if not isinstance(value, expected_type):
                    validation_errors.append(
                        f"配置项 {key} 类型错误: 期望 {expected_type.__name__}, 实际 {type(value).__name__}")

        # 范围验证
        if "agents.coordinator.temperature" in self.config_data:
            temp = self.config_data["agents.coordinator.temperature"].value
            if not (0 <= temp <= 1):
                validation_errors.append("agents.coordinator.temperature 必须在 0 到 1 之间")

        if validation_errors:
            self.logger.warning(f"配置验证警告: {validation_errors}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        if key in self.config_data:
            return self.config_data[key].value
        else:
            return default

    def get_config_value(self, key: str) -> Optional[ConfigValue]:
        """获取完整的配置值对象"""
        return self.config_data.get(key)

    def set(self, key: str, value: Any, description: str = ""):
        """设置配置值"""
        old_value = self.config_data[key].value if key in self.config_data else None

        self.config_data[key] = ConfigValue(
            value=value,
            source=ConfigSource.DEFAULT,
            last_updated=os.path.getctime(__file__),
            description=description
        )

        # 通知监听器
        if old_value != value:
            self._notify_listeners(key, old_value, value)

        self.logger.info(f"📝 更新配置: {key} = {value}")

    def get_nested(self, base_key: str) -> Dict[str, Any]:
        """获取嵌套配置"""
        result = {}
        prefix = f"{base_key}."

        for key, config_value in self.config_data.items():
            if key.startswith(prefix):
                sub_key = key[len(prefix):]
                result[sub_key] = config_value.value

        return result

    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """获取Agent配置"""
        return self.get_nested(f"agents.{agent_name}")

    def get_system_config(self) -> Dict[str, Any]:
        """获取系统配置"""
        return self.get_nested("system")

    def save_to_file(self, file_path: str = None):
        """保存配置到文件"""
        if not file_path:
            file_path = self.config_path

        try:
            # 转换为嵌套字典
            nested_config = self._to_nested_dict()

            with open(file_path, 'w', encoding='utf-8') as file:
                if file_path.endswith(('.yaml', '.yml')):
                    yaml.dump(nested_config, file, allow_unicode=True, indent=2)
                elif file_path.endswith('.json'):
                    json.dump(nested_config, file, ensure_ascii=False, indent=2)
                else:
                    self.logger.error(f"不支持的配置文件格式: {file_path}")
                    return

            self.logger.info(f"💾 配置已保存到文件: {file_path}")

        except Exception as e:
            self.logger.error(f"❌ 保存配置到文件失败: {e}")

    def _to_nested_dict(self) -> Dict[str, Any]:
        """转换为嵌套字典"""
        result = {}

        for key, config_value in self.config_data.items():
            keys = key.split('.')
            current = result

            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]

            current[keys[-1]] = config_value.value

        return result

    def add_listener(self, key: str, callback: Callable):
        """添加配置变更监听器"""
        if key not in self._listeners:
            self._listeners[key] = []

        self._listeners[key].append(callback)
        self.logger.debug(f"添加配置监听器: {key}")

    def remove_listener(self, key: str, callback: Callable):
        """移除配置变更监听器"""
        if key in self._listeners and callback in self._listeners[key]:
            self._listeners[key].remove(callback)
            self.logger.debug(f"移除配置监听器: {key}")

    def _notify_listeners(self, key: str, old_value: Any, new_value: Any):
        """通知监听器"""
        if key in self._listeners:
            for callback in self._listeners[key]:
                try:
                    callback(key, old_value, new_value)
                except Exception as e:
                    self.logger.error(f"配置监听器执行失败: {e}")

    def reload(self):
        """重新加载配置"""
        self.logger.info("🔄 重新加载配置...")
        old_config = self.config_data.copy()
        self.config_data.clear()
        self._load_config()

        # 检查变更并通知监听器
        for key, new_config_value in self.config_data.items():
            if key in old_config:
                old_value = old_config[key].value
                new_value = new_config_value.value
                if old_value != new_value:
                    self._notify_listeners(key, old_value, new_value)

    def list_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """列出所有配置"""
        result = {}
        for key, config_value in self.config_data.items():
            result[key] = {
                "value": config_value.value,
                "source": config_value.source.value,
                "last_updated": config_value.last_updated,
                "description": config_value.description
            }
        return result

    def validate_schema(self, schema: Dict[str, Any]) -> List[str]:
        """根据模式验证配置"""
        errors = []
        # 这里可以实现更复杂的模式验证逻辑
        return errors


# 单例实例
_config_instance: Optional[ConfigManager] = None


def get_config_manager(config_path: str = "config.yaml") -> ConfigManager:
    """获取配置管理器单例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager(config_path)
    return _config_instance


# 便捷函数
def get_config(key: str, default: Any = None) -> Any:
    """便捷函数：获取配置值"""
    return get_config_manager().get(key, default)


def get_agent_config(agent_name: str) -> Dict[str, Any]:
    """便捷函数：获取Agent配置"""
    return get_config_manager().get_agent_config(agent_name)


def get_system_config() -> Dict[str, Any]:
    """便捷函数：获取系统配置"""
    return get_config_manager().get_system_config()