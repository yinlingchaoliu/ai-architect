# multi_agent_system/plugins/custom_agent.py
import random
import json
from typing import List, Dict, Any

from ..agents.plugin_agent import PluginAgent
from ..models.agent_models import AgentType, AgentResponse, AgentCapability


class HotelAgent(PluginAgent):
    """酒店查询 Agent 插件"""

    def __init__(self):
        super().__init__(AgentType.CUSTOM, "酒店专家", "提供专业的酒店查询和推荐服务")

        # 注册酒店查询插件
        hotel_capability = AgentCapability(
            name="hotel_query",
            description="查询城市酒店信息",
            input_schema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"},
                    "check_in": {"type": "string", "description": "入住日期"},
                    "check_out": {"type": "string", "description": "退房日期"},
                    "budget": {"type": "number", "description": "预算范围"}
                },
                "required": ["city"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "hotels": {"type": "array", "items": {"type": "object"}},
                    "recommendation": {"type": "string"}
                }
            }
        )

        self.register_plugin("hotel_query", self._query_hotels, hotel_capability)

    async def process_request(self, query: str, context: Dict[str, Any] = None) -> AgentResponse:
        # 从查询中提取城市信息
        city = self._extract_city(query)
        budget = self._extract_budget(query)

        # 执行酒店查询
        hotel_data = await self.execute_plugin("hotel_query", city=city, budget=budget)

        # 使用 LLM 生成建议
        messages = [
            {"role": "system", "content": "你是一个酒店推荐专家，根据酒店数据提供专业的住宿建议。"},
            {"role": "user", "content": f"基于以下酒店数据提供建议: {json.dumps(hotel_data, ensure_ascii=False)}"}
        ]

        content = self._call_llm(messages)

        return AgentResponse(
            agent_type=self.agent_type,
            content=content,
            data=hotel_data,
            confidence=0.85
        )

    def _extract_city(self, query: str) -> str:
        """从查询中提取城市信息"""
        cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安"]
        for city in cities:
            if city in query:
                return city
        return "北京"  # 默认城市

    def _extract_budget(self, query: str) -> int:
        """从查询中提取预算信息"""
        if "豪华" in query or "五星" in query:
            return 1000
        elif "经济" in query or "快捷" in query:
            return 200
        else:
            return 500  # 默认中等预算

    def _query_hotels(self, city: str, budget: int = 500) -> Dict[str, Any]:
        """查询酒店（模拟）"""
        hotel_chains = ["希尔顿", "万豪", "洲际", "香格里拉", "如家", "汉庭", "7天"]

        hotels = []
        for i in range(3):
            base_price = budget * random.uniform(0.8, 1.5)
            hotels.append({
                "name": f"{random.choice(hotel_chains)}{city}店",
                "price": round(base_price),
                "rating": round(random.uniform(3.5, 5.0), 1),
                "location": f"{city}市中心",
                "features": ["免费WiFi", "早餐", "停车场", "健身房"][:random.randint(2, 4)]
            })

        # 按价格排序
        hotels.sort(key=lambda x: x["price"])

        return {
            "city": city,
            "budget_range": budget,
            "hotels": hotels,
            "recommendation": hotels[0]["name"] if hotels else "无推荐"
        }


class AttractionAgent(PluginAgent):
    """景点推荐 Agent 插件"""

    def __init__(self):
        super().__init__(AgentType.CUSTOM, "景点推荐师", "提供专业的旅游景点推荐和行程安排")

        # 注册景点查询插件
        attraction_capability = AgentCapability(
            name="attraction_query",
            description="查询城市旅游景点",
            input_schema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"},
                    "interests": {"type": "array", "items": {"type": "string"}, "description": "兴趣标签"},
                    "days": {"type": "integer", "description": "游玩天数"}
                },
                "required": ["city"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "attractions": {"type": "array", "items": {"type": "object"}},
                    "itinerary": {"type": "array", "items": {"type": "object"}}
                }
            }
        )

        self.register_plugin("attraction_query", self._query_attractions, attraction_capability)

    async def process_request(self, query: str, context: Dict[str, Any] = None) -> AgentResponse:
        city = self._extract_city(query)
        interests = self._extract_interests(query)
        days = self._extract_days(query)

        # 执行景点查询
        attraction_data = await self.execute_plugin(
            "attraction_query",
            city=city,
            interests=interests,
            days=days
        )

        # 使用 LLM 生成建议
        messages = [
            {"role": "system", "content": "你是一个旅游景点推荐专家，根据景点数据提供专业的行程建议。"},
            {"role": "user", "content": f"基于以下景点数据提供建议: {json.dumps(attraction_data, ensure_ascii=False)}"}
        ]

        content = self._call_llm(messages)

        return AgentResponse(
            agent_type=self.agent_type,
            content=content,
            data=attraction_data,
            confidence=0.8
        )

    def _extract_city(self, query: str) -> str:
        """从查询中提取城市信息"""
        cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安"]
        for city in cities:
            if city in query:
                return city
        return "北京"

    def _extract_interests(self, query: str) -> List[str]:
        """从查询中提取兴趣标签"""
        interests = []
        interest_map = {
            "历史": ["历史", "文化", "古迹", "博物馆"],
            "自然": ["自然", "风景", "公园", "山水"],
            "美食": ["美食", "小吃", "餐厅", "特色菜"],
            "购物": ["购物", "商场", "商业街", "买"]
        }

        for category, keywords in interest_map.items():
            if any(keyword in query for keyword in keywords):
                interests.append(category)

        return interests if interests else ["历史", "自然"]  # 默认兴趣

    def _extract_days(self, query: str) -> int:
        """从查询中提取游玩天数"""
        if "一天" in query or "1天" in query:
            return 1
        elif "两天" in query or "2天" in query:
            return 2
        elif "三天" in query or "3天" in query:
            return 3
        else:
            return 2  # 默认2天

    def _query_attractions(self, city: str, interests: List[str], days: int) -> Dict[str, Any]:
        """查询景点（模拟）"""
        # 各城市的景点数据库
        attractions_db = {
            "北京": [
                {"name": "故宫", "type": "历史", "duration": "半天", "price": 60},
                {"name": "天安门广场", "type": "历史", "duration": "2小时", "price": 0},
                {"name": "颐和园", "type": "自然", "duration": "半天", "price": 30},
                {"name": "长城", "type": "历史", "duration": "一天", "price": 45},
                {"name": "王府井", "type": "购物", "duration": "3小时", "price": 0}
            ],
            "上海": [
                {"name": "外滩", "type": "自然", "duration": "2小时", "price": 0},
                {"name": "东方明珠", "type": "自然", "duration": "3小时", "price": 120},
                {"name": "南京路", "type": "购物", "duration": "3小时", "price": 0},
                {"name": "城隍庙", "type": "历史", "duration": "半天", "price": 10}
            ]
        }

        # 获取城市景点，过滤兴趣
        city_attractions = attractions_db.get(city, [])
        filtered_attractions = [
            attr for attr in city_attractions
            if any(interest in attr["type"] for interest in interests)
        ]

        # 生成行程安排
        itinerary = []
        for day in range(1, days + 1):
            day_attractions = filtered_attractions[(day - 1) * 2:day * 2]
            if day_attractions:
                itinerary.append({
                    "day": day,
                    "attractions": day_attractions,
                    "total_duration": "一天",
                    "estimated_cost": sum(attr["price"] for attr in day_attractions)
                })

        return {
            "city": city,
            "interests": interests,
            "days": days,
            "attractions": filtered_attractions,
            "itinerary": itinerary
        }