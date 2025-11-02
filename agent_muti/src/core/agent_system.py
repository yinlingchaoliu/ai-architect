# multi_agent_system/core/agent_system.py
import asyncio
from typing import Dict, Any, List
from ..agents.coordinator_agent import EnhancedCoordinatorAgent
from ..plugins.weather_agent import WeatherAgent
from ..plugins.transport_agent import TransportAgent
from ..plugins.budget_agent import BudgetAgent
from .plugin_manager import AgentPluginManager
from ..utils.performance_monitor import PerformanceMonitor
from ..utils.message_bus import MessageBus, MessageType, MessagePriority
from ..models.agent_models import AgentResponse


class EnhancedDynamicAgentSystem:
    """增强的动态 Agent 系统"""

    def __init__(self, api_key: str, config: Dict[str, Any] = None):
        self.api_key = api_key
        self.config = config or {}
        self.coordinator = EnhancedCoordinatorAgent()

        # 从配置获取超时设置
        agent_timeout = self.config.get('agent_timeout', 30)
        coordinator_timeout = self.config.get('coordinator_timeout', 45)

        self.coordinator.initialize(api_key, timeout=coordinator_timeout)
        self.plugin_manager = AgentPluginManager()

        # 性能监控
        self.performance_monitor = PerformanceMonitor()
        self.message_bus = MessageBus()

        # 注册内置 Agent
        self._register_builtin_agents(agent_timeout)

        # 注册规划策略
        self._register_planning_strategies()

        # 注意：不在构造函数中初始化消息总线
        self._is_initialized = False

    def _register_builtin_agents(self, timeout: int = 30):
        """注册内置 Agent"""
        # 天气 Agent
        weather_agent = WeatherAgent()
        weather_agent.initialize(self.api_key, timeout=timeout)
        self.coordinator.register_agent(weather_agent)

        # 交通 Agent
        transport_agent = TransportAgent()
        transport_agent.initialize(self.api_key, timeout=timeout)
        self.coordinator.register_agent(transport_agent)

        # 预算 Agent
        budget_agent = BudgetAgent()
        budget_agent.initialize(self.api_key, timeout=timeout)
        self.coordinator.register_agent(budget_agent)

        print(f"✅ 注册了 {len(self.coordinator.agent_registry)} 个内置Agent (超时: {timeout}秒)")

    def _register_planning_strategies(self):
        """注册规划策略"""

        async def complex_multi_domain_strategy(query: str, intent_analysis: Dict[str, Any],
                                                available_agents: List[str]):
            """复杂多领域策略"""
            return {
                "strategy": "complex_multi_domain",
                "agent_sequence": available_agents,
                "parallel_tasks": [available_agents],  # 所有 Agent 并行执行
                "expected_output": "全面的多领域分析报告"
            }

        async def multi_domain_strategy(query: str, intent_analysis: Dict[str, Any], available_agents: List[str]):
            """多领域策略"""
            # 将 Agent 分组并行执行
            if len(available_agents) >= 3:
                mid = len(available_agents) // 2
                task_groups = [available_agents[:mid], available_agents[mid:]]
            else:
                task_groups = [available_agents]

            return {
                "strategy": "multi_domain",
                "agent_sequence": available_agents,
                "parallel_tasks": task_groups,
                "expected_output": "多领域综合分析"
            }

        async def single_domain_strategy(query: str, intent_analysis: Dict[str, Any], available_agents: List[str]):
            """单领域策略"""
            domains = intent_analysis.get("domains", [])
            if domains and available_agents:
                # 选择最相关的 Agent
                relevant_agents = [agent for agent in available_agents if
                                   any(domain in agent.lower() for domain in domains)]
                selected_agents = relevant_agents if relevant_agents else [available_agents[0]]
            else:
                selected_agents = [available_agents[0]] if available_agents else []

            return {
                "strategy": "single_domain",
                "agent_sequence": selected_agents,
                "parallel_tasks": [selected_agents],
                "expected_output": "专业领域深度分析"
            }

        self.coordinator.register_planning_strategy("complex_multi_domain", complex_multi_domain_strategy)
        self.coordinator.register_planning_strategy("multi_domain", multi_domain_strategy)
        self.coordinator.register_planning_strategy("single_domain", single_domain_strategy)

    def _setup_message_bus_sync(self):
        """同步设置消息总线 - 只注册处理器，不初始化"""

        # 注册消息处理器
        async def handle_agent_request(message):
            """处理Agent请求"""
            payload = message.payload
            agent_name = payload.get("target_agent")
            query = payload.get("query")
            context = payload.get("context", {})

            if agent_name in self.coordinator.agent_registry:
                agent = self.coordinator.agent_registry[agent_name]

                # 使用性能监控跟踪执行
                with self.performance_monitor.track_performance("agent_request", agent_name):
                    try:
                        response = await asyncio.wait_for(
                            agent.process_request(query, context),
                            timeout=agent.timeout + 10
                        )
                    except asyncio.TimeoutError:
                        response = AgentResponse(
                            agent_type=agent.agent_type,
                            content=f"Agent {agent_name} 执行超时",
                            data={},
                            confidence=0.0
                        )

                # 发布响应
                await self.message_bus.publish(
                    channel="agent.responses",
                    message_type=MessageType.AGENT_RESPONSE,
                    payload={
                        "agent_name": agent_name,
                        "response": response.to_dict(),
                        "original_request_id": message.message_id
                    },
                    correlation_id=message.correlation_id
                )

        # 订阅Agent请求频道 - 同步调用
        self.message_bus.subscribe("agent.requests", handle_agent_request)

        print("✅ 消息总线处理器注册完成")

    def load_plugins(self, package_path: str):
        """加载插件"""
        self.plugin_manager.discover_plugins(package_path)

    def create_and_register_agent(self, plugin_name: str, *args, **kwargs):
        """创建并注册 Agent"""
        agent = self.plugin_manager.create_agent_instance(plugin_name, *args, **kwargs)
        timeout = kwargs.get('timeout', 30)
        agent.initialize(self.api_key, timeout=timeout)
        self.coordinator.register_agent(agent)
        return agent

    async def process_query(self, query: str) -> AgentResponse:
        """处理用户查询"""
        if not self._is_initialized:
            raise RuntimeError("系统未初始化，请先调用 initialize_system()")

        print(f"🤖 增强多Agent系统开始处理: {query}")
        print("=" * 60)

        # 性能监控
        with self.performance_monitor.track_performance("system_query"):
            try:
                response = await asyncio.wait_for(
                    self.coordinator.process_request(query),
                    timeout=120  # 整个查询处理的超时时间
                )
            except asyncio.TimeoutError:
                print("⏰ 系统处理超时，返回错误响应")
                response = AgentResponse(
                    agent_type=self.coordinator.agent_type,
                    content="系统处理超时，请稍后重试或简化您的请求",
                    data={"error": "timeout", "query": query},
                    confidence=0.0
                )

        print(f"✅ 处理完成! 迭代次数: {response.metadata.get('iterations', 1)}")
        print("=" * 60)

        return response

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        agent_info = {}
        for name, agent in self.coordinator.agent_registry.items():
            agent_info[name] = {
                "type": agent.agent_type.value,
                "timeout": getattr(agent, 'timeout', 'unknown'),
                "initialized": agent._initialized
            }

        return {
            "loaded_plugins": self.plugin_manager.get_available_plugins(),
            "registered_agents": list(self.coordinator.agent_registry.keys()),
            "agent_details": agent_info,
            "conversation_memory": len(self.coordinator.conversation_memory),
            "performance_metrics": self.performance_monitor.get_metrics(),
            "system_health": self.performance_monitor.get_system_health(),
            "is_initialized": self._is_initialized
        }

    async def initialize_system(self):
        """初始化系统 - 异步初始化"""
        if self._is_initialized:
            print("⚠️  系统已经初始化")
            return

        print("🔧 初始化消息总线...")
        await self.message_bus.initialize()

        print("🔧 注册消息处理器...")
        self._setup_message_bus_sync()  # 同步调用

        self._is_initialized = True
        print("✅ 多Agent系统初始化完成")

    async def shutdown_system(self):
        """关闭系统"""
        if not self._is_initialized:
            print("⚠️  系统未初始化，无需关闭")
            return

        await self.message_bus.shutdown()
        self._is_initialized = False
        print("🛑 多Agent系统已关闭")

    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        return self.performance_monitor.generate_report()

    def set_agent_timeout(self, agent_name: str, timeout: int):
        """设置特定Agent的超时时间"""
        if agent_name in self.coordinator.agent_registry:
            agent = self.coordinator.agent_registry[agent_name]
            agent.timeout = timeout
            print(f"⏰ 设置 {agent_name} 超时为 {timeout} 秒")

    def set_iteration_timeout(self, phase: str, timeout: int):
        """设置迭代阶段超时时间"""
        if hasattr(self.coordinator.iteration_controller, 'set_phase_timeout'):
            self.coordinator.iteration_controller.set_phase_timeout(phase, timeout)