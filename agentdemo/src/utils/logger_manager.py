# agentdemo/src/utils/logger_manager.py
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from ..models.agent_models import LogEntry, IterationPhase


class LoggerManager:
    """增强的日志管理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggerManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.loggers: Dict[str, logging.Logger] = {}
        self.log_entries: list[LogEntry] = []
        self.max_entries = 1000  # 最大日志条目数
        self._initialized = True
        
    def setup_logging(self, config: Dict[str, Any]):
        """设置日志系统"""
        log_level = getattr(logging, config.get('level', 'INFO'))
        log_format = config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # 创建日志目录
        if config.get('file_logging', True):
            log_file = config.get('log_file', 'logs/agentdemo.log')
            log_dir = Path(log_file).parent
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # 配置根日志记录器
            logging.basicConfig(
                level=log_level,
                format=log_format,
                handlers=[
                    logging.handlers.RotatingFileHandler(
                        log_file,
                        maxBytes=config.get('max_file_size', 10 * 1024 * 1024),  # 10MB
                        backupCount=config.get('backup_count', 5)
                    ),
                    logging.StreamHandler(sys.stdout)
                ]
            )
        else:
            logging.basicConfig(
                level=log_level,
                format=log_format,
                handlers=[logging.StreamHandler(sys.stdout)]
            )
        
        print(f"✅ 日志系统已初始化 - 级别: {config.get('level', 'INFO')}")
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志记录器"""
        if name not in self.loggers:
            self.loggers[name] = logging.getLogger(name)
        return self.loggers[name]
    
    def log_agent_operation(self, agent_name: str, operation: str, level: str = "INFO", 
                           execution_time: Optional[float] = None, 
                           timeout_occurred: bool = False,
                           retry_count: Optional[int] = None,
                           metadata: Dict[str, Any] = None):
        """记录Agent操作日志"""
        logger = self.get_logger(f"agent.{agent_name}")
        message = f"[{agent_name}] {operation}"
        
        if execution_time is not None:
            message += f" - 执行时间: {execution_time:.2f}s"
        if timeout_occurred:
            message += " - 超时发生"
        if retry_count is not None:
            message += f" - 重试次数: {retry_count}"
        
        # 记录到标准日志
        if level.upper() == "DEBUG":
            logger.debug(message)
        elif level.upper() == "INFO":
            logger.info(message)
        elif level.upper() == "WARNING":
            logger.warning(message)
        elif level.upper() == "ERROR":
            logger.error(message)
        elif level.upper() == "CRITICAL":
            logger.critical(message)
        
        # 记录到内存日志
        log_entry = LogEntry(
            timestamp=datetime.now(),
            level=level.upper(),
            module=f"agent.{agent_name}",
            message=operation,
            agent_name=agent_name,
            execution_time=execution_time,
            timeout_occurred=timeout_occurred,
            retry_count=retry_count,
            metadata=metadata or {}
        )
        self._add_log_entry(log_entry)
    
    def log_iteration_phase(self, phase: IterationPhase, iteration: int, 
                           operation: str, level: str = "INFO",
                           execution_time: Optional[float] = None,
                           timeout_warning: bool = False,
                           metadata: Dict[str, Any] = None):
        """记录迭代阶段日志"""
        logger = self.get_logger(f"iteration.{phase.value}")
        message = f"[迭代{iteration} - {phase.value}] {operation}"
        
        if execution_time is not None:
            message += f" - 执行时间: {execution_time:.2f}s"
        if timeout_warning:
            message += " - 超时预警"
        
        # 记录到标准日志
        if level.upper() == "DEBUG":
            logger.debug(message)
        elif level.upper() == "INFO":
            logger.info(message)
        elif level.upper() == "WARNING":
            logger.warning(message)
        elif level.upper() == "ERROR":
            logger.error(message)
        
        # 记录到内存日志
        log_entry = LogEntry(
            timestamp=datetime.now(),
            level=level.upper(),
            module=f"iteration.{phase.value}",
            message=operation,
            phase=phase,
            execution_time=execution_time,
            timeout_occurred=timeout_warning,
            metadata=metadata or {}
        )
        self._add_log_entry(log_entry)
    
    def log_system_event(self, event: str, level: str = "INFO", 
                        details: Dict[str, Any] = None):
        """记录系统事件日志"""
        logger = self.get_logger("system")
        message = f"[系统] {event}"
        
        if details:
            message += f" - 详情: {details}"
        
        # 记录到标准日志
        if level.upper() == "DEBUG":
            logger.debug(message)
        elif level.upper() == "INFO":
            logger.info(message)
        elif level.upper() == "WARNING":
            logger.warning(message)
        elif level.upper() == "ERROR":
            logger.error(message)
        elif level.upper() == "CRITICAL":
            logger.critical(message)
        
        # 记录到内存日志
        log_entry = LogEntry(
            timestamp=datetime.now(),
            level=level.upper(),
            module="system",
            message=event,
            metadata=details or {}
        )
        self._add_log_entry(log_entry)
    
    def log_timeout_event(self, component: str, operation: str, 
                         timeout_duration: float, retry_count: int = 0):
        """记录超时事件"""
        logger = self.get_logger("timeout")
        message = f"[{component}] {operation} - 超时: {timeout_duration}s"
        if retry_count > 0:
            message += f" - 重试: {retry_count}"
        
        logger.warning(message)
        
        log_entry = LogEntry(
            timestamp=datetime.now(),
            level="WARNING",
            module=f"timeout.{component}",
            message=operation,
            execution_time=timeout_duration,
            timeout_occurred=True,
            retry_count=retry_count,
            metadata={"component": component, "timeout_duration": timeout_duration}
        )
        self._add_log_entry(log_entry)
    
    def log_retry_attempt(self, component: str, operation: str, 
                         attempt: int, max_attempts: int, reason: str = ""):
        """记录重试尝试"""
        logger = self.get_logger("retry")
        message = f"[{component}] {operation} - 重试 {attempt}/{max_attempts}"
        if reason:
            message += f" - 原因: {reason}"
        
        logger.info(message)
        
        log_entry = LogEntry(
            timestamp=datetime.now(),
            level="INFO",
            module=f"retry.{component}",
            message=operation,
            retry_count=attempt,
            metadata={
                "component": component,
                "attempt": attempt,
                "max_attempts": max_attempts,
                "reason": reason
            }
        )
        self._add_log_entry(log_entry)
    
    def _add_log_entry(self, log_entry: LogEntry):
        """添加日志条目到内存"""
        self.log_entries.append(log_entry)
        
        # 限制日志条目数量
        if len(self.log_entries) > self.max_entries:
            self.log_entries = self.log_entries[-self.max_entries:]
    
    def get_recent_logs(self, count: int = 100, level: str = None) -> list[LogEntry]:
        """获取最近的日志条目"""
        logs = self.log_entries.copy()
        
        if level:
            logs = [log for log in logs if log.level == level.upper()]
        
        return logs[-count:]
    
    def get_logs_by_agent(self, agent_name: str, count: int = 50) -> list[LogEntry]:
        """获取指定Agent的日志"""
        agent_logs = [log for log in self.log_entries if log.agent_name == agent_name]
        return agent_logs[-count:]
    
    def get_logs_by_phase(self, phase: IterationPhase, count: int = 50) -> list[LogEntry]:
        """获取指定阶段的日志"""
        phase_logs = [log for log in self.log_entries if log.phase == phase]
        return phase_logs[-count:]
    
    def clear_logs(self):
        """清空内存中的日志"""
        self.log_entries.clear()
    
    def export_logs(self, file_path: str):
        """导出日志到文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for log_entry in self.log_entries:
                    f.write(f"{log_entry.to_dict()}\n")
            print(f"✅ 日志已导出到: {file_path}")
        except Exception as e:
            print(f"❌ 日志导出失败: {e}")


# 全局日志管理器实例
logger_manager = LoggerManager()
