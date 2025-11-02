# agentdemo/src/agents/coordinator_agent.py
import asyncio
import json
from typing import Dict, List, Any, Optional

from .base_agent import BaseAgent
from ..models.agent_models import AgentType, AgentResponse, AgentCapability
from ..utils.logger_manager import logger_manager


class CoordinatorAgent(BaseAgent):
    """协调器 Agent - 负责协调其他Agent的工作"""

    def __init__(self):
        super().__init__(AgentType.COORDINATOR, "协调器", "负责协调和管理其他Agent的工作")
        
        # 注册协调能力
        coordination_capability = AgentCapability(
            name="coordination",
            description="协调多个Agent的工作",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "用户查询"},
                    "available_agents": {"type": "array", "description": "可用Agent列表"},
                    "context": {"type": "object", "description": "执行上下文"}
                },
                "required": ["query", "available_agents"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "plan": {"type": "object"},
                    "reasoning": {"type": "string"}
                }
            }
        )
        
        self.register_capability(coordination_capability)

    async def process_request(self, query: str, context: Dict[str, Any] = None) -> AgentResponse:
        """处理协调请求"""
        logger_manager.log_agent_operation(
            self.name,
            f"开始处理协调请求: {query}",
            level="INFO"
        )
        
        try:
            # 分析查询并制定协调策略
            coordination_plan = await self._analyze_and_coordinate(query, context)
            
            # 生成响应
            content = await self._generate_response(coordination_plan, query)
            
            response = AgentResponse(
                agent_type=self.agent_type,
                content=content,
                data=coordination_plan,
                confidence=0.9
            )
            
            logger_manager.log_agent_operation(
                self.name,
                "协调请求处理完成",
                level="INFO"
            )
            
            return response
            
        except Exception as e:
            logger_manager.log_agent_operation(
                self.name,
                f"协调请求处理失败: {e}",
                level="ERROR"
            )
            
            # 返回错误响应
            return AgentResponse(
                agent_type=self.agent_type,
                content=f"协调处理失败: {e}",
                data={"error": str(e)},
                confidence=0.1
            )

    async def _analyze_and_coordinate(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """分析查询并制定协调策略"""
        # 使用LLM分析查询并制定协调计划
        analysis_prompt = f"""
用户查询: {query}
当前上下文: {json.dumps(context or {}, ensure_ascii=False, default=str)}

请分析这个查询并制定一个协调计划：
1. 识别查询中的关键需求
2. 确定需要哪些类型的Agent来处理
3. 制定执行顺序和策略
4. 预估可能的问题和解决方案

请以JSON格式返回分析结果，包括：
- key_requirements: 关键需求列表
- required_agent_types: 需要的Agent类型
- execution_strategy: 执行策略
- potential_issues: 潜在问题
- fallback_plan: 备用计划

请确保返回有效的JSON格式，不要包含其他文本。
"""

        messages = [
            {"role": "system", "content": "你是一个专业的协调专家，能够准确分析需求并制定高效的执行计划。"},
            {"role": "user", "content": analysis_prompt}
        ]

        analysis_text = await self._call_llm(messages, timeout=self.timeout)

        try:
            # 清理响应文本，确保是有效的JSON
            cleaned_text = analysis_text.strip()
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()
            
            coordination_plan = json.loads(cleaned_text)
            
            # 确保计划中包含必要的字段
            coordination_plan.setdefault("key_requirements", [])
            coordination_plan.setdefault("required_agent_types", [])
            coordination_plan.setdefault("execution_strategy", "sequential")
            coordination_plan.setdefault("potential_issues", [])
            coordination_plan.setdefault("fallback_plan", {})
            
            logger_manager.log_agent_operation(
                self.name,
                f"协调计划制定完成 - 需要Agent类型: {coordination_plan['required_agent_types']}",
                level="INFO"
            )
            
            return coordination_plan
            
        except Exception as e:
            logger_manager.log_agent_operation(
                self.name,
                f"协调计划解析失败: {e}",
                level="WARNING"
            )
            
            # 返回默认协调计划
            return {
                "key_requirements": [query],
                "required_agent_types": ["weather", "transport", "budget"],
                "execution_strategy": "parallel",
                "potential_issues": ["信息不足"],
                "fallback_plan": {"strategy": "basic_info_collection"}
            }

    async def _generate_response(self, coordination_plan: Dict[str, Any], query: str) -> str:
        """生成协调响应"""
        response_prompt = f"""
基于以下协调计划生成一个友好的响应：

用户查询: {query}
协调计划: {json.dumps(coordination_plan, ensure_ascii=False, default=str)}

请生成一个自然、友好的响应，告诉用户我们将如何处理他们的请求，包括：
1. 我们将要做什么
2. 需要哪些步骤
3. 预期的结果

请用中文回复，保持友好和专业。
"""

        messages = [
            {"role": "system", "content": "你是一个友好的助手，能够用自然语言解释复杂的协调计划。"},
            {"role": "user", "content": response_prompt}
        ]

        response_text = await self._call_llm(messages, timeout=self.timeout)
        
        # 如果响应为空或无效，使用默认响应
        if not response_text or not isinstance(response_text, str):
            response_text = f"我已经收到您的查询：'{query}'。我将协调相关专家为您提供帮助，包括分析需求、收集信息和制定解决方案。请稍等片刻，我会尽快为您提供详细答复。"
        
        return response_text

    async def evaluate_agent_responses(self, agent_responses: Dict[str, Any], original_query: str) -> Dict[str, Any]:
        """评估Agent响应并决定下一步行动"""
        logger_manager.log_agent_operation(
            self.name,
            "开始评估Agent响应",
            level="INFO"
        )
        
        try:
            evaluation_prompt = f"""
原始查询: {original_query}
Agent响应汇总: {json.dumps(agent_responses, ensure_ascii=False, default=str)}

请评估：
1. 当前收集的信息是否足够回答用户问题？
2. 哪些信息还需要补充？
3. 是否需要继续迭代？
4. 下一轮迭代的重点是什么？

以JSON格式返回评估结果：
- is_sufficient: 信息是否足够
- missing_information: 缺失的信息
- should_continue: 是否继续迭代
- next_focus: 下一轮迭代重点
- confidence: 当前置信度(0-1)
- reasoning: 评估理由

请确保返回有效的JSON格式，不要包含其他文本。
"""

            messages = [
                {"role": "system", "content": "你是一个专业的评估专家，能够准确评估信息完整性和决定下一步行动。"},
                {"role": "user", "content": evaluation_prompt}
            ]

            evaluation_text = await self._call_llm(messages, timeout=self.timeout)

            try:
                # 清理响应文本，确保是有效的JSON
                cleaned_text = evaluation_text.strip()
                if cleaned_text.startswith('```json'):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.endswith('```'):
                    cleaned_text = cleaned_text[:-3]
                cleaned_text = cleaned_text.strip()
                
                evaluation_result = json.loads(cleaned_text)
                
                # 确保结果中包含必要的字段
                evaluation_result.setdefault("is_sufficient", False)
                evaluation_result.setdefault("missing_information", [])
                evaluation_result.setdefault("should_continue", True)
                evaluation_result.setdefault("next_focus", "收集更多信息")
                evaluation_result.setdefault("confidence", 0.5)
                evaluation_result.setdefault("reasoning", "需要进一步评估")
                
                logger_manager.log_agent_operation(
                    self.name,
                    f"Agent响应评估完成 - 置信度: {evaluation_result['confidence']}",
                    level="INFO"
                )
                
                return evaluation_result
                
            except Exception as e:
                logger_manager.log_agent_operation(
                    self.name,
                    f"评估结果解析失败: {e}",
                    level="WARNING"
                )
                
                # 返回默认评估结果
                return {
                    "is_sufficient": False,
                    "missing_information": ["更多详细信息"],
                    "should_continue": True,
                    "next_focus": "基础信息收集",
                    "confidence": 0.3,
                    "reasoning": "评估失败，需要继续收集信息"
                }
                
        except Exception as e:
            logger_manager.log_agent_operation(
                self.name,
                f"Agent响应评估失败: {e}",
                level="ERROR"
            )
            
            # 返回默认评估结果
            return {
                "is_sufficient": False,
                "missing_information": ["基础信息"],
                "should_continue": True,
                "next_focus": "错误恢复",
                "confidence": 0.1,
                "reasoning": f"评估过程出错: {e}"
            }
