# agentdemo/src/plugins/transport_agent.py
import random
import json
from typing import Dict, Any

from ..agents.base_agent import BaseAgent
from ..models.agent_models import AgentType, AgentResponse, AgentCapability
from ..utils.logger_manager import logger_manager


class TransportAgent(BaseAgent):
    """交通查询 Agent 插件 - 增强版"""

    def __init__(self):
        super().__init__(AgentType.TRANSPORT, "交通专家", "提供专业的交通方式和路线规划服务")

        # 注册交通查询能力
        transport_capability = AgentCapability(
            name="transport_query",
            description="查询交通方式和路线规划",
            input_schema={
                "type": "object",
                "properties": {
                    "from_city": {"type": "string", "description": "出发城市"},
                    "to_city": {"type": "string", "description": "目的城市"},
                    "transport_type": {"type": "string", "description": "交通方式"}
                },
                "required": ["from_city", "to_city"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "options": {"type": "array"},
                    "recommendation": {"type": "string"},
                    "cost_estimate": {"type": "object"}
                }
            },
            timeout=30,
            max_retries=2
        )

        self.register_capability(transport_capability)

    async def process_request(self, query: str, context: Dict[str, Any] = None) -> AgentResponse:
        """处理交通查询请求"""
        logger_manager.log_agent_operation(
            self.name,
            f"开始处理交通查询: {query}",
            level="INFO"
        )
        
        try:
            # 从查询中提取城市信息
            from_city, to_city = self._extract_cities(query)
            
            # 执行交通查询
            transport_data = await self._query_transport_with_timeout(from_city, to_city)
            
            # 使用 LLM 生成自然语言响应
            content = await self._generate_transport_report(transport_data, query)
            
            response = AgentResponse(
                agent_type=self.agent_type,
                content=content,
                data=transport_data,
                confidence=0.85
            )
            
            logger_manager.log_agent_operation(
                self.name,
                f"交通查询完成 - 从 {from_city} 到 {to_city}",
                level="INFO"
            )
            
            return response
            
        except Exception as e:
            logger_manager.log_agent_operation(
                self.name,
                f"交通查询失败: {e}",
                level="ERROR"
            )
            
            # 返回错误响应
            return AgentResponse(
                agent_type=self.agent_type,
                content=f"交通查询失败: {e}",
                data={"error": str(e)},
                confidence=0.1
            )

    async def _query_transport_with_timeout(self, from_city: str, to_city: str) -> Dict[str, Any]:
        """带超时的交通查询"""
        try:
            # 模拟网络延迟
            await asyncio.sleep(random.uniform(0.5, 3.0))
            
            # 执行交通查询
            transport_data = self._query_transport_options(from_city, to_city)
            
            return transport_data
            
        except asyncio.TimeoutError:
            logger_manager.log_timeout_event(
                self.name,
                "交通查询",
                self.timeout,
                retry_count=0
            )
            
            # 返回默认交通数据
            return self._get_default_transport_data(from_city, to_city)

    def _extract_cities(self, query: str) -> tuple[str, str]:
        """从查询中提取出发和目的城市"""
        cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安"]
        
        from_city = "北京"  # 默认出发城市
        to_city = "上海"    # 默认目的城市
        
        # 简单的城市提取逻辑
        for city in cities:
            if f"从{city}" in query or f"到{city}" in query:
                if "从" in query and query.index(f"从{city}") < query.index(f"到"):
                    from_city = city
                elif "到" in query:
                    to_city = city
        
        # 如果没有明确指定，使用第一个找到的城市作为目的城市
        for city in cities:
            if city in query and city != from_city:
                to_city = city
                break
        
        logger_manager.log_agent_operation(
            self.name,
            f"提取城市信息 - 从 {from_city} 到 {to_city}",
            level="INFO"
        )
        
        return from_city, to_city

    def _query_transport_options(self, from_city: str, to_city: str) -> Dict[str, Any]:
        """查询交通选项（模拟）"""
        # 基础交通选项
        transport_options = []
        
        # 飞机选项
        if from_city != to_city:
            flight_time = random.randint(1, 4)
            flight_price = random.randint(500, 2000)
            transport_options.append({
                "type": "飞机",
                "duration": f"{flight_time}小时",
                "cost": f"{flight_price}元",
                "description": f"{from_city}到{to_city}的直飞航班",
                "advantages": ["速度快", "舒适"],
                "disadvantages": ["价格较高", "需要提前到达机场"]
            })
        
        # 高铁选项
        train_time = random.randint(2, 8)
        train_price = random.randint(200, 800)
        transport_options.append({
            "type": "高铁",
            "duration": f"{train_time}小时",
            "cost": f"{train_price}元",
            "description": f"{from_city}到{to_city}的高铁",
            "advantages": ["准时", "舒适", "市中心到市中心"],
            "disadvantages": ["时间较长"]
        })
        
        # 自驾选项
        drive_distance = random.randint(100, 800)
        drive_time = random.randint(2, 10)
        drive_cost = random.randint(100, 500)
        transport_options.append({
            "type": "自驾",
            "duration": f"{drive_time}小时",
            "distance": f"{drive_distance}公里",
            "cost": f"{drive_cost}元（油费+过路费）",
            "description": f"{from_city}到{to_city}的自驾路线",
            "advantages": ["灵活", "自由"],
            "disadvantages": ["驾驶疲劳", "交通拥堵风险"]
        })
        
        # 大巴选项（短途）
        if drive_distance < 300:
            bus_time = random.randint(3, 6)
            bus_price = random.randint(80, 200)
            transport_options.append({
                "type": "大巴",
                "duration": f"{bus_time}小时",
                "cost": f"{bus_price}元",
                "description": f"{from_city}到{to_city}的长途大巴",
                "advantages": ["价格便宜"],
                "disadvantages": ["舒适度较低", "时间较长"]
            })
        
        # 推荐选项
        recommendation = self._get_recommendation(transport_options)
        
        return {
            "from_city": from_city,
            "to_city": to_city,
            "options": transport_options,
            "recommendation": recommendation,
            "cost_estimate": {
                "min_cost": min(int(opt["cost"].replace("元", "")) for opt in transport_options),
                "max_cost": max(int(opt["cost"].replace("元", "")) for opt in transport_options),
                "average_cost": sum(int(opt["cost"].replace("元", "")) for opt in transport_options) // len(transport_options)
            }
        }

    def _get_recommendation(self, options: list) -> str:
        """获取推荐交通方式"""
        if not options:
            return "暂无推荐"
        
        # 简单的推荐逻辑
        for option in options:
            if option["type"] == "高铁":
                return "高铁是最佳选择，兼顾速度和舒适度"
            elif option["type"] == "飞机":
                return "飞机是最快的方式，适合长途旅行"
        
        return options[0]["type"]

    def _get_default_transport_data(self, from_city: str, to_city: str) -> Dict[str, Any]:
        """获取默认交通数据（超时或错误时使用）"""
        return {
            "from_city": from_city,
            "to_city": to_city,
            "options": [
                {
                    "type": "高铁",
                    "duration": "4小时",
                    "cost": "500元",
                    "description": f"{from_city}到{to_city}的高铁",
                    "advantages": ["准时", "舒适"],
                    "disadvantages": ["可能需要中转"]
                }
            ],
            "recommendation": "高铁是推荐的交通方式",
            "cost_estimate": {
                "min_cost": 500,
                "max_cost": 500,
                "average_cost": 500
            },
            "note": "数据可能不完整，请稍后重试"
        }

    async def _generate_transport_report(self, transport_data: Dict[str, Any], original_query: str) -> str:
        """生成交通报告"""
        report_prompt = f"""
基于以下交通数据生成一个友好的交通建议：

原始查询: {original_query}
交通数据: {json.dumps(transport_data, ensure_ascii=False, default=str)}

请生成一个自然、友好的交通建议，包括：
1. 可用的交通方式
2. 各种方式的优缺点
3. 推荐的方式和理由
4. 大致的费用和时间

请用中文回复，保持友好和专业。
"""

        messages = [
            {"role": "system", "content": "你是一个交通专家，能够根据交通数据生成友好、专业的交通建议。"},
            {"role": "user", "content": report_prompt}
        ]

        try:
            report_text = await self._call_llm(messages, timeout=25)
            
            # 如果响应为空或无效，使用默认报告
            if not report_text or not isinstance(report_text, str):
                report_text = self._generate_default_report(transport_data)
            
            return report_text
            
        except Exception as e:
            logger_manager.log_agent_operation(
                self.name,
                f"交通报告生成失败: {e}",
                level="WARNING"
            )
            
            # 使用默认报告
            return self._generate_default_report(transport_data)

    def _generate_default_report(self, transport_data: Dict[str, Any]) -> str:
        """生成默认交通报告"""
        from_city = transport_data.get("from_city", "未知城市")
        to_city = transport_data.get("to_city", "未知城市")
        recommendation = transport_data.get("recommendation", "暂无推荐")
        
        return f"从{from_city}到{to_city}有多种交通方式可选。{recommendation}。建议您根据具体需求和预算选择合适的交通方式。"
