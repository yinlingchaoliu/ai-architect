import datetime
from typing import Any, Dict


# 辅助函数：将datetime对象转换为字符串
def datetime_to_str(data: Any) -> Any:
    if isinstance(data, datetime.datetime):
        return data.isoformat()
    elif isinstance(data, datetime.date):
        return data.isoformat()
    elif isinstance(data, dict):
        return {k: datetime_to_str(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [datetime_to_str(item) for item in data]
    return data
