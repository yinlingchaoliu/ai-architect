# multi_agent_system/utils/message_bus.py
import asyncio
import json
import uuid
from typing import Dict, List, Any, Callable, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict
import threading
import time


class MessageType(Enum):
    """消息类型枚举"""
    AGENT_REQUEST = "agent_request"
    AGENT_RESPONSE = "agent_response"
    SYSTEM_EVENT = "system_event"
    PERFORMANCE_METRIC = "performance_metric"
    ERROR_REPORT = "error_report"
    PLANNING_UPDATE = "planning_update"
    ITERATION_PROGRESS = "iteration_progress"


class MessagePriority(Enum):
    """消息优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Message:
    """消息数据结构"""
    message_id: str
    message_type: MessageType
    channel: str
    payload: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: float = None
    source: str = None
    target: str = None
    correlation_id: str = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """初始化后自动设置时间戳"""
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def __lt__(self, other):
        """定义比较方法，优先按优先级排序，相同优先级则按时间戳排序"""
        if not isinstance(other, Message):
            return NotImplemented
        # 优先级数字越小优先级越低，所以返回负号进行降序排序
        if self.priority.value != other.priority.value:
            return self.priority.value > other.priority.value
        # 相同优先级时，时间戳小的优先（先到达的消息优先）
        return self.timestamp < other.timestamp

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "channel": self.channel,
            "payload": self.payload,
            "priority": self.priority.value,
            "timestamp": self.timestamp,
            "source": self.source,
            "target": self.target,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata or {}
        }

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)


class MessageBus:
    """增强的消息总线系统"""

    def __init__(self, max_queue_size: int = 1000):
        self.channels: Dict[str, asyncio.PriorityQueue] = {}
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.message_handlers: Dict[MessageType, List[Callable]] = defaultdict(list)
        self.max_queue_size = max_queue_size
        self.message_counter = 0
        self._lock = threading.Lock()
        self._statistics = {
            "messages_sent": 0,
            "messages_received": 0,
            "messages_processed": 0,
            "channels_created": 0,
            "subscribers_registered": 0
        }

        # 启动后台任务
        self._background_tasks = set()
        self._is_running = True

    async def initialize(self):
        """初始化消息总线"""
        # 创建系统监控任务
        monitor_task = asyncio.create_task(self._monitor_system_health())
        self._background_tasks.add(monitor_task)
        monitor_task.add_done_callback(self._background_tasks.discard)

        print("🚀 消息总线系统已初始化")

    async def shutdown(self):
        """关闭消息总线"""
        self._is_running = False

        # 等待所有后台任务完成
        for task in self._background_tasks:
            task.cancel()

        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)

        print("🛑 消息总线系统已关闭")

    async def publish(self,
                      channel: str,
                      message_type: MessageType,
                      payload: Dict[str, Any],
                      priority: MessagePriority = MessagePriority.NORMAL,
                      source: str = None,
                      target: str = None,
                      correlation_id: str = None,
                      metadata: Dict[str, Any] = None) -> str:
        """发布消息到指定频道"""

        # 创建消息
        message = Message(
            message_id=str(uuid.uuid4()),
            message_type=message_type,
            channel=channel,
            payload=payload,
            priority=priority,
            timestamp=time.time(),
            source=source,
            target=target,
            correlation_id=correlation_id,
            metadata=metadata
        )

        # 确保频道存在
        if channel not in self.channels:
            self.channels[channel] = asyncio.PriorityQueue(maxsize=self.max_queue_size)
            self._statistics["channels_created"] += 1

        # 计算优先级权重（数值越小优先级越高）
        priority_weight = 5 - message.priority.value  # CRITICAL=1, HIGH=2, NORMAL=3, LOW=4

        try:
            # 发布消息到队列
            await self.channels[channel].put((priority_weight, message))
            self._statistics["messages_sent"] += 1

            # 通知订阅者
            await self._notify_subscribers(message)

            print(f"📤 发布消息 [{message.message_type.value}] 到频道 '{channel}' (ID: {message.message_id})")

            return message.message_id

        except asyncio.QueueFull:
            print(f"⚠️  消息队列已满，无法发布消息到频道 '{channel}'")
            raise

    # async def subscribe(self, channel: str, callback: Callable):
    #     """订阅频道"""
    #     self.subscribers[channel].append(callback)
    #     self._statistics["subscribers_registered"] += 1
    #     print(f"📥 订阅频道 '{channel}'，当前订阅者: {len(self.subscribers[channel])}")

    # multi_agent_system/utils/message_bus.py
    # 修改 subscribe 方法为同步：

    def subscribe(self, channel: str, callback: Callable):
        """订阅频道"""
        if channel not in self.subscribers:
            self.subscribers[channel] = []

        self.subscribers[channel].append(callback)
        self._statistics["subscribers_registered"] += 1
        print(f"📥 订阅频道 '{channel}'，当前订阅者: {len(self.subscribers[channel])}")

    def subscribe_to_message_type(self, message_type: MessageType, callback: Callable):
        """订阅特定类型的消息"""
        self.message_handlers[message_type].append(callback)
        print(f"📥 订阅消息类型 '{message_type.value}'，当前处理器: {len(self.message_handlers[message_type])}")

    async def receive(self,
                      channel: str,
                      timeout: float = None,
                      filter_func: Callable[[Message], bool] = None) -> Optional[Message]:
        """从频道接收消息"""
        if channel not in self.channels:
            self.channels[channel] = asyncio.PriorityQueue(maxsize=self.max_queue_size)
            self._statistics["channels_created"] += 1

        try:
            if timeout:
                # 带超时的接收
                async with asyncio.timeout(timeout):
                    priority_weight, message = await self.channels[channel].get()
            else:
                # 无限等待
                priority_weight, message = await self.channels[channel].get()

            self._statistics["messages_received"] += 1

            # 应用过滤器
            if filter_func and not filter_func(message):
                # 如果不匹配，重新放回队列
                await self.channels[channel].put((priority_weight, message))
                return await self.receive(channel, timeout, filter_func)

            self._statistics["messages_processed"] += 1
            return message

        except asyncio.TimeoutError:
            print(f"⏰ 接收消息超时 (频道: {channel}, 超时: {timeout}s)")
            return None
        except Exception as e:
            print(f"❌ 接收消息失败: {e}")
            return None

    async def request_response(self,
                               request_channel: str,
                               response_channel: str,
                               message_type: MessageType,
                               payload: Dict[str, Any],
                               timeout: float = 30.0,
                               priority: MessagePriority = MessagePriority.NORMAL) -> Optional[Message]:
        """请求-响应模式"""
        correlation_id = str(uuid.uuid4())

        # 发布请求
        request_id = await self.publish(
            channel=request_channel,
            message_type=message_type,
            payload=payload,
            priority=priority,
            correlation_id=correlation_id
        )

        print(f"🔄 发送请求 [{message_type.value}] (ID: {request_id})，等待响应...")

        # 等待响应
        start_time = time.time()
        while time.time() - start_time < timeout:
            response = await self.receive(
                channel=response_channel,
                timeout=1.0,  # 短超时以便检查总超时
                filter_func=lambda msg: msg.correlation_id == correlation_id
            )

            if response:
                print(f"✅ 收到响应 (关联ID: {correlation_id})")
                return response

        print(f"⏰ 请求响应超时 (关联ID: {correlation_id})")
        return None

    async def broadcast(self,
                        message_type: MessageType,
                        payload: Dict[str, Any],
                        exclude_channels: List[str] = None,
                        priority: MessagePriority = MessagePriority.NORMAL):
        """广播消息到所有频道"""
        exclude_channels = exclude_channels or []
        broadcast_channels = [channel for channel in self.channels.keys()
                              if channel not in exclude_channels]

        tasks = []
        for channel in broadcast_channels:
            task = self.publish(
                channel=channel,
                message_type=message_type,
                payload=payload,
                priority=priority
            )
            tasks.append(task)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            print(f"📢 广播消息 [{message_type.value}] 到 {len(broadcast_channels)} 个频道")

    async def _notify_subscribers(self, message: Message):
        """通知订阅者"""
        channel = message.channel
        message_type = message.message_type

        # 通知频道订阅者
        if channel in self.subscribers:
            tasks = []
            for subscriber in self.subscribers[channel]:
                try:
                    if asyncio.iscoroutinefunction(subscriber):
                        task = asyncio.create_task(subscriber(message))
                    else:
                        # 如果是同步函数，在线程池中执行
                        task = asyncio.create_task(
                            asyncio.to_thread(subscriber, message)
                        )
                    tasks.append(task)
                except Exception as e:
                    print(f"❌ 通知订阅者失败: {e}")

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        # 通知消息类型处理器
        if message_type in self.message_handlers:
            tasks = []
            for handler in self.message_handlers[message_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        task = asyncio.create_task(handler(message))
                    else:
                        task = asyncio.create_task(
                            asyncio.to_thread(handler, message)
                        )
                    tasks.append(task)
                except Exception as e:
                    print(f"❌ 处理消息类型失败: {e}")

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    async def _monitor_system_health(self):
        """监控系统健康状态"""
        while self._is_running:
            try:
                # 收集统计信息
                stats = self.get_statistics()

                # 发布健康状态
                health_payload = {
                    "timestamp": time.time(),
                    "statistics": stats,
                    "channels_count": len(self.channels),
                    "total_subscribers": sum(len(subs) for subs in self.subscribers.values()),
                    "queue_sizes": {
                        channel: self.channels[channel].qsize()
                        for channel in self.channels
                    }
                }

                await self.publish(
                    channel="system.health",
                    message_type=MessageType.SYSTEM_EVENT,
                    payload=health_payload,
                    priority=MessagePriority.LOW
                )

                # 每30秒检查一次
                await asyncio.sleep(30)

            except Exception as e:
                print(f"❌ 系统健康监控失败: {e}")
                await asyncio.sleep(60)  # 出错时等待更长时间

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return self._statistics.copy()

    def get_channel_info(self, channel: str) -> Dict[str, Any]:
        """获取频道信息"""
        if channel not in self.channels:
            return {"error": f"频道 '{channel}' 不存在"}

        return {
            "channel": channel,
            "queue_size": self.channels[channel].qsize(),
            "subscribers_count": len(self.subscribers.get(channel, [])),
            "max_queue_size": self.max_queue_size
        }

    def list_channels(self) -> List[str]:
        """列出所有频道"""
        return list(self.channels.keys())

    def list_subscribers(self, channel: str = None) -> Dict[str, Any]:
        """列出订阅者"""
        if channel:
            return {
                channel: [sub.__name__ if hasattr(sub, '__name__') else str(sub)
                          for sub in self.subscribers.get(channel, [])]
            }
        else:
            return {
                chan: [sub.__name__ if hasattr(sub, '__name__') else str(sub)
                       for sub in subscribers]
                for chan, subscribers in self.subscribers.items()
            }


# 预定义的频道常量
class MessageChannels:
    """消息频道常量"""
    AGENT_REQUESTS = "agent.requests"
    AGENT_RESPONSES = "agent.responses"
    SYSTEM_EVENTS = "system.events"
    PERFORMANCE_METRICS = "performance.metrics"
    PLANNING_UPDATES = "planning.updates"
    ITERATION_PROGRESS = "iteration.progress"
    ERROR_REPORTS = "error.reports"
    COORDINATOR_COMMANDS = "coordinator.commands"

    # 各个Agent的专用频道
    WEATHER_AGENT = "agents.weather"
    TRANSPORT_AGENT = "agents.transport"
    BUDGET_AGENT = "agents.budget"
    COORDINATOR_AGENT = "agents.coordinator"