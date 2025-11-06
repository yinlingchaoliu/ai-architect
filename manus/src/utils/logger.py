# src/utils/logger.py
import logging
import os
from datetime import datetime

# 创建logger实例
def get_logger(name: str = __name__, level: int = logging.INFO) -> logging.Logger:
    """获取或创建logger实例
    
    Args:
        name: logger名称
        level: 日志级别
        
    Returns:
        logging.Logger实例
    """
    logger = logging.getLogger(name)
    
    # 避免重复添加handler
    if not logger.handlers:
        # 设置默认日志级别
        logger.setLevel(level)
        
        # 创建console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        # 添加handler到logger
        logger.addHandler(console_handler)
    
    return logger

def setup_logger(
    name: str = __name__, 
    level: int = logging.INFO, 
    log_file: str = None
) -> logging.Logger:
    """配置logger，包括文件输出
    
    Args:
        name: logger名称
        level: 日志级别
        log_file: 日志文件路径，None则不输出到文件
        
    Returns:
        logging.Logger实例
    """
    logger = get_logger(name, level)
    
    # 如果指定了日志文件，添加file handler
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 创建file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # 添加file handler到logger
        logger.addHandler(file_handler)
    
    return logger