import logging
import sys
from datetime import datetime

import os

class ColorFormatter(logging.Formatter):
    """彩色日志格式化器 - 支持自定义颜色"""

    # ANSI 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',  # 青色
        'INFO': '\033[32m',  # 绿色
        'WARNING': '\033[34m',  # 黄色
        'ERROR': '\033[31m',  # 红色
        'CRITICAL': '\033[35m',  # 洋红色
        'RED': '\033[31m',
        'GREEN': '\033[32m',
        'YELLOW': '\033[33m',
        'BLUE': '\033[34m',
        'MAGENTA': '\033[35m',
        'CYAN': '\033[36m',
        'WHITE': '\033[37m',
        'RESET': '\033[0m'  # 重置颜色
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
            reset = self.COLORS['RESET']
            # 为消息内容添加颜色
            record.msg = f"{color}{record.msg}{reset}"
            # 为级别名称添加颜色
            record.levelname = f"{color}{record.levelname}{reset}"
        elif record.levelname in self.COLORS:
            color = self.COLORS[record.levelname]
            reset = self.COLORS['RESET']
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


class Logger:
    """日志管理类 - 支持指定颜色"""

    # 颜色常量
    RED = 'RED'
    GREEN = 'GREEN'
    YELLOW = 'YELLOW'
    BLUE = 'BLUE'
    MAGENTA = 'MAGENTA'
    CYAN = 'CYAN'
    WHITE = 'WHITE'

    def __init__(self, name: str = "discussion"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # 避免重复添加handler
        if not self.logger.handlers:
            # 获取调用者的文件名
            caller_frame = sys._getframe(1)
            caller_filename = os.path.basename(caller_frame.f_code.co_filename)
            print(caller_filename)

            # 通用格式化器（用于文件）
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s'
            )

            # 控制台handler - 使用彩色格式化器
            console_handler = logging.StreamHandler(sys.stdout)
            console_formatter = ColorFormatter(
                '%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

            # 文件handler - 使用普通格式化器（无颜色）
            file_handler = logging.FileHandler(
                f'logs/discussion_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def info(self, message: str, color: str = WHITE):
        """记录信息级别日志，可指定颜色"""
        if color:
            self.logger.info(message, extra={'custom_color': color},stacklevel=2)
        else:
            self.logger.info(message,stacklevel=2)

    def error(self, message: str, color: str = None):
        """记录错误级别日志，可指定颜色"""
        if color:
            self.logger.error(message, extra={'custom_color': color},stacklevel=2)
        else:
            self.logger.error(message,stacklevel=2)

    def warning(self, message: str, color: str = None):
        """记录警告级别日志，可指定颜色"""
        if color:
            self.logger.warning(message, extra={'custom_color': color},stacklevel=2)
        else:
            self.logger.warning(message,stacklevel=2)

    def debug(self, message: str, color: str = None):
        """记录调试级别日志，可指定颜色"""
        if color:
            self.logger.debug(message, extra={'custom_color': color},stacklevel=2)
        else:
            self.logger.debug(message,stacklevel=2)

    def critical(self, message: str, color: str = None):
        """记录严重级别日志，可指定颜色"""
        if color:
            self.logger.critical(message, extra={'custom_color': color},stacklevel=2)
        else:
            self.logger.critical(message,stacklevel=2)


# 全局日志实例
logger = Logger()