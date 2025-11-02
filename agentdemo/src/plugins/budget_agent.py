# agentdemo/src/plugins/budget_agent.py
import random
import json
from typing import Dict, Any

from ..agents.base_agent import BaseAgent
from ..models.agent_models import AgentType, AgentResponse, AgentCapability
from ..utils.logger_manager import logger_manager


class BudgetAgent(BaseAgent):
    """预算分析 Agent 插件 - 增强版"""

    def __init__(self):
        super().__init__(AgentType.BUDGET, "预算专家", "提供专业的旅行预算分析和成本估算服务")

        # 注册预算分析能力
        budget_capability = AgentCapability(
            name="budget_analysis",
            description="分析旅行预算和成本",
            input_schema={
                "type": "object",
                "properties": {
                    "destination": {"type": "string", "description": "目的地"},
                    "days": {"type": "integer", "description": "旅行天数"},
                    "travelers": {"type": "integer", "description": "旅行人数"},
                    "budget_range": {"type": "string", "description": "预算范围"}
                },
                "required": ["destination"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "cost_breakdown": {"type": "object"},
                    "total_cost": {"type": "number"},
                    "recommendations": {"type": "array"}
                }
            },
            timeout=20,
            max_retries=2
        )

        self.register_capability(budget_capability)

    async def process_request(self, query: str, context: Dict[str, Any] = None) -> AgentResponse:
        """处理预算分析请求"""
        logger_manager.log_agent_operation(
            self.name,
            f"开始处理预算分析: {query}",
            level="INFO"
        )
        
        try:
            # 从查询中提取预算信息
            budget_info = self._extract_budget_info(query)
            
            # 执行预算分析
            budget_data = await self._analyze_budget_with_timeout(budget_info)
            
            # 使用 LLM 生成自然语言响应
            content = await self._generate_budget_report(budget_data, query)
            
            response = AgentResponse(
                agent_type=self.agent_type,
                content=content,
                data=budget_data,
                confidence=0.8
            )
            
            logger_manager.log_agent_operation(
                self.name,
                f"预算分析完成 - 目的地: {budget_info['destination']}",
                level="INFO"
            )
            
            return response
            
        except Exception as e:
            logger_manager.log_agent_operation(
                self.name,
                f"预算分析失败: {e}",
                level="ERROR"
            )
            
            # 返回错误响应
            return AgentResponse(
                agent_type=self.agent_type,
                content=f"预算分析失败: {e}",
                data={"error": str(e)},
                confidence=0.1
            )

    async def _analyze_budget_with_timeout(self, budget_info: Dict[str, Any]) -> Dict[str, Any]:
        """带超时的预算分析"""
        try:
            # 模拟计算延迟
            await asyncio.sleep(random.uniform(0.3, 1.5))
            
            # 执行预算分析
            budget_data = self._analyze_budget(budget_info)
            
            return budget_data
            
        except asyncio.TimeoutError:
            logger_manager.log_timeout_event(
                self.name,
                "预算分析",
                self.timeout,
                retry_count=0
            )
            
            # 返回默认预算数据
            return self._get_default_budget_data(budget_info)

    def _extract_budget_info(self, query: str) -> Dict[str, Any]:
        """从查询中提取预算信息"""
        cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安"]
        
        # 默认值
        budget_info = {
            "destination": "北京",
            "days": 3,
            "travelers": 2,
            "budget_range": "中等"
        }
        
        # 提取目的地
        for city in cities:
            if city in query:
                budget_info["destination"] = city
                break
        
        # 提取天数
        if "天" in query:
            for word in query.split():
                if word.endswith("天"):
                    try:
                        days = int(word.replace("天", ""))
                        budget_info["days"] = days
                        break
                    except ValueError:
                        pass
        
        # 提取人数
        if "人" in query:
            for word in query.split():
                if word.endswith("人"):
                    try:
                        travelers = int(word.replace("人", ""))
                        budget_info["travelers"] = travelers
                        break
                    except ValueError:
                        pass
        
        # 提取预算范围
        if "便宜" in query or "经济" in query or "低预算" in query:
            budget_info["budget_range"] = "经济"
        elif "豪华" in query or "高端" in query or "高预算" in query:
            budget_info["budget_range"] = "豪华"
        
        logger_manager.log_agent_operation(
            self.name,
            f"提取预算信息: {budget_info}",
            level="INFO"
        )
        
        return budget_info

    def _analyze_budget(self, budget_info: Dict[str, Any]) -> Dict[str, Any]:
        """分析预算（模拟）"""
        destination = budget_info["destination"]
        days = budget_info["days"]
        travelers = budget_info["travelers"]
        budget_range = budget_info["budget_range"]
        
        # 基础成本数据（按城市和预算级别）
        cost_data = {
            "北京": {"经济": 300, "中等": 500, "豪华": 800},
            "上海": {"经济": 350, "中等": 550, "豪华": 850},
            "广州": {"经济": 250, "中等": 450, "豪华": 750},
            "深圳": {"经济": 320, "中等": 520, "豪华": 820},
            "杭州": {"经济": 280, "中等": 480, "豪华": 780},
            "成都": {"经济": 220, "中等": 420, "豪华": 720},
            "武汉": {"经济": 240, "中等": 440, "豪华": 740},
            "西安": {"经济": 200, "中等": 400, "豪华": 700}
        }
        
        daily_cost = cost_data.get(destination, {}).get(budget_range, 400)
        
        # 成本细分
        cost_breakdown = {
            "住宿": int(daily_cost * 0.4 * days * travelers),
            "餐饮": int(daily_cost * 0.3 * days * travelers),
            "交通": int(daily_cost * 0.15 * days * travelers),
            "景点": int(daily_cost * 0.1 * days * travelers),
            "购物": int(daily_cost * 0.05 * days * travelers)
        }
        
        total_cost = sum(cost_breakdown.values())
        
        # 生成建议
        recommendations = self._generate_recommendations(budget_range, total_cost, destination)
        
        return {
            "destination": destination,
            "days": days,
            "travelers": travelers,
            "budget_range": budget_range,
            "cost_breakdown": cost_breakdown,
            "total_cost": total_cost,
            "daily_cost_per_person": int(total_cost / (days * travelers)),
            "recommendations": recommendations,
            "currency": "CNY"
        }

    def _generate_recommendations(self, budget_range: str, total_cost: int, destination: str) -> list:
        """生成预算建议"""
        recommendations = []
        
        if budget_range == "经济":
            recommendations.extend([
                "选择经济型酒店或民宿",
                "多使用公共交通",
                "尝试当地特色小吃",
                "提前预订可享受优惠"
            ])
        elif budget_range == "中等":
            recommendations.extend([
                "选择舒适型酒店",
                "混合使用公共交通和网约车",
                "品尝当地特色餐厅",
                "合理安排景点游览顺序"
            ])
        else:  # 豪华
            recommendations.extend([
                "选择高端酒店或度假村",
                "考虑包车服务",
                "体验高端餐饮",
                "预留购物和娱乐预算"
            ])
        
        # 通用建议
        recommendations.extend([
            f"{destination}的旅游旺季价格会更高",
            "提前规划可以节省不少费用",
            "关注当地旅游优惠活动"
        ])
        
        return recommendations

    def _get_default_budget_data(self, budget_info: Dict[str, Any]) -> Dict[str, Any]:
        """获取默认预算数据（超时或错误时使用）"""
        return {
            "destination": budget_info["destination"],
            "days": budget_info["days"],
            "travelers": budget_info["travelers"],
            "budget_range": budget_info["budget_range"],
            "cost_breakdown": {
                "住宿": 1200,
                "餐饮": 900,
                "交通": 450,
                "景点": 300,
                "购物": 150
            },
            "total_cost": 3000,
            "daily_cost_per_person": 500,
            "recommendations": [
                "建议提前规划行程",
                "关注当地旅游信息",
                "合理安排预算"
            ],
            "currency": "CNY",
            "note": "预算数据仅供参考，实际费用可能有所不同"
        }

    async def _generate_budget_report(self, budget_data: Dict[str, Any], original_query: str) -> str:
        """生成预算报告"""
        report_prompt = f"""
基于以下预算数据生成一个友好的预算建议：

原始查询: {original_query}
预算数据: {json.dumps(budget_data, ensure_ascii=False, default=str)}

请生成一个自然、友好的预算建议，包括：
1. 总体预算估算
2. 各项费用明细
3. 实用的省钱建议
4. 预算分配建议

请用中文回复，保持友好和专业。
"""

        messages = [
            {"role": "system", "content": "你是一个预算专家，能够根据预算数据生成友好、专业的预算建议。"},
            {"role": "user", "content": report_prompt}
        ]

        try:
            report_text = await self._call_llm(messages, timeout=20)
            
            # 如果响应为空或无效，使用默认报告
            if not report_text or not isinstance(report_text, str):
                report_text = self._generate_default_report(budget_data)
            
            return report_text
            
        except Exception as e:
            logger_manager.log_agent_operation(
                self.name,
                f"预算报告生成失败: {e}",
                level="WARNING"
            )
            
            # 使用默认报告
            return self._generate_default_report(budget_data)

    def _generate_default_report(self, budget_data: Dict[str, Any]) -> str:
        """生成默认预算报告"""
        destination = budget_data.get("destination", "未知目的地")
        total_cost = budget_data.get("total_cost", 0)
        days = budget_data.get("days", 3)
        travelers = budget_data.get("travelers", 2)
        
        return f"根据估算，{destination}{days}天{travelers}人旅行的总预算约为{total_cost}元。建议您根据具体需求进一步调整预算分配。"
