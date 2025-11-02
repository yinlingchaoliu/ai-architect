# multi_agent_system/plugins/weather_agent.py
import random
import json
from datetime import datetime, timedelta
from typing import Dict, Any

from ..agents.plugin_agent import PluginAgent
from ..models.agent_models import AgentType, AgentResponse, AgentCapability


class WeatherAgent(PluginAgent):
    """天气查询 Agent 插件"""

    def __init__(self):
        super().__init__(AgentType.WEATHER, "天气专家", "提供专业的天气查询和预报服务")

        # 注册天气查询插件
        weather_capability = AgentCapability(
            name="weather_query",
            description="查询城市天气信息",
            input_schema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"},
                    "date": {"type": "string", "description": "日期"}
                },
                "required": ["city"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "weather": {"type": "string"},
                    "temperature": {"type": "string"},
                    "humidity": {"type": "string"}
                }
            }
        )

        self.register_plugin("weather_query", self._query_weather, weather_capability)

    async def process_request(self, query: str, context: Dict[str, Any] = None) -> AgentResponse:
        # 从查询中提取城市信息
        city = self._extract_city(query)

        # 执行天气查询
        weather_data = await self.execute_plugin("weather_query", city=city)

        # 使用 LLM 生成自然语言响应
        messages = [
            {"role": "system", "content": "你是一个天气专家，根据天气数据生成友好的天气报告。"},
            {"role": "user", "content": f"基于以下天气数据生成天气报告: {json.dumps(weather_data, ensure_ascii=False)}"}
        ]

        content = self._call_llm(messages)

        return AgentResponse(
            agent_type=self.agent_type,
            content=content,
            data=weather_data,
            confidence=0.9
        )

    def _extract_city(self, query: str) -> str:
        """从查询中提取城市信息"""
        cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安"]
        for city in cities:
            if city in query:
                return city
        return "北京"  # 默认城市

    def _query_weather(self, city: str) -> Dict[str, Any]:
        """查询天气（模拟）"""
        weather_conditions = ["晴朗", "多云", "小雨", "大雨", "雾", "雪"]

        return {
            "city": city,
            "date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "weather": random.choice(weather_conditions),
            "temperature": f"{random.randint(15, 35)}°C",
            "humidity": f"{random.randint(40, 90)}%",
            "wind_speed": f"{random.randint(1, 15)} km/h"
        }