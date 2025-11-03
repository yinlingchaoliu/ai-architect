# multi_agent_system/core/iteration_controller.py
import asyncio
import json
import time
from typing import Dict, List, Any, Optional

from ..models.agent_models import IterationStep, AgentResponse, AgentType
from ..prompt.constants import  THINK_PROMPT, think_prompt, plan_prompt,PLAN_PROMPT,next_prompt,NEXT_PROMPT


class IterationController:
    """多轮迭代控制器"""

    def __init__(self, max_iterations: int = 5):
        self.max_iterations = max_iterations
        self.current_iteration = 0
        self.iteration_history: List[IterationStep] = []
        self.phase_timeouts = {
            "think": 3000,
            "plan": 3000,
            "action": 6000,
            "next": 1500
        }

    async def execute_iteration_cycle(self, query: str, context: Dict[str, Any],
                                      coordinator, available_agents: List[str]) -> Dict[str, Any]:
        """执行完整的迭代周期"""
        self.coordinator = coordinator
        self.current_iteration = 0
        final_results = {}
        execution_context = context or {}

        while self.current_iteration < self.max_iterations:
            print(f"🔄 迭代 {self.current_iteration + 1}/{self.max_iterations}")

            try:
                # THINK 阶段 - 分析当前状态和需求
                coordinator.set_step("think")
                think_result = await self._think_phase(query, execution_context, coordinator)
                self._record_step("think", think_result)

                # 检查是否可以直接完成
                if think_result.get("should_complete", False):
                    final_results = think_result
                    break

                # PLAN 阶段 - 制定执行计划
                coordinator.set_step("plan")
                plan_result = await self._plan_phase(query, think_result, coordinator, available_agents)
                self._record_step("plan", plan_result)

                # ACTION 阶段 - 执行计划
                coordinator.set_step("action")
                action_result = await self._action_phase(plan_result, coordinator, execution_context)
                self._record_step("action", action_result, action_result.get("agent_responses"))

                # NEXT 阶段 - 决定下一步
                coordinator.set_step("next")
                next_result = await self._next_phase(query, action_result, coordinator)
                self._record_step("next", next_result)

                # 更新上下文
                execution_context.update(action_result.get("updated_context", {}))

                # 检查迭代终止条件
                if next_result.get("should_terminate", False):
                    final_results = action_result
                    break

            except Exception as e:
                print(f"❌ 迭代 {self.current_iteration + 1} 失败: {e}")
                # 记录错误但继续下一轮迭代
                error_step = IterationStep(
                    state="error",
                    data={"error": str(e), "iteration": self.current_iteration + 1},
                    timestamp=asyncio.get_event_loop().time()
                )
                self.iteration_history.append(error_step)

                # 如果是最后一次迭代，返回错误信息
                if self.current_iteration == self.max_iterations - 1:
                    final_results = {
                        "error": str(e),
                        "agent_responses": {},
                        "updated_context": execution_context
                    }
                    break

            self.current_iteration += 1

        if self.current_iteration >= self.max_iterations:
            print("⚠️  达到最大迭代次数，强制终止")

        return {
            "final_result": final_results,
            "iteration_count": self.current_iteration + 1,
            "history": [step.to_dict() for step in self.iteration_history]
        }

    async def _think_phase(self, query: str, context: Dict, coordinator) -> Dict[str, Any]:
        """思考阶段 - 分析意图和当前状态"""
        try:

            prompt = think_prompt(
                query=query,
                context=json.dumps(context, ensure_ascii=False, default=str),
                iteration_count=self.current_iteration + 1
            )

            messages = [
                {"role": "system", "content": THINK_PROMPT},
                {"role": "user", "content": prompt}
            ]

            analysis_text = await asyncio.wait_for(
                coordinator._call_llm(messages, timeout=self.phase_timeouts["think"]),
                timeout=self.phase_timeouts["think"] + 5
            )

            try:
                result = json.loads(analysis_text)
                # 确保结果可序列化
                return self._make_serializable(result)
            except Exception:
                return {
                    "core_requirements": [query],
                    "acquired_info": self._make_serializable(context),
                    "missing_info": ["更多详细信息"],
                    "confidence_level": 0.3,
                    "should_complete": False,
                    "reasoning": "需要进一步收集信息"
                }

        except asyncio.TimeoutError:
            print("⏰ Think 阶段超时，使用默认分析")
            return {
                "core_requirements": [query],
                "acquired_info": context,
                "missing_info": ["基础信息"],
                "confidence_level": 0.2,
                "should_complete": False,
                "reasoning": "分析超时，需要收集基础信息"
            }

    async def _plan_phase(self, query: str, think_result: Dict, coordinator, available_agents: List[str]) -> Dict[
        str, Any]:
        """规划阶段 - 制定执行计划"""
        try:
            missing_info = think_result.get("missing_info", [])
            current_context = think_result.get("acquired_info", {})

            prompt = plan_prompt(
                query=query,
                context=json.dumps(current_context, ensure_ascii=False, default=str),
                missing_info=missing_info,
                available_agents=available_agents
            )

            messages = [
                {"role": "system", "content": PLAN_PROMPT},
                {"role": "user", "content": prompt}
            ]

            plan_text = await asyncio.wait_for(
                coordinator._call_llm(messages, timeout=self.phase_timeouts["plan"]),
                timeout=self.phase_timeouts["plan"] + 5
            )

            try:
                plan = json.loads(plan_text)
                # 确保计划中包含必要的字段
                plan.setdefault("required_agents", available_agents)
                plan.setdefault("execution_sequence", [available_agents])
                plan.setdefault("expected_outputs", {})
                plan.setdefault("strategy", "parallel")
                plan.setdefault("iteration_goal", "收集缺失信息")
                # 确保结果可序列化
                return self._make_serializable(plan)
            except Exception:
                return {
                    "required_agents": available_agents,
                    "execution_sequence": [available_agents],
                    "expected_outputs": {},
                    "strategy": "parallel",
                    "iteration_goal": "基础信息收集"
                }

        except asyncio.TimeoutError:
            print("⏰ Plan 阶段超时，使用默认计划")
            return {
                "required_agents": available_agents,
                "execution_sequence": [available_agents],
                "expected_outputs": {},
                "strategy": "parallel",
                "iteration_goal": "超时后备计划"
            }

    async def _action_phase(self, plan: Dict, coordinator, context: Dict) -> Dict[str, Any]:
        """执行阶段 - 调用Agent执行计划"""
        required_agents = plan.get("required_agents", [])
        expected_outputs = plan.get("expected_outputs", {})
        execution_sequence = plan.get("execution_sequence", [required_agents])

        agent_responses = {}
        updated_context = context.copy()

        # 按序列执行
        tasks = []
        for agent_name in required_agents:
            if agent_name in coordinator.agent_registry:
                agent = coordinator.agent_registry[agent_name]
                prompt = expected_outputs[agent_name]
                # 为每个Agent任务设置超时
                task = asyncio.wait_for(
                    agent.process_request(prompt, updated_context),
                    timeout=self.phase_timeouts["action"]
                )
                tasks.append(task)

        # 并行执行任务组
        if tasks:
            try:
                task_results = await asyncio.gather(*tasks, return_exceptions=True)
                for agent_name, result in zip(required_agents, task_results):
                    if isinstance(result, AgentResponse):
                        agent_responses[agent_name] = result
                        # 更新上下文并确保数据可序列化
                        updated_context[agent_name] = self._make_serializable(result.data)
                    elif isinstance(result, Exception):
                        print(f"❌ Agent {agent_name} 执行错误: {result}")
                        agent_responses[agent_name] = AgentResponse(
                            agent_type=AgentType.CUSTOM,
                            content=f"执行错误: {str(result)}",
                            data={},
                            confidence=0.0
                        )
            except Exception as e:
                print(f"❌ 任务组执行失败: {e}")

        return {
            "agent_responses": agent_responses,
            "updated_context": updated_context,
            "plan_executed": plan
        }

    async def _next_phase(self, query: str, action_result: Dict, coordinator) -> Dict[str, Any]:
        """下一步决策阶段"""
        try:
            agent_responses = action_result.get("agent_responses", {})
            updated_context = action_result.get("updated_context", {})

            context = json.dumps(updated_context, ensure_ascii=False, default=str)
            agent_responses_context = json.dumps({k: v.content for k, v in agent_responses.items()}, ensure_ascii=False)

            prompt = next_prompt(query, context, agent_responses_context)
            messages = [
                {"role": "system", "content": NEXT_PROMPT},
                {"role": "user", "content": prompt}
            ]

            next_text = await asyncio.wait_for(
                coordinator._call_llm(messages, timeout=self.phase_timeouts["next"]),
                timeout=self.phase_timeouts["next"] + 5
            )

            try:
                result = json.loads(next_text)
                # 确保结果可序列化
                return self._make_serializable(result)
            except Exception:
                return {
                    "should_terminate": len(agent_responses) > 0,
                    "confidence_score": 0.7,
                    "next_focus": "整合现有信息",
                    "reasoning": "已收集到基础信息"
                }

        except asyncio.TimeoutError:
            print("⏰ Next 阶段超时，使用默认决策")
            return {
                "should_terminate": True,
                "confidence_score": 0.5,
                "next_focus": "超时终止",
                "reasoning": "决策超时，终止迭代"
            }

    def _record_step(self, state: str, data: Dict, agent_responses: Dict = None):
        """记录迭代步骤"""
        step = IterationStep(
            state=state,
            data=data,
            timestamp=asyncio.get_event_loop().time(),
            agent_responses=agent_responses
        )
        self.iteration_history.append(step)

    def _make_serializable(self, data):
        """确保数据可JSON序列化"""
        if data is None:
            return None
        
        # 处理字典
        if isinstance(data, dict):
            return {k: self._make_serializable(v) for k, v in data.items()}
        
        # 处理列表
        elif isinstance(data, list):
            return [self._make_serializable(item) for item in data]
        
        # 处理AgentResponse对象
        elif hasattr(data, 'to_dict') and callable(getattr(data, 'to_dict')):
            return data.to_dict()
        
        # 处理协程对象（转换为字符串）
        elif asyncio.iscoroutine(data):
            print(f"⚠️  发现协程对象，转换为字符串表示")
            return f"<coroutine object at {hex(id(data))}>"
        
        # 处理其他可能不可序列化的对象
        elif not isinstance(data, (str, int, float, bool, list, dict, type(None))):
            try:
                return str(data)
            except:
                return f"<object {type(data).__name__}>"
        
        return data

    def set_phase_timeout(self, phase: str, timeout: int):
        """设置阶段超时时间"""
        if phase in self.phase_timeouts:
            self.phase_timeouts[phase] = timeout
            print(f"⏰ 设置 {phase} 阶段超时为 {timeout} 秒")