# agentdemo/src/plugins/weather_agent.py
import random
import json
from datetime import datetime, timedelta
from typing import Dict, Any

from ..agents.base_agent import BaseAgent
from ..models.agent_models import AgentType, AgentResponse, AgentCapability
from ..utils.logger_manager import logger_manager


class WeatherAgent(BaseAgent):
    """天气查询 Agent 插件 - 增强版"""

    def __init__(self):
        super().__init__(AgentType.WEATHER, "天气专家", "提供专业的天气查询和预报服务")

        # 注册天气查询能力
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
                    "humidity": {"type": "string"},
                    "wind_speed": {"type": "string"}
                }
            },
            timeout=25,
            max_retries=2
        )

        self.register_capability(weather_capability)

    async def process_request(self, query: str, context: Dict[str, Any] = None) -> AgentResponse:
        """处理天气查询请求"""
        logger_manager.log_agent_operation(
            self.name,
            f"开始处理天气查询: {query}",
            level="INFO"
        )
        
        try:
            # 从查询中提取城市信息
            city = self._extract_city(query)
            
            # 执行天气查询
            weather_data = await self._query_weather_with_timeout(city)
            
            # 使用 LLM 生成自然语言响应
            content = await self._generate_weather_report(weather_data, query)
            
            response = AgentResponse(
                agent_type=self.agent_type,
                content=content,
                data=weather_data,
                confidence=0.9
            )
            
            logger_manager.log_agent_operation(
                self.name,
                f"天气查询完成 - 城市: {city}",
                level="INFO"
            )
            
            return response
            
        except Exception as e:
            logger_manager.log_agent_operation(
                self.name,
                f"天气查询失败: {e}",
                level="ERROR"
            )
            
            # 返回错误响应
            return AgentResponse(
                agent_type=self.agent_type,
                content=f"天气查询失败: {e}",
                data={"error": str(e)},
                confidence=0.1
            )

    async def _query_weather_with_timeout(self, city: str) -> Dict[str, Any]:
        """带超时的天气查询"""
        try:
            # 模拟网络延迟
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            # 执行天气查询
            weather_data = self._query_weather(city)
            
            return weather_data
            
        except asyncio.TimeoutError:
            logger_manager.log_timeout_event(
                self.name,
                "天气查询",
                self.timeout,
                retry_count=0
            )
            
            # 返回默认天气数据
            return self._get_default_weather_data(city)

    def _extract_city(self, query: str) -> str:
        """从查询中提取城市信息"""
        cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安"]
        for city in cities:
            if city in query:
                return city
        
        # 如果没有找到特定城市，返回默认城市
        logger_manager.log_agent_operation(
            self.name,
            f"未在查询中找到特定城市，使用默认城市: 北京",
            level="WARNING"
        )
        return "北京"

    def _query_weather(self, city: str) -> Dict[str, Any]:
        """查询天气（模拟）"""
        weather_conditions = ["晴朗", "多云", "小雨", "大雨", "雾", "雪"]
        temperatures = {
            "北京": (15, 25),
            "上海": (18, 28),
            "广州": (20, 30),
            "深圳": (22, 32),
            "杭州": (16, 26),
            "成都": (14, 24),
            "武汉": (17, 27),
            "西安": (13, 23)
        }
        
        temp_range = temperatures.get(city, (15, 25))
        temperature = random.randint(temp_range[0], temp_range[1])
        
        return {
            "city": city,
            "date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "weather": random.choice(weather_conditions),
            "temperature": f"{temperature}°C",
            "humidity": f"{random.randint(40, 90)}%",
            "wind_speed": f"{random.randint(1, 15)} km/h",
            "aqi": random.randint(30, 150),
            "uv_index": random.randint(1, 10)
        }

    def _get_default_weather_data(self, city: str) -> Dict[str, Any]:
        """获取默认天气数据（超时或错误时使用）"""
        return {
            "city": city,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "weather": "多云",
            "temperature": "20°C",
            "humidity": "60%",
            "wind_speed": "5 km/h",
            "aqi": 80,
            "uv_index": 5,
            "note": "数据可能不准确，请稍后重试"
        }

    async def _generate_weather_report(self, weather_data: Dict[str, Any], original_query: str) -> str:
        """生成天气报告"""
        report_prompt = f"""
基于以下天气数据生成一个友好的天气报告：

原始查询: {original_query}
天气数据: {json.dumps(weather_data, ensure_ascii=False, default=str)}

请生成一个自然、友好的天气报告，包括：
1. 城市和日期
2. 天气状况
3. 温度、湿度、风速等关键信息
4. 适当的建议（如穿衣建议、出行建议等）

请用中文回复，保持友好和专业。
"""

        messages = [
            {"role": "system", "content": "你是一个天气专家，能够根据天气数据生成友好、专业的天气报告。"},
            {"role": "user", "content": report_prompt}
        ]

        try:
            report_text = await self._call_llm(messages, timeout=20)
            
            # 如果响应为空或无效，使用默认报告
            if not report_text or not isinstance(report_text, str):
                report_text = self._generate_default_report(weather_data)
            
            return report_text
            
        except Exception as e:
            logger_manager.log_agent_operation(
                self.name,
                f"天气报告生成失败: {e}",
                level="WARNING"
            )
            
            # 使用默认报告
            return self._generate_default_report(weather_data)

    def _generate_default_report(self, weather_data: Dict[str, Any]) -> str:
        """生成默认天气报告"""
        city = weather_data.get("city", "未知城市")
        weather = weather_data.get("weather", "未知")
        temperature = weather_data.get("temperature", "未知")
        
        return f"根据最新数据，{city}的天气情况为：{weather}，气温{temperature}。建议您根据实际情况安排出行。"
