"""utils模块初始化 - 包含工具函数和辅助组件"""

# 配置管理
from .config import Config, global_config, ConfigLoader

# 日志工具
try:
    from .logger import default_logger, setup_logger, log_debug, log_info, log_warning, log_error
except ImportError:
    # 如果logger模块不存在，则提供默认实现
    import logging
    default_logger = logging.getLogger(__name__)
    def setup_logger(name):
        return default_logger
    def log_debug(msg): pass
    def log_info(msg): pass
    def log_warning(msg): pass
    def log_error(msg): pass

__all__ = [
    # 配置管理
    "Config",
    "global_config",
    "ConfigLoader",
    
    # 日志工具
    "default_logger",
    "setup_logger",
    "log_debug",
    "log_info",
    "log_warning",
    "log_error"
]