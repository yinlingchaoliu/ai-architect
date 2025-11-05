# 基础工具类
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from ..utils.logger import get_logger


class BaseTool(ABC):
    """基础工具抽象类"""

    def __init__(self, name: str, description: str = ""):
        self._name = name
        self._description = description
        self.logger = get_logger(f"Tool-{name}")

    @abstractmethod
    def execute(self, query: str, **kwargs) -> Any:
        """
        执行工具的主要方法

        Args:
            query: 查询内容
            **kwargs: 其他参数

        Returns:
            工具执行结果
        """
        pass

    @property
    def name(self) -> str:
        """工具名称"""
        return self._name

    @property
    def description(self) -> str:
        """工具描述"""
        return self._description

    def validate_input(self, query: str) -> bool:
        """
        验证输入是否有效

        Args:
            query: 查询内容

        Returns:
            是否有效
        """
        if not query or not isinstance(query, str):
            self.logger.warning("输入查询不能为空", "red")
            return False
        return True

    def pre_process(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        预处理输入参数

        Args:
            query: 查询内容
            **kwargs: 其他参数

        Returns:
            处理后的参数字典
        """
        processed = {
            "query": query.strip(),
            "domain": kwargs.get("domain", ""),
            "max_results": kwargs.get("max_results", 5),
            "timeout": kwargs.get("timeout", 30)
        }
        return processed

    def post_process(self, result: Any, **kwargs) -> Any:
        """
        后处理结果

        Args:
            result: 原始结果
            **kwargs: 其他参数

        Returns:
            处理后的结果
        """
        if isinstance(result, str):
            # 清理结果字符串
            result = result.strip()
            if not result:
                return "未找到相关信息"

        return result

    def __call__(self, query: str, **kwargs) -> Any:
        """
        使工具可调用

        Args:
            query: 查询内容
            **kwargs: 其他参数

        Returns:
            工具执行结果
        """
        # 输入验证
        if not self.validate_input(query):
            return "输入无效"

        try:
            # 预处理
            processed_kwargs = self.pre_process(query, **kwargs)

            # 执行工具
            self.logger.info(f"执行工具: {self.name}, 查询: xxx", "yellow")
            raw_result = self.execute(**processed_kwargs)

            # 后处理
            final_result = self.post_process(raw_result, **kwargs)

            self.logger.info(f"工具 {self.name} 执行完成", "yellow")
            return final_result

        except Exception as e:
            error_msg = f"工具 {self.name} 执行出错: {str(e)}"
            self.logger.error(error_msg, "red")
            return error_msg

    def get_usage_info(self) -> Dict[str, Any]:
        """
        获取工具使用信息

        Returns:
            工具信息字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "query": "查询字符串",
                "domain": "领域限定（可选）",
                "max_results": "最大结果数（可选）",
                "timeout": "超时时间（可选）"
            }
        }

