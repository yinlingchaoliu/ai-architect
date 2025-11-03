# multi_agent_system/plugins/attraction_agent.py
import random
import json
from typing import Dict, Any, List

from ..agents.plugin_agent import PluginAgent
from ..models.agent_models import AgentType, AgentResponse, AgentCapability


class AttractionAgent(PluginAgent):
    """景点推荐师 Agent 插件"""

    def __init__(self):
        super().__init__(AgentType.ATTRACTION, "景点推荐师", "提供专业的景点推荐和旅游攻略服务")

        # 注册景点查询插件
        attraction_capability = AgentCapability(
            name="attraction_query",
            description="查询城市景点信息和攻略",
            input_schema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"},
                    "days": {"type": "integer", "description": "游玩天数"}
                },
                "required": ["city"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "attractions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "rating": {"type": "string"},
                                "description": {"type": "string"},
                                "ticket": {"type": "string"},
                                "opening_hours": {"type": "string"},
                                "tips": {"type": "string"}
                            }
                        }
                    },
                    "itinerary": {"type": "string"}
                }
            }
        )

        self.register_plugin("attraction_query", self._query_attraction, attraction_capability)
        
        # 城市景点数据库（模拟）
        self.city_attractions = {
            "北京": [
                {"name": "故宫", "rating": "4.8", "description": "中国明清两代的皇家宫殿", "ticket": "¥60"},
                {"name": "长城", "rating": "4.9", "description": "世界文化遗产，中国古代军事防御工程", "ticket": "¥40"},
                {"name": "天坛", "rating": "4.6", "description": "明清两代皇帝祭天祈谷之地", "ticket": "¥15"},
                {"name": "颐和园", "rating": "4.7", "description": "中国古典园林之杰作", "ticket": "¥30"},
                {"name": "圆明园", "rating": "4.5", "description": "被誉为万园之园的皇家园林", "ticket": "¥10"},
                {"name": "鸟巢", "rating": "4.4", "description": "2008年北京奥运会主体育场", "ticket": "¥50"}
            ],
            "上海": [
                {"name": "外滩", "rating": "4.7", "description": "上海的标志性景观", "ticket": "免费"},
                {"name": "东方明珠", "rating": "4.5", "description": "上海地标性建筑", "ticket": "¥160"},
                {"name": "迪士尼乐园", "rating": "4.7", "description": "大型主题乐园", "ticket": "¥399"},
                {"name": "豫园", "rating": "4.3", "description": "江南古典园林", "ticket": "¥40"},
                {"name": "田子坊", "rating": "4.2", "description": "文艺小资聚集地", "ticket": "免费"},
                {"name": "上海博物馆", "rating": "4.6", "description": "综合性博物馆", "ticket": "免费"}
            ],
            "杭州": [
                {"name": "西湖", "rating": "4.9", "description": "人间天堂，世界文化遗产", "ticket": "免费"},
                {"name": "灵隐寺", "rating": "4.6", "description": "中国佛教古刹", "ticket": "¥30"},
                {"name": "千岛湖", "rating": "4.7", "description": "国家5A级景区", "ticket": "¥130"},
                {"name": "宋城", "rating": "4.4", "description": "大型宋代文化主题公园", "ticket": "¥310"},
                {"name": "西溪湿地", "rating": "4.5", "description": "国家湿地公园", "ticket": "¥80"},
                {"name": "雷峰塔", "rating": "4.3", "description": "西湖十景之一", "ticket": "¥40"}
            ],
            "成都": [
                {"name": "大熊猫繁育研究基地", "rating": "4.7", "description": "世界著名的大熊猫迁地保护基地", "ticket": "¥58"},
                {"name": "锦里古街", "rating": "4.5", "description": "成都著名的商业街", "ticket": "免费"},
                {"name": "宽窄巷子", "rating": "4.4", "description": "成都遗留下来的较成规模的清朝古街道", "ticket": "免费"},
                {"name": "武侯祠", "rating": "4.5", "description": "纪念三国时期蜀汉丞相诸葛亮的祠堂", "ticket": "¥60"},
                {"name": "都江堰", "rating": "4.7", "description": "世界文化遗产", "ticket": "¥80"},
                {"name": "青城山", "rating": "4.6", "description": "道教名山", "ticket": "¥90"}
            ]
        }

    async def process_request(self, query: str, context: Dict[str, Any] = None) -> AgentResponse:
        # 从查询中提取城市和天数信息
        city = self._extract_city(query)
        days = self._extract_days(query)

        # 执行景点查询
        attraction_data = await self.execute_plugin("attraction_query", city=city, days=days)

        # 使用 LLM 生成自然语言响应
        messages = [
            {"role": "system", "content": "你是一个专业的景点推荐师，根据景点数据为用户提供详细的景点推荐和旅游攻略。"},
            {"role": "user", "content": f"基于以下景点数据为用户提供推荐和攻略: {json.dumps(attraction_data, ensure_ascii=False)}"}
        ]

        content = await self._call_llm(messages)

        return AgentResponse(
            agent_type=self.agent_type,
            content=content,
            data=attraction_data,
            confidence=0.9
        )

    def _extract_city(self, query: str) -> str:
        """从查询中提取城市信息"""
        cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安"]
        for city in cities:
            if city in query:
                return city
        return "北京"  # 默认城市
    
    def _extract_days(self, query: str) -> int:
        """从查询中提取游玩天数"""
        if "一天" in query or "1天" in query:
            return 1
        elif "两天" in query or "2天" in query:
            return 2
        elif "三天" in query or "3天" in query:
            return 3
        elif "四天" in query or "4天" in query:
            return 4
        elif "五天" in query or "5天" in query:
            return 5
        return 2  # 默认2天

    def _query_attraction(self, city: str, days: int = 2) -> Dict[str, Any]:
        """查询景点信息（模拟）"""
        # 获取城市景点列表，如果城市不存在则使用默认景点
        city_data = self.city_attractions.get(city, self.city_attractions["北京"])
        
        # 根据天数选择景点数量
        num_attractions = min(days * 3, len(city_data))
        
        # 随机选择景点并添加开放时间和游玩建议
        selected_attractions = random.sample(city_data, num_attractions)
        for attraction in selected_attractions:
            # 添加开放时间
            opening_hours = ["08:00-17:00", "09:00-18:00", "全天开放", "08:30-17:30", "09:30-16:30"]
            attraction["opening_hours"] = random.choice(opening_hours)
            
            # 添加游玩建议
            tips = [
                "建议早上前往，避开人流高峰",
                "记得携带学生证，可享受优惠",
                "周边有很多特色餐厅",
                "建议游玩时间2-3小时",
                "周末人流量大，建议工作日前往",
                "建议穿舒适的鞋子"
            ]
            attraction["tips"] = random.choice(tips)
        
        # 生成行程安排
        itinerary = self._generate_itinerary(selected_attractions, days)
        
        return {
            "city": city,
            "attractions": selected_attractions,
            "days": days,
            "itinerary": itinerary,
            "total": len(selected_attractions)
        }
    
    def _generate_itinerary(self, attractions: List[Dict[str, Any]], days: int) -> str:
        """根据景点生成行程安排"""
        attractions_per_day = len(attractions) // days
        itinerary = f"{days}天行程安排：\n"
        
        for day in range(days):
            start_idx = day * attractions_per_day
            if day == days - 1:
                # 最后一天安排剩余所有景点
                day_attractions = attractions[start_idx:]
            else:
                day_attractions = attractions[start_idx:start_idx + attractions_per_day]
            
            itinerary += f"\n第{day + 1}天：\n"
            for i, attraction in enumerate(day_attractions, 1):
                itinerary += f"  {i}. {attraction['name']} - {attraction['description'][:20]}...\n"
        
        return itinerary