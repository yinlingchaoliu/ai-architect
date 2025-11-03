# multi_agent_system/plugins/hotel_agent.py
import random
import json
from typing import Dict, Any

from ..agents.plugin_agent import PluginAgent
from ..models.agent_models import AgentType, AgentResponse, AgentCapability


class HotelAgent(PluginAgent):
    """酒店选择师 Agent 插件"""

    def __init__(self):
        super().__init__(AgentType.HOTEL, "酒店选择师", "提供专业的酒店查询和推荐服务")

        # 注册酒店查询插件
        hotel_capability = AgentCapability(
            name="hotel_query",
            description="查询城市酒店信息",
            input_schema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"},
                    "budget": {"type": "number", "description": "预算金额"}
                },
                "required": ["city"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "hotels": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "price": {"type": "string"},
                                "rating": {"type": "string"},
                                "description": {"type": "string"}
                            }
                        }
                    }
                }
            }
        )

        self.register_plugin("hotel_query", self._query_hotel, hotel_capability)

    async def process_request(self, query: str, context: Dict[str, Any] = None) -> AgentResponse:
        # 从查询中提取城市信息
        city = self._extract_city(query)
        budget = self._extract_budget(query)

        # 执行酒店查询
        hotel_data = await self.execute_plugin("hotel_query", city=city, budget=budget)

        # 使用 LLM 生成自然语言响应
        messages = [
            {"role": "system", "content": "你是一个专业的酒店选择师，根据酒店数据为用户提供详细的酒店推荐。"},
            {"role": "user", "content": f"基于以下酒店数据为用户提供推荐: {json.dumps(hotel_data, ensure_ascii=False)}"}
        ]

        content = await self._call_llm(messages)

        return AgentResponse(
            agent_type=self.agent_type,
            content=content,
            data=hotel_data,
            confidence=0.9
        )

    def _extract_city(self, query: str) -> str:
        """从查询中提取城市信息"""
        cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安"]
        for city in cities:
            if city in query:
                return city
        return "北京"  # 默认城市
    
    def _extract_budget(self, query: str) -> float:
        """从查询中提取预算信息"""
        # 简单的预算提取逻辑
        if "经济型" in query or "便宜" in query or "实惠" in query:
            return 500
        elif "豪华" in query or "高档" in query:
            return 1500
        elif "舒适" in query or "商务" in query:
            return 1000
        return 0  # 不指定预算

    def _query_hotel(self, city: str, budget: float = 0) -> Dict[str, Any]:
        """查询酒店信息（模拟）"""
        hotel_names = [
            f"{city}国际大酒店",
            f"{city}丽思卡尔顿酒店",
            f"{city}希尔顿酒店",
            f"{city}万豪酒店",
            f"{city}如家快捷酒店",
            f"{city}汉庭酒店",
            f"{city}悦榕庄",
            f"{city}四季酒店"
        ]
        
        descriptions = [
            "位于市中心，交通便利，设施齐全",
            "靠近商业区，适合商务出行",
            "环境优雅，服务周到",
            "性价比高，干净整洁",
            "五星级服务，奢华体验",
            "靠近旅游景点，观光便利"
        ]
        
        hotels = []
        # 根据预算筛选酒店
        for i in range(random.randint(3, 5)):
            if budget == 0:
                price = random.randint(300, 2000)
            elif budget <= 500:
                price = random.randint(200, 500)
            elif budget <= 1000:
                price = random.randint(500, 1000)
            else:
                price = random.randint(1000, 3000)
                
            hotel = {
                "name": hotel_names[i % len(hotel_names)],
                "price": f"¥{price}/晚",
                "rating": f"{round(random.uniform(3.5, 5.0), 1)}/5分",
                "description": random.choice(descriptions)
            }
            hotels.append(hotel)
        
        # 按价格排序
        hotels.sort(key=lambda x: int(x["price"][1:x["price"].find("/")]))
        
        return {
            "city": city,
            "hotels": hotels,
            "total": len(hotels)
        }