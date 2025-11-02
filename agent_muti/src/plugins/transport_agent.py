# multi_agent_system/plugins/transport_agent.py
import random
import json
from typing import Any, Dict

from ..agents.plugin_agent import PluginAgent
from ..models.agent_models import AgentType, AgentResponse, AgentCapability


class TransportAgent(PluginAgent):
    """交通规划 Agent 插件"""

    def __init__(self):
        super().__init__(AgentType.TRANSPORT, "交通规划师", "提供专业的交通路线规划和出行建议")

        # 注册交通查询插件
        transport_capability = AgentCapability(
            name="transport_query",
            description="查询交通路线和方式",
            input_schema={
                "type": "object",
                "properties": {
                    "from_city": {"type": "string", "description": "出发城市"},
                    "to_city": {"type": "string", "description": "目的城市"}
                },
                "required": ["from_city", "to_city"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "options": {"type": "array", "items": {"type": "object"}},
                    "best_option": {"type": "object"}
                }
            }
        )

        self.register_plugin("transport_query", self._query_transport, transport_capability)

    async def process_request(self, query: str, context: Dict[str, Any] = None) -> AgentResponse:
        locations = self._extract_locations(query)

        # 执行交通查询
        transport_data = await self.execute_plugin(
            "transport_query",
            from_city=locations.get("from", "北京"),
            to_city=locations.get("to", "上海")
        )

        # 使用 LLM 生成建议
        messages = [
            {"role": "system", "content": "你是一个交通规划专家，根据交通选项提供专业的旅行建议。"},
            {"role": "user", "content": f"基于以下交通数据提供建议: {json.dumps(transport_data, ensure_ascii=False)}"}
        ]

        content = await self._call_llm(messages)

        return AgentResponse(
            agent_type=self.agent_type,
            content=content,
            data=transport_data,
            confidence=0.85
        )

    def _extract_locations(self, query: str) -> Dict[str, str]:
        """提取地点信息"""
        cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安"]
        found_cities = [city for city in cities if city in query]

        if len(found_cities) >= 2:
            return {"from": found_cities[0], "to": found_cities[1]}
        elif len(found_cities) == 1:
            return {"to": found_cities[0]}
        else:
            return {"from": "北京", "to": "上海"}

    def _query_transport(self, from_city: str, to_city: str) -> Dict[str, Any]:
        """查询交通方式（模拟）"""
        transport_options = []

        transport_types = [
            {"type": "飞机", "duration": f"{random.randint(1, 4)}小时", "cost": random.randint(500, 2000)},
            {"type": "高铁", "duration": f"{random.randint(2, 6)}小时", "cost": random.randint(300, 800)},
            {"type": "自驾", "duration": f"{random.randint(5, 12)}小时", "cost": random.randint(200, 500)}
        ]

        for transport in transport_types:
            transport_options.append({
                "type": transport["type"],
                "from": from_city,
                "to": to_city,
                "duration": transport["duration"],
                "cost": transport["cost"],
                "recommendation": "推荐" if transport["type"] == "高铁" else "可选"
            })

        return {
            "from_city": from_city,
            "to_city": to_city,
            "options": transport_options,
            "best_option": next((opt for opt in transport_options if opt["recommendation"] == "推荐"),
                                transport_options[0])
        }