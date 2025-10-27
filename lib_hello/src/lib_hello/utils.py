import time
from typing import Any, Dict

def format_message(message: str, **kwargs) -> str:
    """格式化消息"""
    if kwargs:
        return message.format(**kwargs)
    return message

def timestamp() -> int:
    """获取当前时间戳"""
    return int(time.time())

def validate_name(name: str) -> bool:
    """验证名称是否有效"""
    if not name or not isinstance(name, str):
        return False
    return len(name.strip()) > 0