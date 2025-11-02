# agentdemo/src/core/agent_system.py
import asyncio
import time
from typing import Dict, List, Any, Optional
import importlib
import inspect
from pathlib import Path

from ..agents.base_agent import BaseAgent
from ..agents.coordinator_agent import CoordinatorAgent
from ..core.iteration_controller import EnhancedIterationController
from ..utils.logger_manager import logger_manager
from ..models.agent_models import AgentType, SystemStatus


class EnhancedDynamicAgentSystem:
    """增强的动态 Agent 系统 - 专注于超时处理和系统稳定性"""

    def __init__(self, api_key: str, config: Dict[str, Any] = None):
        self.api_key = api_key
        self.config = config or {}
        self.agent_registry: Dict[str, BaseAgent] = {}
        self.coordinator: Optional[CoordinatorAgent] = None
        self.iteration_controller: Optional[EnhancedIterationController] = None
        self.initialized = False
        self.start_time = time.time()
        
        # 系统状态监控
        self.system_status = SystemStatus()
        self.total_queries = 0
        self.successful_queries = 0
        self.failed_queries = 0

    async def initialize_system(self):
        """初始化系统"""
        logger_manager.log_system_event(
            "开始初始化系统",
            level="INFO"
        )
        
        try:
            # 初始化迭代控制器
            max_iterations = self.config.get('iteration', {}).get('max_iterations', 5)
            self.iteration_controller = EnhancedIterationController(max_iterations=max_iterations)
            
            # 初始化协调器
            self.coordinator = CoordinatorAgent()
            coordinator_config = self.config.get('agents', {}).get('coordinator', {})
            self.coordinator.initialize(
                self.api_key,
                model=coordinator_config.get('model', 'gpt-3.5-turbo'),
                timeout=coordinator_config.get('timeout', 50)
            )
            
            # 注册协调器
            self.agent_registry['coordinator'] = self.coordinator
            
            # 加载插件Agent
            await self._load_plugin_agents()
            
            # 更新系统状态
            self.system_status.overall_status = "ready"
            self.system_status.total_agents = len(self.agent_registry)
            self.system_status.active_agents = len(self.agent_registry)
            self.system_status.uptime = time.time() - self.start_time
            
            self.initialized = True
            
            logger_manager.log_system_event(
                f"系统初始化完成 - 总Agent数: {len(self.agent_registry)}",
                level="INFO",
                details={
                    "total_agents": len(self.agent_registry),
                    "agent_names": list(self.agent_registry.keys())
                }
            )
            
        except Exception as e:
            self.system_status.overall_status = "error"
            logger_manager.log_system_event(
                f"系统初始化失败: {e}",
                level="ERROR"
            )
            raise

    async def _load_plugin_agents(self):
        """加载插件Agent"""
        plugins_config = self.config.get('plugins', {})
        if not plugins_config.get('auto_discover', True):
            return

        # 从配置中获取启用的Agent
        enabled_agents = self.config.get('agents', {})
        
        for agent_name, agent_config in enabled_agents.items():
            if agent_name == 'coordinator':
                continue
                
            if not agent_config.get('enabled', True):
                logger_manager.log_system_event(
                    f"跳过未启用的Agent: {agent_name}",
                    level="DEBUG"
                )
                continue

            try:
                # 动态导入Agent类
                agent_class = await self._import_agent_class(agent_name)
                if agent_class:
                    agent_instance = agent_class()
                    
                    # 初始化Agent
                    agent_instance.initialize(
                        self.api_key,
                        model=agent_config.get('model', 'gpt-3.5-turbo'),
                        timeout=agent_config.get('timeout', 30)
                    )
                    
                    # 注册Agent
                    self.agent_registry[agent_name] = agent_instance
                    
                    logger_manager.log_agent_operation(
                        agent_name,
                        "Agent加载成功",
                        level="INFO"
                    )
                    
            except Exception as e:
                logger_manager.log_system_event(
                    f"加载Agent失败: {agent_name} - {e}",
                    level="ERROR"
                )

    async def _import_agent_class(self, agent_name: str):
        """动态导入Agent类"""
        try:
            # 尝试从plugins模块导入
            module_name = f"..plugins.{agent_name}_agent"
            module = importlib.import_module(module_name, __package__)
            
            # 查找Agent类（类名格式为 WeatherAgent, TransportAgent 等）
            class_name = f"{agent_name.capitalize()}Agent"
            
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BaseAgent) and 
                    obj != BaseAgent and
                    name == class_name):
                    return obj
            
            logger_manager.log_system_event(
                f"在模块 {module_name} 中未找到Agent类: {class_name}",
                level="WARNING"
            )
            return None
            
        except ImportError as e:
            logger_manager.log_system_event(
                f"导入Agent模块失败: {agent_name} - {e}",
                level="WARNING"
            )
            return None

    async def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """处理用户查询"""
        if not self.initialized:
            raise RuntimeError("系统未初始化")
        
        self.total_queries += 1
        start_time = time.time()
        
        logger_manager.log_system_event(
            f"开始处理查询: {query}",
            level="INFO",
            details={"query": query}
        )

        try:
            # 准备上下文
            execution_context = context or {}
            execution_context["last_query"] = query
            execution_context["query_timestamp"] = time.time()
            
            # 获取可用的Agent列表（排除协调器）
            available_agents = [name for name in self.agent_registry.keys() if name != 'coordinator']
            
            # 执行迭代周期
            result = await self.iteration_controller.execute_iteration_cycle(
                query, execution_context, self.coordinator, available_agents
            )
            
            # 更新成功统计
            self.successful_queries += 1
            execution_time = time.time() - start_time
            
            logger_manager.log_system_event(
                f"查询处理完成 - 执行时间: {execution_time:.2f}s",
                level="INFO",
                details={
                    "query": query,
                    "execution_time": round(execution_time, 2),
                    "iterations": result.get('iteration_count', 0)
                }
            )
            
            return result
            
        except Exception as e:
            self.failed_queries += 1
            execution_time = time.time() - start_time
            
            logger_manager.log_system_event(
                f"查询处理失败: {e}",
                level="ERROR",
                details={
                    "query": query,
                    "execution_time": round(execution_time, 2),
                    "error": str(e)
                }
            )
            
            return {
                "final_result": {
                    "error": str(e),
                    "content": f"处理查询时发生错误: {e}",
                    "confidence_score": 0.0
                },
                "iteration_count": 0,
                "history": [],
                "performance": {
                    "total_timeouts": 0,
                    "total_retries": 0,
                    "phase_execution_times": {}
                }
            }

    async def shutdown_system(self):
        """关闭系统"""
        logger_manager.log_system_event(
            "开始关闭系统",
            level="INFO"
        )
        
        try:
            # 清理资源
            self.agent_registry.clear()
            self.coordinator = None
            self.iteration_controller = None
            self.initialized = False
            
            logger_manager.log_system_event(
                "系统关闭完成",
                level="INFO"
            )
            
        except Exception as e:
            logger_manager.log_system_event(
                f"系统关闭失败: {e}",
                level="ERROR"
            )

    def get_system_status(self) -> SystemStatus:
        """获取系统状态"""
        if not self.initialized:
            self.system_status.overall_status = "not_initialized"
            return self.system_status
        
        # 更新实时状态
        self.system_status.uptime = time.time() - self.start_time
        self.system_status.total_agents = len(self.agent_registry)
        self.system_status.active_agents = len(self.agent_registry)
        self.system_status.current_iteration = getattr(
            self.iteration_controller, 'current_iteration', 0
        )
        
        # 更新Agent状态
        agent_statuses = {}
        for name, agent in self.agent_registry.items():
            agent_statuses[name] = getattr(agent, 'status', 'unknown').value
        
        self.system_status.agent_statuses = agent_statuses
        
        return self.system_status

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        if not self.initialized:
            return {}
        
        # 系统级指标
        system_metrics = {
            "total_queries": self.total_queries,
            "successful_queries": self.successful_queries,
            "failed_queries": self.failed_queries,
            "success_rate": (self.successful_queries / self.total_queries * 100) if self.total_queries > 0 else 0,
            "uptime": time.time() - self.start_time
        }
        
        # Agent级指标
        agent_metrics = {}
        for name, agent in self.agent_registry.items():
            if hasattr(agent, 'get_performance_metrics'):
                agent_metrics[name] = agent.get_performance_metrics()
        
        # 迭代控制器指标
        iteration_metrics = {}
        if self.iteration_controller:
            iteration_metrics = self.iteration_controller.get_performance_metrics()
        
        return {
            "system": system_metrics,
            "agents": agent_metrics,
            "iteration": iteration_metrics
        }

    def get_available_agents(self) -> List[str]:
        """获取可用的Agent列表"""
        return list(self.agent_registry.keys())

    def get_agent_info(self, agent_name: str) -> Dict[str, Any]:
        """获取指定Agent的详细信息"""
        if agent_name not in self.agent_registry:
            raise ValueError(f"Agent '{agent_name}' 不存在")
        
        agent = self.agent_registry[agent_name]
        if hasattr(agent, 'get_agent_info'):
            return agent.get_agent_info()
        
        return {
            "name": agent_name,
            "type": getattr(agent, 'agent_type', 'unknown'),
            "description": getattr(agent, 'description', ''),
            "initialized": getattr(agent, '_initialized', False)
        }
