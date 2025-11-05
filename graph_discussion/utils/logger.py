# 彩色日志工具
import logging

class ColorfulLogger:
    """彩色日志类"""
    COLORS = {
        'red': '\033[91m',
        'green': '\033[92m', 
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'reset': '\033[0m'
    }
    
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def info(self, message: str, color: str = 'white'):
        """带颜色的info日志"""
        color_code = self.COLORS.get(color, self.COLORS['white'])
        reset_code = self.COLORS['reset']
        self.logger.info(f"{color_code}{message}{reset_code}",stacklevel=2)

# 创建全局logger实例
def get_logger(name: str) -> ColorfulLogger:
    return ColorfulLogger(name)