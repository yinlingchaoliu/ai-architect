# multi_agent_system/core/planning_engine.py
import asyncio
import json
import uuid
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict


class PlanPriority(Enum):
    """计划优先级枚举"""
    CRITICAL = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1


class PlanStatus(Enum):
    """计划状态枚举"""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionPlan:
    """执行计划数据结构"""
    plan_id: str
    strategy: str
    agent_sequence: List[str]
    parallel_tasks: List[List[str]]
    expected_outputs: Dict[str, Any]
    priority: PlanPriority
    estimated_duration: float  # 预估执行时间（秒）
    dependencies: List[str]  # 依赖的计划ID
    context_requirements: Dict[str, Any]  # 执行所需上下文
    status: PlanStatus = PlanStatus.PENDING
    created_at: float = None
    started_at: float = None
    completed_at: float = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "plan_id": self.plan_id,
            "strategy": self.strategy,
            "agent_sequence": self.agent_sequence,
            "parallel_tasks": self.parallel_tasks,
            "expected_outputs": self.expected_outputs,
            "priority": self.priority.value,
            "estimated_duration": self.estimated_duration,
            "dependencies": self.dependencies,
            "context_requirements": self.context_requirements,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }


@dataclass
class PlanningContext:
    """规划上下文"""
    query: str
    available_agents: List[str]
    agent_capabilities: Dict[str, List[Dict]]
    conversation_history: List[Dict]
    current_iteration: int
    previous_plans: List[ExecutionPlan]
    system_constraints: Dict[str, Any]


