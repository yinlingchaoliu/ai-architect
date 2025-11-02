# multi_agent_system/utils/performance_monitor.py
import time
import threading
from typing import Dict, Any, List
from contextlib import contextmanager
from dataclasses import dataclass
from collections import defaultdict, deque
import statistics


@dataclass
class PerformanceMetric:
    """性能指标数据结构"""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = None
    metadata: Dict[str, Any] = None


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self, max_metrics_history: int = 1000):
        self.max_metrics_history = max_metrics_history
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_metrics_history))
        self._lock = threading.Lock()
        self._aggregated_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_response_time": 0.0,
            "active_agents": 0,
            "max_concurrent_agents": 0
        }

        # Agent 性能统计
        self.agent_metrics: Dict[str, Dict] = defaultdict(lambda: {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_execution_time": 0.0,
            "average_execution_time": 0.0,
            "min_execution_time": float('inf'),
            "max_execution_time": 0.0,
            "last_execution_time": 0.0
        })

    @contextmanager
    def track_performance(self, operation_name: str, agent_name: str = None, tags: Dict[str, str] = None):
        """跟踪操作性能"""
        start_time = time.time()

        # 更新活跃Agent计数
        if agent_name:
            with self._lock:
                self._aggregated_metrics["active_agents"] += 1
                current_active = self._aggregated_metrics["active_agents"]
                if current_active > self._aggregated_metrics["max_concurrent_agents"]:
                    self._aggregated_metrics["max_concurrent_agents"] = current_active

        try:
            yield
            end_time = time.time()
            duration = end_time - start_time

            # 记录成功指标
            self._record_metric(
                PerformanceMetric(
                    name=f"{operation_name}.duration",
                    value=duration,
                    timestamp=end_time,
                    tags=tags or {},
                    metadata={"agent": agent_name, "status": "success"}
                )
            )

            # 更新聚合指标
            with self._lock:
                self._aggregated_metrics["total_requests"] += 1
                self._aggregated_metrics["successful_requests"] += 1
                self._aggregated_metrics["total_response_time"] += duration

            # 更新Agent指标
            if agent_name:
                with self._lock:
                    agent_metric = self.agent_metrics[agent_name]
                    agent_metric["total_executions"] += 1
                    agent_metric["successful_executions"] += 1
                    agent_metric["total_execution_time"] += duration
                    agent_metric["last_execution_time"] = duration

                    # 更新最小/最大执行时间
                    if duration < agent_metric["min_execution_time"]:
                        agent_metric["min_execution_time"] = duration
                    if duration > agent_metric["max_execution_time"]:
                        agent_metric["max_execution_time"] = duration

                    # 计算平均执行时间
                    agent_metric["average_execution_time"] = (
                            agent_metric["total_execution_time"] / agent_metric["total_executions"]
                    )

        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time

            # 记录失败指标
            self._record_metric(
                PerformanceMetric(
                    name=f"{operation_name}.duration",
                    value=duration,
                    timestamp=end_time,
                    tags=tags or {},
                    metadata={"agent": agent_name, "status": "failed", "error": str(e)}
                )
            )

            # 更新聚合指标
            with self._lock:
                self._aggregated_metrics["total_requests"] += 1
                self._aggregated_metrics["failed_requests"] += 1

            # 更新Agent指标
            if agent_name:
                with self._lock:
                    agent_metric = self.agent_metrics[agent_name]
                    agent_metric["total_executions"] += 1
                    agent_metric["failed_executions"] += 1
                    agent_metric["last_execution_time"] = duration

            raise e

        finally:
            # 减少活跃Agent计数
            if agent_name:
                with self._lock:
                    self._aggregated_metrics["active_agents"] -= 1

    def _record_metric(self, metric: PerformanceMetric):
        """记录性能指标"""
        with self._lock:
            self.metrics_history[metric.name].append(metric)

    def record_custom_metric(self, name: str, value: float, tags: Dict[str, str] = None,
                             metadata: Dict[str, Any] = None):
        """记录自定义指标"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=time.time(),
            tags=tags or {},
            metadata=metadata or {}
        )
        self._record_metric(metric)

    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        with self._lock:
            metrics = self._aggregated_metrics.copy()

            # 计算平均响应时间
            if metrics["total_requests"] > 0:
                metrics["average_response_time"] = metrics["total_response_time"] / metrics["total_requests"]
            else:
                metrics["average_response_time"] = 0.0

            # 计算成功率
            if metrics["total_requests"] > 0:
                metrics["success_rate"] = (metrics["successful_requests"] / metrics["total_requests"]) * 100
            else:
                metrics["success_rate"] = 0.0

            # 添加Agent指标
            metrics["agent_metrics"] = dict(self.agent_metrics)

            return metrics

    def get_metric_history(self, metric_name: str, limit: int = None) -> List[PerformanceMetric]:
        """获取指标历史"""
        with self._lock:
            history = list(self.metrics_history.get(metric_name, []))
            if limit and len(history) > limit:
                return history[-limit:]
            return history

    def get_metric_statistics(self, metric_name: str, time_window: float = None) -> Dict[str, Any]:
        """获取指标统计信息"""
        history = self.get_metric_history(metric_name)

        if time_window:
            cutoff_time = time.time() - time_window
            history = [m for m in history if m.timestamp >= cutoff_time]

        if not history:
            return {
                "count": 0,
                "average": 0,
                "min": 0,
                "max": 0,
                "p95": 0,
                "p99": 0
            }

        values = [m.value for m in history]

        return {
            "count": len(values),
            "average": statistics.mean(values),
            "min": min(values),
            "max": max(values),
            "p95": self._calculate_percentile(values, 95),
            "p99": self._calculate_percentile(values, 99)
        }

    def _calculate_percentile(self, values: List[float], percentile: float) -> float:
        """计算百分位数"""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = (len(sorted_values) - 1) * percentile / 100
        lower_index = int(index)
        upper_index = lower_index + 1

        if upper_index >= len(sorted_values):
            return sorted_values[lower_index]

        weight = index - lower_index
        return sorted_values[lower_index] * (1 - weight) + sorted_values[upper_index] * weight

    def get_agent_performance(self, agent_name: str) -> Dict[str, Any]:
        """获取Agent性能数据"""
        with self._lock:
            return self.agent_metrics.get(agent_name, {}).copy()

    def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        metrics = self.get_metrics()

        health_status = "healthy"
        issues = []

        # 检查成功率
        if metrics.get("success_rate", 100) < 90:
            health_status = "degraded"
            issues.append("成功率低于90%")

        # 检查平均响应时间
        avg_response_time = metrics.get("average_response_time", 0)
        if avg_response_time > 30:  # 超过30秒
            health_status = "degraded"
            issues.append(f"平均响应时间过高: {avg_response_time:.2f}秒")

        # 检查失败请求数
        if metrics.get("failed_requests", 0) > 10:
            health_status = "degraded"
            issues.append(f"失败请求数过多: {metrics['failed_requests']}")

        return {
            "status": health_status,
            "issues": issues,
            "timestamp": time.time(),
            "metrics": {
                "success_rate": metrics.get("success_rate", 0),
                "average_response_time": metrics.get("average_response_time", 0),
                "total_requests": metrics.get("total_requests", 0),
                "active_agents": metrics.get("active_agents", 0)
            }
        }

    def reset_metrics(self):
        """重置性能指标"""
        with self._lock:
            self.metrics_history.clear()
            self._aggregated_metrics = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_response_time": 0.0,
                "active_agents": 0,
                "max_concurrent_agents": 0
            }
            self.agent_metrics.clear()

    def generate_report(self) -> Dict[str, Any]:
        """生成性能报告"""
        metrics = self.get_metrics()
        system_health = self.get_system_health()

        report = {
            "timestamp": time.time(),
            "system_health": system_health,
            "overall_metrics": {
                "total_requests": metrics["total_requests"],
                "success_rate": metrics["success_rate"],
                "average_response_time": metrics["average_response_time"],
                "max_concurrent_agents": metrics["max_concurrent_agents"]
            },
            "agent_performance": {}
        }

        # 添加Agent性能详情
        for agent_name, agent_metric in metrics.get("agent_metrics", {}).items():
            report["agent_performance"][agent_name] = {
                "total_executions": agent_metric["total_executions"],
                "success_rate": (agent_metric["successful_executions"] / agent_metric["total_executions"] * 100) if
                agent_metric["total_executions"] > 0 else 0,
                "average_execution_time": agent_metric["average_execution_time"],
                "min_execution_time": agent_metric["min_execution_time"],
                "max_execution_time": agent_metric["max_execution_time"]
            }

        return report