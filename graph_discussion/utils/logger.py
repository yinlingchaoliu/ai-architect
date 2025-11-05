# 彩色日志工具
import logging

from datetime import datetime

import sys

class ColorFormatter(logging.Formatter):
    """彩色日志格式化器 - 支持自定义颜色"""

    COLORS = {
        'DEBUG': '\033[36m',  # 青色
        'INFO': '\033[32m',  # 绿色
        'WARNING': '\033[34m',  # 黄色
        'ERROR': '\033[31m',  # 红色
        'CRITICAL': '\033[35m',  # 洋红色
        'red': '\033[91m',
        'green': '\033[92m', 
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'reset': '\033[0m',
    }

    def format(self, record):
        # 保存原始格式
        original_msg = record.msg
        original_levelname = record.levelname

        # 获取自定义颜色（如果存在）
        custom_color = getattr(record, 'custom_color', None)

        # 为整个消息添加颜色
        if custom_color and custom_color in self.COLORS:
            color = self.COLORS[custom_color]
            reset = self.COLORS['reset']
            # 为消息内容添加颜色
            record.msg = f"{color}{record.msg}{reset}"
            # 为级别名称添加颜色
            record.levelname = f"{color}{record.levelname}{reset}"
        elif record.levelname in self.COLORS:
            color = self.COLORS[record.levelname]
            reset = self.COLORS['reset']
            # 为消息内容添加颜色
            record.msg = f"{color}{record.msg}{reset}"
            # 为级别名称添加颜色
            record.levelname = f"{color}{record.levelname}{reset}"

        # 调用父类格式化
        result = super().format(record)

        # 恢复原始格式（不影响文件输出）
        record.msg = original_msg
        record.levelname = original_levelname

        return result

class ColorfulLogger:
    
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            # 控制台handler - 使用彩色格式化器
            console_handler = logging.StreamHandler(sys.stdout)
            console_formatter = ColorFormatter(
                '%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

            # 通用格式化器（用于文件）
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s'
            )

            # 文件handler - 使用普通格式化器（无颜色）
            file_handler = logging.FileHandler(
                f'logs/discussion_{datetime.now().strftime("%Y%m%d_%H")}.log'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def info(self, message: str, color: str = 'white'):
        """带颜色的info日志"""
        self.logger.info(message,extra={'custom_color': color},stacklevel=2)

# 创建全局logger实例
def get_logger(name: str) -> ColorfulLogger:
    return ColorfulLogger(name)