class PlanningEngine:
    """智能规划引擎"""

    def __init__(self, coordinator):
        self.coordinator = coordinator
        self.planning_strategies: Dict[str, Callable] = {}
        self.plan_history: Dict[str, ExecutionPlan] = {}
        self.agent_performance_stats: Dict[str, Dict] = defaultdict(lambda: {
            "total_executions": 0,
            "successful_executions": 0,
            "average_execution_time": 0.0,
            "last_execution_time": 0.0
        })

        # 注册内置规划策略
        self._register_builtin_strategies()

    def _register_builtin_strategies(self):
        """注册内置规划策略"""

        async def sequential_strategy(context: PlanningContext) -> ExecutionPlan:
            """顺序执行策略 - 适用于简单任务"""
            plan_id = f"plan_{len(self.plan_history) + 1}"

            return ExecutionPlan(
                plan_id=plan_id,
                strategy="sequential",
                agent_sequence=context.available_agents,
                parallel_tasks=[[agent] for agent in context.available_agents],  # 每个任务单独执行
                expected_outputs={agent: f"{agent}的专业分析" for agent in context.available_agents},
                priority=PlanPriority.MEDIUM,
                estimated_duration=len(context.available_agents) * 10,  # 预估每个Agent 10秒
                dependencies=[],
                context_requirements={"query": context.query},
                created_at=asyncio.get_event_loop().time()
            )

        async def parallel_strategy(context: PlanningContext) -> ExecutionPlan:
            """并行执行策略 - 适用于独立任务"""
            plan_id = f"plan_{len(self.plan_history) + 1}"

            return ExecutionPlan(
                plan_id=plan_id,
                strategy="parallel",
                agent_sequence=context.available_agents,
                parallel_tasks=[context.available_agents],  # 所有Agent并行执行
                expected_outputs={agent: f"{agent}的专业分析" for agent in context.available_agents},
                priority=PlanPriority.HIGH,
                estimated_duration=15,  # 并行执行时间较短
                dependencies=[],
                context_requirements={"query": context.query},
                created_at=asyncio.get_event_loop().time()
            )

        async def dependency_aware_strategy(context: PlanningContext) -> ExecutionPlan:
            """依赖感知策略 - 考虑任务间依赖关系"""
            # 分析任务依赖关系
            dependencies = self._analyze_dependencies(context)

            # 构建执行序列
            execution_sequence = self._build_dependency_sequence(dependencies, context.available_agents)

            plan_id = f"plan_{len(self.plan_history) + 1}"

            return ExecutionPlan(
                plan_id=plan_id,
                strategy="dependency_aware",
                agent_sequence=execution_sequence,
                parallel_tasks=self._group_parallel_tasks(execution_sequence, dependencies),
                expected_outputs={agent: f"{agent}的专业分析" for agent in context.available_agents},
                priority=PlanPriority.HIGH,
                estimated_duration=self._estimate_duration(execution_sequence, dependencies),
                dependencies=[],
                context_requirements={"query": context.query, "dependencies": dependencies},
                created_at=asyncio.get_event_loop().time()
            )

        async def llm_optimized_strategy(context: PlanningContext) -> ExecutionPlan:
            """LLM优化策略 - 使用LLM生成最优计划"""
            plan_prompt = self._build_llm_planning_prompt(context)

            messages = [
                {"role": "system", "content": "你是一个专业的任务规划专家，能够制定高效的多Agent执行计划。"},
                {"role": "user", "content": plan_prompt}
            ]

            plan_text = self.coordinator._call_llm(messages)

            try:
                plan_data = json.loads(plan_text)
                return self._parse_llm_plan(plan_data, context)
            except json.JSONDecodeError:
                # 如果LLM返回的不是标准JSON，使用fallback策略
                print("⚠️  LLM规划解析失败，使用fallback策略")
                return await self.planning_strategies["dependency_aware"](context)

        async def iterative_refinement_strategy(context: PlanningContext) -> ExecutionPlan:
            """迭代优化策略 - 基于历史执行数据优化"""
            if not context.previous_plans:
                return await self.planning_strategies["dependency_aware"](context)

            # 分析历史执行数据
            performance_analysis = self._analyze_historical_performance(context.previous_plans)

            # 基于性能数据优化计划
            optimized_plan = await self._optimize_plan_based_on_history(
                context, performance_analysis
            )

            return optimized_plan

        # 注册策略
        self.planning_strategies["sequential"] = sequential_strategy
        self.planning_strategies["parallel"] = parallel_strategy
        self.planning_strategies["dependency_aware"] = dependency_aware_strategy
        self.planning_strategies["llm_optimized"] = llm_optimized_strategy
        self.planning_strategies["iterative_refinement"] = iterative_refinement_strategy

    async def generate_plan(self, context: PlanningContext) -> ExecutionPlan:
        """生成执行计划"""

        # 1. 选择最适合的规划策略
        strategy = self._select_planning_strategy(context)

        # 2. 使用选定策略生成计划
        if strategy in self.planning_strategies:
            plan = await self.planning_strategies[strategy](context)
        else:
            # 默认使用依赖感知策略
            plan = await self.planning_strategies["dependency_aware"](context)

        # 3. 验证和优化计划
        validated_plan = await self._validate_and_optimize_plan(plan, context)

        # 4. 记录计划
        self.plan_history[validated_plan.plan_id] = validated_plan

        print(f"📋 生成执行计划: {validated_plan.plan_id}")
        print(f"   策略: {validated_plan.strategy}")
        print(f"   Agent序列: {validated_plan.agent_sequence}")
        print(f"   并行任务组: {validated_plan.parallel_tasks}")
        print(f"   预估耗时: {validated_plan.estimated_duration}秒")

        return validated_plan

    def _select_planning_strategy(self, context: PlanningContext) -> str:
        """选择规划策略"""
        available_agents_count = len(context.available_agents)
        query_complexity = self._assess_query_complexity(context.query)
        iteration_number = context.current_iteration

        # 基于多个因素选择策略
        strategy_scores = {
            "sequential": 0,
            "parallel": 0,
            "dependency_aware": 0,
            "llm_optimized": 0,
            "iterative_refinement": 0
        }

        # 评分规则
        if available_agents_count == 1:
            strategy_scores["sequential"] += 10
        elif available_agents_count <= 3:
            strategy_scores["parallel"] += 8
            strategy_scores["dependency_aware"] += 6
        else:
            strategy_scores["dependency_aware"] += 8
            strategy_scores["llm_optimized"] += 7

        if query_complexity == "high":
            strategy_scores["dependency_aware"] += 5
            strategy_scores["llm_optimized"] += 6
        elif query_complexity == "medium":
            strategy_scores["parallel"] += 4
            strategy_scores["dependency_aware"] += 5

        if iteration_number > 1 and context.previous_plans:
            strategy_scores["iterative_refinement"] += 10

        # 选择得分最高的策略
        best_strategy = max(strategy_scores.items(), key=lambda x: x[1])[0]

        print(f"🎯 选择规划策略: {best_strategy} (得分: {strategy_scores[best_strategy]})")
        return best_strategy

    def _assess_query_complexity(self, query: str) -> str:
        """评估查询复杂度"""
        complexity_indicators = {
            "high": ["比较", "多个", "不同", "综合", "全面", "详细", "复杂"],
            "medium": ["规划", "建议", "分析", "查询", "了解"],
            "low": ["简单", "基本", "今天", "现在"]
        }

        score = 0
        for level, indicators in complexity_indicators.items():
            for indicator in indicators:
                if indicator in query:
                    if level == "high":
                        score += 3
                    elif level == "medium":
                        score += 2
                    else:
                        score += 1

        if score >= 5:
            return "high"
        elif score >= 3:
            return "medium"
        else:
            return "low"

    def _analyze_dependencies(self, context: PlanningContext) -> Dict[str, List[str]]:
        """分析任务间依赖关系"""
        dependencies = {}
        agent_capabilities = context.agent_capabilities

        # 简化的依赖分析逻辑
        # 假设预算分析可能依赖交通和天气信息
        if "预算分析师" in context.available_agents:
            dependencies["预算分析师"] = []
            if "交通规划师" in context.available_agents:
                dependencies["预算分析师"].append("交通规划师")
            if "天气专家" in context.available_agents:
                dependencies["预算分析师"].append("天气专家")

        # 交通规划可能依赖目的地信息（从天气Agent获取）
        if "交通规划师" in context.available_agents and "天气专家" in context.available_agents:
            dependencies["交通规划师"] = ["天气专家"]

        return dependencies

    def _build_dependency_sequence(self, dependencies: Dict[str, List[str]], available_agents: List[str]) -> List[str]:
        """构建考虑依赖关系的执行序列"""
        from collections import deque

        # 计算入度
        in_degree = {agent: 0 for agent in available_agents}
        for agent, deps in dependencies.items():
            if agent in available_agents:
                for dep in deps:
                    if dep in available_agents:
                        in_degree[agent] += 1

        # 拓扑排序
        queue = deque([agent for agent in available_agents if in_degree[agent] == 0])
        sequence = []

        while queue:
            current = queue.popleft()
            sequence.append(current)

            # 更新依赖当前Agent的其他Agent的入度
            for agent, deps in dependencies.items():
                if current in deps and agent in available_agents:
                    in_degree[agent] -= 1
                    if in_degree[agent] == 0:
                        queue.append(agent)

        # 如果还有剩余Agent（存在环），按原始顺序添加
        remaining = [agent for agent in available_agents if agent not in sequence]
        sequence.extend(remaining)

        return sequence

    def _group_parallel_tasks(self, sequence: List[str], dependencies: Dict[str, List[str]]) -> List[List[str]]:
        """分组可以并行执行的任务"""
        parallel_groups = []
        current_group = []

        for agent in sequence:
            # 检查当前Agent是否可以与现有组中的Agent并行执行
            can_parallelize = True

            for group_agent in current_group:
                # 如果存在依赖关系，不能并行
                if (agent in dependencies and group_agent in dependencies[agent]) or \
                        (group_agent in dependencies and agent in dependencies[group_agent]):
                    can_parallelize = False
                    break

            if can_parallelize:
                current_group.append(agent)
            else:
                if current_group:
                    parallel_groups.append(current_group)
                current_group = [agent]

        if current_group:
            parallel_groups.append(current_group)

        return parallel_groups

    def _estimate_duration(self, sequence: List[str], dependencies: Dict[str, List[str]]) -> float:
        """预估执行时间"""
        base_time_per_agent = 8.0  # 每个Agent基础执行时间
        parallel_efficiency = 0.7  # 并行效率系数

        parallel_groups = self._group_parallel_tasks(sequence, dependencies)

        total_time = 0.0
        for group in parallel_groups:
            group_time = base_time_per_agent * (1 + 0.2 * (len(group) - 1))  # 组内轻微开销
            total_time += group_time * parallel_efficiency

        return max(total_time, 5.0)  # 最少5秒

    def _build_llm_planning_prompt(self, context: PlanningContext) -> str:
        """构建LLM规划提示"""
        agent_descriptions = []
        for agent_name in context.available_agents:
            capabilities = context.agent_capabilities.get(agent_name, [])
            capability_descs = [cap.get('description', '未知能力') for cap in capabilities]
            agent_descriptions.append(f"- {agent_name}: {', '.join(capability_descs)}")

        return f"""
用户查询: {context.query}

可用Agent列表:
{chr(10).join(agent_descriptions)}

对话历史摘要:
{json.dumps(context.conversation_history[-3:], ensure_ascii=False, default=str)}

当前迭代: {context.current_iteration}

请制定一个高效的多Agent执行计划，考虑以下因素:
1. 任务依赖关系
2. 执行效率优化
3. 资源合理分配
4. 预期输出质量

请以JSON格式返回计划，包括以下字段:
- strategy: 策略名称
- agent_sequence: Agent执行序列
- parallel_tasks: 并行执行的任务组
- expected_outputs: 每个Agent的预期输出
- priority: 优先级 (critical/high/medium/low)
- estimated_duration: 预估执行时间(秒)
- reasoning: 规划理由
"""

    def _parse_llm_plan(self, plan_data: Dict[str, Any], context: PlanningContext) -> ExecutionPlan:
        """解析LLM生成的计划"""
        plan_id = f"plan_llm_{len(self.plan_history) + 1}"

        # 映射优先级
        priority_map = {
            "critical": PlanPriority.CRITICAL,
            "high": PlanPriority.HIGH,
            "medium": PlanPriority.MEDIUM,
            "low": PlanPriority.LOW
        }

        priority = priority_map.get(plan_data.get("priority", "medium"), PlanPriority.MEDIUM)

        return ExecutionPlan(
            plan_id=plan_id,
            strategy=plan_data.get("strategy", "llm_optimized"),
            agent_sequence=plan_data.get("agent_sequence", context.available_agents),
            parallel_tasks=plan_data.get("parallel_tasks", [context.available_agents]),
            expected_outputs=plan_data.get("expected_outputs", {}),
            priority=priority,
            estimated_duration=plan_data.get("estimated_duration", 30.0),
            dependencies=[],
            context_requirements={"query": context.query, "llm_reasoning": plan_data.get("reasoning", "")},
            created_at=asyncio.get_event_loop().time()
        )

    def _analyze_historical_performance(self, previous_plans: List[ExecutionPlan]) -> Dict[str, Any]:
        """分析历史执行性能"""
        performance_data = {
            "agent_performance": {},
            "strategy_performance": {},
            "common_bottlenecks": []
        }

        for plan in previous_plans:
            # 分析策略性能
            strategy = plan.strategy
            if strategy not in performance_data["strategy_performance"]:
                performance_data["strategy_performance"][strategy] = {
                    "count": 0,
                    "total_duration": 0,
                    "success_rate": 0
                }

            # 分析Agent性能（需要实际执行数据，这里简化）
            for agent in plan.agent_sequence:
                if agent not in performance_data["agent_performance"]:
                    performance_data["agent_performance"][agent] = {
                        "execution_count": 0,
                        "average_time": 0,
                        "reliability": 1.0
                    }

        return performance_data

    async def _optimize_plan_based_on_history(self, context: PlanningContext,
                                              performance_data: Dict[str, Any]) -> ExecutionPlan:
        """基于历史数据优化计划"""

        # 使用依赖感知策略作为基础
        base_plan = await self.planning_strategies["dependency_aware"](context)

        # 基于性能数据优化执行顺序
        optimized_sequence = self._optimize_agent_sequence(
            base_plan.agent_sequence,
            performance_data["agent_performance"]
        )

        # 更新计划
        base_plan.agent_sequence = optimized_sequence
        base_plan.parallel_tasks = self._group_parallel_tasks(
            optimized_sequence,
            self._analyze_dependencies(context)
        )
        base_plan.strategy = "iterative_refinement"

        return base_plan

    def _optimize_agent_sequence(self, sequence: List[str], performance_data: Dict[str, Any]) -> List[str]:
        """优化Agent执行顺序"""

        # 根据性能数据重新排序：执行时间短的优先
        def get_agent_performance_score(agent: str) -> float:
            perf = performance_data.get(agent, {})
            avg_time = perf.get("average_time", 10.0)  # 默认10秒
            reliability = perf.get("reliability", 1.0)
            return avg_time * (1.0 / reliability)  # 时间越短、可靠性越高，得分越低（优先）

        return sorted(sequence, key=get_agent_performance_score)

    async def _validate_and_optimize_plan(self, plan: ExecutionPlan, context: PlanningContext) -> ExecutionPlan:
        """验证和优化计划"""

        # 验证Agent可用性
        valid_agents = []
        for agent in plan.agent_sequence:
            if agent in context.available_agents:
                valid_agents.append(agent)
            else:
                print(f"⚠️  计划中的Agent不可用: {agent}")

        # 更新计划中的Agent序列
        plan.agent_sequence = valid_agents

        # 重新计算并行任务组
        dependencies = self._analyze_dependencies(context)
        plan.parallel_tasks = self._group_parallel_tasks(valid_agents, dependencies)

        # 重新估算执行时间
        plan.estimated_duration = self._estimate_duration(valid_agents, dependencies)

        return plan

    def register_strategy(self, name: str, strategy_func: Callable):
        """注册自定义规划策略"""
        self.planning_strategies[name] = strategy_func
        print(f"✅ 注册规划策略: {name}")

    def update_agent_performance(self, agent_name: str, execution_time: float, success: bool = True):
        """更新Agent性能数据"""
        stats = self.agent_performance_stats[agent_name]
        stats["total_executions"] += 1
        stats["successful_executions"] += 1 if success else 0
        stats["last_execution_time"] = execution_time

        # 更新平均执行时间
        if stats["total_executions"] > 0:
            total_time = stats["average_execution_time"] * (stats["total_executions"] - 1) + execution_time
            stats["average_execution_time"] = total_time / stats["total_executions"]

    def get_plan_history(self) -> Dict[str, ExecutionPlan]:
        """获取计划历史"""
        return self.plan_history.copy()