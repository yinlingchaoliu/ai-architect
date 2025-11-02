# agentdemo/src/core/iteration_controller.py
import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from ..models.agent_models import IterationStep, AgentResponse, AgentType, IterationPhase
from ..utils.logger_manager import logger_manager


class EnhancedIterationController:
    """增强的多轮迭代控制器 - 专注于超时处理和详细日志记录"""

    def __init__(self, max_iterations: int = 5):
        self.max_iterations = max_iterations
        self.current_iteration = 0
        self.iteration_history: List[IterationStep] = []
        
        # 增强的超时配置
        self.phase_timeouts = {
            "think": 30,
            "plan": 30,
            "action": 60,
            "next": 15
        }
        
        # 超时预警阈值（80%）
        self.timeout_warning_threshold = 0.8
        
        # 性能监控
        self.phase_execution_times = {
            "think": [],
            "plan": [],
            "action": [],
            "next": []
        }
        self.total_timeouts = 0
        self.total_retries = 0

    async def execute_iteration_cycle(self, query: str, context: Dict[str, Any],
                                      coordinator, available_agents: List[str]) -> Dict[str, Any]:
        """执行完整的迭代周期 - 增强的超时处理和日志记录"""

        self.current_iteration = 0
        final_results = {}
        execution_context = context or {}

        logger_manager.log_system_event(
            f"开始迭代周期 - 最大迭代次数: {self.max_iterations}",
            level="INFO",
            details={"query": query, "available_agents": available_agents}
        )

        while self.current_iteration < self.max_iterations:
            iteration_start_time = time.time()
            
            logger_manager.log_iteration_phase(
                IterationPhase.THINK,
                self.current_iteration + 1,
                f"开始迭代 {self.current_iteration + 1}/{self.max_iterations}",
                level="INFO"
            )

            try:
                # THINK 阶段 - 分析当前状态和需求
                think_result = await self._execute_phase_with_timeout(
                    "think", self._think_phase, self.phase_timeouts["think"],
                    query, execution_context, coordinator
                )
                self._record_step("think", think_result, phase=IterationPhase.THINK)

                # 检查是否可以直接完成
                if think_result.get("should_complete", False):
                    final_results = think_result
                    logger_manager.log_iteration_phase(
                        IterationPhase.THINK,
                        self.current_iteration + 1,
                        "Think阶段决定直接完成",
                        level="INFO"
                    )
                    break

                # PLAN 阶段 - 制定执行计划
                plan_result = await self._execute_phase_with_timeout(
                    "plan", self._plan_phase, self.phase_timeouts["plan"],
                    query, think_result, coordinator, available_agents
                )
                self._record_step("plan", plan_result, phase=IterationPhase.PLAN)

                # ACTION 阶段 - 执行计划
                action_result = await self._execute_phase_with_timeout(
                    "action", self._action_phase, self.phase_timeouts["action"],
                    plan_result, coordinator, execution_context
                )
                self._record_step("action", action_result, action_result.get("agent_responses"), phase=IterationPhase.ACTION)

                # NEXT 阶段 - 决定下一步
                next_result = await self._execute_phase_with_timeout(
                    "next", self._next_phase, self.phase_timeouts["next"],
                    query, action_result, coordinator
                )
                self._record_step("next", next_result, phase=IterationPhase.NEXT)

                # 更新上下文
                execution_context.update(action_result.get("updated_context", {}))

                # 检查迭代终止条件
                if next_result.get("should_terminate", False):
                    final_results = action_result
                    logger_manager.log_iteration_phase(
                        IterationPhase.NEXT,
                        self.current_iteration + 1,
                        "Next阶段决定终止迭代",
                        level="INFO"
                    )
                    break

            except Exception as e:
                iteration_time = time.time() - iteration_start_time
                logger_manager.log_iteration_phase(
                    IterationPhase.ACTION,  # 使用ACTION作为通用错误阶段
                    self.current_iteration + 1,
                    f"迭代失败: {e}",
                    level="ERROR",
                    execution_time=iteration_time
                )
                
                # 记录错误但继续下一轮迭代
                error_step = IterationStep(
                    state="error",
                    data={"error": str(e), "iteration": self.current_iteration + 1},
                    timestamp=asyncio.get_event_loop().time(),
                    execution_time=iteration_time
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
            logger_manager.log_system_event(
                "达到最大迭代次数，强制终止",
                level="WARNING"
            )

        total_iteration_time = time.time() - iteration_start_time
        
        logger_manager.log_system_event(
            f"迭代周期完成 - 总迭代次数: {self.current_iteration}, 总时间: {total_iteration_time:.2f}s",
            level="INFO",
            details={
                "total_iterations": self.current_iteration,
                "total_time": round(total_iteration_time, 2),
                "timeouts": self.total_timeouts,
                "retries": self.total_retries
            }
        )

        return {
            "final_result": final_results,
            "iteration_count": self.current_iteration + 1,
            "history": [step.to_dict() for step in self.iteration_history],
            "performance": {
                "total_timeouts": self.total_timeouts,
                "total_retries": self.total_retries,
                "phase_execution_times": self.phase_execution_times
            }
        }

    async def _execute_phase_with_timeout(self, phase_name: str, phase_func, timeout: int, *args):
        """执行阶段并处理超时 - 增强的超时处理"""
        phase_start_time = time.time()
        timeout_warning_issued = False
        
        try:
            # 设置超时
            result = await asyncio.wait_for(
                phase_func(*args),
                timeout=timeout
            )
            
            execution_time = time.time() - phase_start_time
            
            # 检查是否接近超时（预警）
            if execution_time > timeout * self.timeout_warning_threshold and not timeout_warning_issued:
                logger_manager.log_iteration_phase(
                    getattr(IterationPhase, phase_name.upper()),
                    self.current_iteration + 1,
                    f"{phase_name}阶段接近超时 - 当前执行时间: {execution_time:.2f}s",
                    level="WARNING",
                    execution_time=execution_time,
                    timeout_warning=True
                )
                timeout_warning_issued = True
            
            # 记录执行时间
            self.phase_execution_times[phase_name].append(execution_time)
            
            logger_manager.log_iteration_phase(
                getattr(IterationPhase, phase_name.upper()),
                self.current_iteration + 1,
                f"{phase_name}阶段完成 - 执行时间: {execution_time:.2f}s",
                level="INFO",
                execution_time=execution_time
            )
            
            return result

        except asyncio.TimeoutError:
            execution_time = time.time() - phase_start_time
            self.total_timeouts += 1
            
            logger_manager.log_timeout_event(
                f"iteration.{phase_name}",
                f"{phase_name}阶段",
                timeout,
                retry_count=0
            )
            
            # 返回默认响应
            default_result = self._get_default_phase_response(phase_name, *args)
            default_result["timeout_occurred"] = True
            default_result["execution_time"] = execution_time
            
            logger_manager.log_iteration_phase(
                getattr(IterationPhase, phase_name.upper()),
                self.current_iteration + 1,
                f"{phase_name}阶段超时 - 使用默认响应",
                level="WARNING",
                execution_time=execution_time,
                timeout_warning=True
            )
            
            return default_result

    async def _think_phase(self, query: str, context: Dict, coordinator) -> Dict[str, Any]:
        """思考阶段 - 分析意图和当前状态"""
        try:
            # 确保上下文可序列化
            serializable_context = self._make_serializable(context)
            
            think_prompt = f"""
当前用户查询: {query}
历史上下文: {json.dumps(serializable_context, ensure_ascii=False, default=str)}
当前迭代: {self.current_iteration + 1}

请分析：
1. 用户的核心需求是什么？
2. 当前已经获得了哪些信息？
3. 还需要获取哪些关键信息？
4. 是否可以直接回答用户问题？

请以JSON格式返回分析结果，包括：
- core_requirements: 核心需求列表
- acquired_info: 已获得信息
- missing_info: 缺失的关键信息
- confidence_level: 当前置信度(0-1)
- should_complete: 是否可以直接完成
- reasoning: 推理过程

请确保返回有效的JSON格式，不要包含其他文本。
"""

            messages = [
                {"role": "system", "content": "你是一个深思熟虑的分析专家，能够准确评估当前状况和下一步需求。"},
                {"role": "user", "content": think_prompt}
            ]

            analysis_text = await coordinator._call_llm(messages, timeout=self.phase_timeouts["think"])

            try:
                # 清理响应文本，确保是有效的JSON
                cleaned_text = analysis_text.strip()
                if cleaned_text.startswith('```json'):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.endswith('```'):
                    cleaned_text = cleaned_text[:-3]
                cleaned_text = cleaned_text.strip()
                
                result = json.loads(cleaned_text)
                # 确保结果可序列化
                return self._make_serializable(result)
            except Exception as e:
                logger_manager.log_iteration_phase(
                    IterationPhase.THINK,
                    self.current_iteration + 1,
                    f"Think阶段JSON解析失败: {e}",
                    level="WARNING"
                )
                return self._get_default_think_response(query, serializable_context)

        except Exception as e:
            logger_manager.log_iteration_phase(
                IterationPhase.THINK,
                self.current_iteration + 1,
                f"Think阶段执行异常: {e}",
                level="ERROR"
            )
            return self._get_default_think_response(query, context)

    async def _plan_phase(self, query: str, think_result: Dict, coordinator, available_agents: List[str]) -> Dict[str, Any]:
        """规划阶段 - 制定执行计划"""
        try:
            missing_info = think_result.get("missing_info", [])
            current_context = think_result.get("acquired_info", {})

            plan_prompt = f"""
用户查询: {query}
缺失信息: {missing_info}
可用Agent: {available_agents}
当前上下文: {json.dumps(current_context, ensure_ascii=False, default=str)}

请制定一个详细的执行计划来获取缺失信息，以JSON格式返回：
- required_agents: 需要调用的Agent列表
- execution_sequence: 执行序列（并行/串行）
- expected_outputs: 期望从每个Agent获得的输出
- strategy: 执行策略
- iteration_goal: 本轮迭代的目标

请确保返回有效的JSON格式，不要包含其他文本。
"""

            messages = [
                {"role": "system", "content": "你是一个专业的任务规划师，能够制定高效的信息收集和执行计划。"},
                {"role": "user", "content": plan_prompt}
            ]

            plan_text = await coordinator._call_llm(messages, timeout=self.phase_timeouts["plan"])

            try:
                # 清理响应文本，确保是有效的JSON
                cleaned_text = plan_text.strip()
                if cleaned_text.startswith('```json'):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.endswith('```'):
                    cleaned_text = cleaned_text[:-3]
                cleaned_text = cleaned_text.strip()
                
                plan = json.loads(cleaned_text)
                # 确保计划中包含必要的字段
                plan.setdefault("required_agents", available_agents)
                plan.setdefault("execution_sequence", [available_agents])
                plan.setdefault("expected_outputs", {})
                plan.setdefault("strategy", "parallel")
                plan.setdefault("iteration_goal", "收集缺失信息")
                # 确保结果可序列化
                return self._make_serializable(plan)
            except Exception as e:
                logger_manager.log_iteration_phase(
                    IterationPhase.PLAN,
                    self.current_iteration + 1,
                    f"Plan阶段JSON解析失败: {e}",
                    level="WARNING"
                )
                return self._get_default_plan_response(available_agents)

        except Exception as e:
            logger_manager.log_iteration_phase(
                IterationPhase.PLAN,
                self.current_iteration + 1,
                f"Plan阶段执行异常: {e}",
                level="ERROR"
            )
            return self._get_default_plan_response(available_agents)

    async def _action_phase(self, plan: Dict, coordinator, context: Dict) -> Dict[str, Any]:
        """执行阶段 - 调用Agent执行计划"""
        required_agents = plan.get("required_agents", [])
        execution_sequence = plan.get("execution_sequence", [required_agents])

        agent_responses = {}
        updated_context = context.copy()
        max_retries = 2  # 设置最大重试次数

        logger_manager.log_iteration_phase(
            IterationPhase.ACTION,
            self.current_iteration + 1,
            f"开始执行阶段 - 需要Agent: {required_agents}",
            level="INFO"
        )

        # 按序列执行
        for task_group in execution_sequence:
            tasks = []
            agent_mapping = []  # 保存agent名称和实例的映射
            
            for agent_name in task_group:
                if agent_name in coordinator.agent_registry:
                    agent = coordinator.agent_registry[agent_name]
                    # 使用agent自身的超时设置，如果没有则使用action阶段的超时
                    agent_timeout = getattr(agent, 'timeout', self.phase_timeouts["action"])
                    # 为每个agent创建任务，使用单独的超时时间
                    task = asyncio.create_task(
                        self._execute_agent_with_retry(agent, context.get("last_query", ""), 
                                                     updated_context, agent_timeout, max_retries)
                    )
                    tasks.append(task)
                    agent_mapping.append((agent_name, agent))

            # 并行执行任务组
            if tasks:
                try:
                    # 给整个任务组一个合理的超时（比单个agent超时稍长）
                    group_timeout = min(self.phase_timeouts["action"] + 10, 90)  # 最大90秒
                    task_results = await asyncio.wait_for(
                        asyncio.gather(*tasks, return_exceptions=True),
                        timeout=group_timeout
                    )
                    
                    for (agent_name, _), result in zip(agent_mapping, task_results):
                        if isinstance(result, AgentResponse):
                            agent_responses[agent_name] = result
                            # 更新上下文
                            updated_context[agent_name] = self._make_serializable(result.data)
                        elif isinstance(result, Exception):
                            logger_manager.log_agent_operation(
                                agent_name,
                                f"执行错误: {result}",
                                level="ERROR"
                            )
                            agent_responses[agent_name] = AgentResponse(
                                agent_type=AgentType.CUSTOM,
                                content=f"执行错误: {str(result)}",
                                data={},
                                confidence=0.0
                            )
                        else:
                            # 处理重试后仍然失败的情况
                            logger_manager.log_agent_operation(
                                agent_name,
                                f"执行失败，所有重试都已耗尽",
                                level="ERROR"
                            )
                            agent_responses[agent_name] = AgentResponse(
                                agent_type=AgentType.CUSTOM,
                                content=f"执行超时，已重试{max_retries}次后仍失败",
                                data={"error": "max_retries_exceeded"},
                                confidence=0.0
                            )
                except asyncio.TimeoutError:
                    logger_manager.log_timeout_event(
                        "action.task_group",
                        "任务组执行",
                        group_timeout,
                        retry_count=0
                    )
                    # 为超时的任务组创建默认响应
                    for agent_name, _ in agent_mapping:
                        agent_responses[agent_name] = AgentResponse(
                            agent_type=AgentType.CUSTOM,
                            content=f"执行超时，任务组处理时间过长",
                            data={"error": "group_timeout"},
                            confidence=0.0
                        )
                except Exception as e:
                    logger_manager.log_iteration_phase(
                        IterationPhase.ACTION,
                        self.current_iteration + 1,
                        f"任务组执行失败: {e}",
                        level="ERROR"
                    )

        logger_manager.log_iteration_phase(
            IterationPhase.ACTION,
            self.current_iteration + 1,
            f"执行阶段完成 - 成功Agent: {len(agent_responses)}/{len(required_agents)}",
            level="INFO"
        )

        return {
            "agent_responses": agent_responses,
            "updated_context": updated_context,
            "plan_executed": plan,
            "execution_status": "partial" if not agent_responses else "complete"
        }
    
    async def _execute_agent_with_retry(self, agent, query, context, timeout, max_retries):
        """带重试机制的agent执行方法"""
        retries = 0
        last_error = None
        
        while retries <= max_retries:
            try:
                if retries > 0:
                    logger_manager.log_retry_attempt(
                        agent.name,
                        "Agent执行",
                        retries,
                        max_retries,
                        reason=str(last_error) if last_error else "首次尝试"
                    )
                    # 重试时使用稍微更长的超时时间
                    retry_timeout = min(timeout + (retries * 5), timeout * 2)
                else:
                    retry_timeout = timeout
                
                # 执行agent请求并设置超时
                response = await asyncio.wait_for(
                    agent.process_request(query, context),
                    timeout=retry_timeout
                )
                return response
                
            except asyncio.TimeoutError as e:
                last_error = e
                retries += 1
                self.total_retries += 1
                # 重试前短暂等待
                if retries <= max_retries:
                    await asyncio.sleep(1)
            except Exception as e:
                # 非超时错误，直接返回
                logger_manager.log_agent_operation(
                    agent.name,
                    f"执行异常: {e}",
                    level="ERROR"
                )
                raise
        
        # 所有重试都失败了
        raise last_error

    async def _next_phase(self, query: str, action_result: Dict, coordinator) -> Dict[str, Any]:
        """下一步决策阶段"""
        try:
            agent_responses = action_result.get("agent_responses", {})
            updated_context = action_result.get("updated_context", {})

            next_prompt = f"""
原始查询: {query}
当前收集到的信息: {json.dumps(updated_context, ensure_ascii=False, default=str)}
Agent执行结果: {json.dumps({k: v.content for k, v in agent_responses.items()}, ensure_ascii=False)}

请评估：
1. 当前信息是否足够回答用户问题？
2. 是否需要继续迭代收集更多信息？
3. 下一轮迭代的重点应该是什么？

以JSON格式返回：
- should_terminate: 是否终止迭代
- confidence_score: 当前整体置信度(0-1)
- next_focus: 下一轮迭代重点
- reasoning: 决策理由

请确保返回有效的JSON格式，不要包含其他文本。
"""

            messages = [
                {"role": "system", "content": "你是一个决策专家，能够基于当前信息质量决定是否继续迭代。"},
                {"role": "user", "content": next_prompt}
            ]

            next_text = await coordinator._call_llm(messages, timeout=self.phase_timeouts["next"])

            try:
                # 清理响应文本，确保是有效的JSON
                cleaned_text = next_text.strip()
                if cleaned_text.startswith('```json'):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.endswith('```'):
                    cleaned_text = cleaned_text[:-3]
                cleaned_text = cleaned_text.strip()
                
                result = json.loads(cleaned_text)
                # 确保结果可序列化
                return self._make_serializable(result)
            except Exception as e:
                logger_manager.log_iteration_phase(
                    IterationPhase.NEXT,
                    self.current_iteration + 1,
                    f"Next阶段JSON解析失败: {e}",
                    level="WARNING"
                )
                return self._get_default_next_response(agent_responses)

        except Exception as e:
            logger_manager.log_iteration_phase(
                IterationPhase.NEXT,
                self.current_iteration + 1,
                f"Next阶段执行异常: {e}",
                level="ERROR"
            )
            return self._get_default_next_response(agent_responses)

    def _record_step(self, state: str, data: Dict, agent_responses: Dict = None, phase: IterationPhase = None):
        """记录迭代步骤"""
        step = IterationStep(
            state=state,
            data=data,
            timestamp=asyncio.get_event_loop().time(),
            agent_responses=agent_responses,
            phase=phase
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
            logger_manager.log_system_event(
                "发现协程对象，转换为字符串表示",
                level="WARNING"
            )
            return f"<coroutine object at {hex(id(data))}>"
        
        # 处理其他可能不可序列化的对象
        elif not isinstance(data, (str, int, float, bool, list, dict)):
            try:
                # 尝试转换为字符串
                return str(data)
            except:
                # 如果转换失败，返回类型信息
                return f"<object {type(data).__name__}>"
        
        # 处理基本类型
        return data

    def _get_default_phase_response(self, phase_name: str, *args) -> Dict[str, Any]:
        """获取阶段的默认响应"""
        if phase_name == "think":
            return self._get_default_think_response(args[0], args[1])
        elif phase_name == "plan":
            return self._get_default_plan_response(args[2])
        elif phase_name == "action":
            return self._get_default_action_response()
        elif phase_name == "next":
            return self._get_default_next_response({})
        else:
            return {"error": f"未知阶段: {phase_name}"}

    def _get_default_think_response(self, query: str, context: Dict) -> Dict[str, Any]:
        """获取Think阶段的默认响应"""
        return {
            "core_requirements": [query],
            "acquired_info": self._make_serializable(context),
            "missing_info": ["基础信息"],
            "confidence_level": 0.2,
            "should_complete": False,
            "reasoning": "分析超时，需要收集基础信息"
        }

    def _get_default_plan_response(self, available_agents: List[str]) -> Dict[str, Any]:
        """获取Plan阶段的默认响应"""
        return {
            "required_agents": available_agents,
            "execution_sequence": [available_agents],
            "expected_outputs": {},
            "strategy": "parallel",
            "iteration_goal": "超时后备计划"
        }

    def _get_default_action_response(self) -> Dict[str, Any]:
        """获取Action阶段的默认响应"""
        return {
            "agent_responses": {},
            "updated_context": {},
            "plan_executed": {},
            "execution_status": "timeout"
        }

    def _get_default_next_response(self, agent_responses: Dict) -> Dict[str, Any]:
        """获取Next阶段的默认响应"""
        return {
            "should_terminate": len(agent_responses) > 0,
            "confidence_score": 0.5,
            "next_focus": "超时终止",
            "reasoning": "决策超时，终止迭代"
        }

    def set_phase_timeout(self, phase: str, timeout: int):
        """设置阶段超时时间"""
        if phase in self.phase_timeouts:
            self.phase_timeouts[phase] = timeout
            logger_manager.log_system_event(
                f"设置 {phase} 阶段超时为 {timeout} 秒",
                level="INFO"
            )

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return {
            "total_iterations": self.current_iteration,
            "total_timeouts": self.total_timeouts,
            "total_retries": self.total_retries,
            "phase_execution_times": self.phase_execution_times,
            "average_phase_times": {
                phase: sum(times) / len(times) if times else 0
                for phase, times in self.phase_execution_times.items()
            }
        }
