# multi_agent_system/plugins/budget_agent.py
import random
import json
from typing import Dict, Any

from ..agents.plugin_agent import PluginAgent
from ..models.agent_models import AgentType, AgentResponse, AgentCapability


class BudgetAgent(PluginAgent):
    """预算分析 Agent 插件"""

    def __init__(self):
        super().__init__(AgentType.BUDGET, "预算分析师", "提供专业的旅行预算分析和成本优化建议")

        # 注册预算分析插件
        budget_capability = AgentCapability(
            name="budget_analysis",
            description="分析旅行预算",
            input_schema={
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "旅行天数"},
                    "travelers": {"type": "integer", "description": "旅行人数"},
                    "city": {"type": "string", "description": "目的城市"}
                },
                "required": ["days", "travelers"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "budget_breakdown": {"type": "object"},
                    "total_budget": {"type": "number"}
                }
            }
        )

        self.register_plugin("budget_analysis", self._analyze_budget, budget_capability)

    async def process_request(self, query: str, context: Dict[str, Any] = None) -> AgentResponse:
        days = self._extract_days(query)
        travelers = self._extract_travelers(query)
        city = self._extract_city(query)

        # 执行预算分析
        budget_data = await self.execute_plugin(
            "budget_analysis",
            days=days,
            travelers=travelers,
            city=city
        )

        # 使用 LLM 生成预算建议
        messages = [
            {"role": "system", "content": "你是一个预算分析专家，提供详细且实用的预算建议。"},
            {"role": "user", "content": f"基于以下预算数据提供建议: {json.dumps(budget_data, ensure_ascii=False)}"}
        ]

        content = self._call_llm(messages)

        return AgentResponse(
            agent_type=self.agent_type,
            content=content,
            data=budget_data,
            confidence=0.8
        )

    def _extract_days(self, query: str) -> int:
        """从查询中提取旅行天数"""
        if "三天" in query or "3天" in query:
            return 3
        elif "五天" in query or "5天" in query:
            return 5
        elif "七天" in query or "7天" in query:
            return 7
        elif "一天" in query or "1天" in query:
            return 1
        elif "两天" in query or "2天" in query:
            return 2
        else:
            return random.randint(3, 7)  # 默认3-7天

    def _extract_travelers(self, query: str) -> int:
        """从查询中提取旅行人数"""
        if "一人" in query or "1人" in query:
            return 1
        elif "两人" in query or "2人" in query:
            return 2
        elif "三人" in query or "3人" in query:
            return 3
        elif "四人" in query or "4人" in query:
            return 4
        elif "五人" in query or "5人" in query:
            return 5
        else:
            return random.randint(1, 4)  # 默认1-4人

    def _extract_city(self, query: str) -> str:
        """从查询中提取城市信息"""
        cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安"]
        for city in cities:
            if city in query:
                return city
        return "北京"  # 默认城市

    def _analyze_budget(self, days: int, travelers: int, city: str = "北京") -> Dict[str, Any]:
        """分析预算（模拟）"""
        # 生成预算分析
        budget_breakdown = {
            "accommodation": random.randint(200, 500) * days * travelers,
            "food": random.randint(100, 300) * days * travelers,
            "transportation": random.randint(500, 1500) * travelers,
            "activities": random.randint(300, 800) * travelers,
            "miscellaneous": random.randint(100, 300) * travelers
        }

        total_budget = sum(budget_breakdown.values())

        return {
            "travel_days": days,
            "travelers": travelers,
            "destination": city,
            "budget_breakdown": budget_breakdown,
            "total_budget": total_budget,
            "cost_per_person": total_budget / travelers,
            "currency": "CNY"
        }