from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BasePlugin(ABC):
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = self.__class__.__name__

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """执行插件功能"""
        pass

    def validate_config(self) -> bool:
        """验证配置"""
        return True