import datetime
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

from src.config.settings import DEFAULT_CITY
from src.utils.utils import datetime_to_str
from src.weather.service import WeatherService

SERVER_NAME = "WeatherTools"
# 初始化FastMCP服务器
mcp = FastMCP(SERVER_NAME)

service = WeatherService()

@mcp.tool(description="获取指定城市的当前天气信息")
def get_weather(city: str = DEFAULT_CITY) -> dict:
    """
    获取指定城市的当前天气信息

    参数:
        city: 城市名称，默认为Beijing

    返回:
        包含天气信息的字典
    """
    try:
        weather_info = service.get_current_weather_info(city)
        if weather_info:
            # 确保返回的是可序列化的JSON数据
            serializable_data = datetime_to_str(weather_info)
            return {
                "status": "success",
                "data": serializable_data,
                "city": city
            }
        else:
            return {
                "status": "error",
                "message": f"无法获取城市 {city} 的天气信息"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"获取天气信息时出错: {str(e)}"
        }


@mcp.tool(description="获取指定城市的未来天气预报")
def get_forecast(city: str = DEFAULT_CITY) -> dict:
    """
    获取指定城市的未来天气预报

    参数:
        city: 城市名称，默认为Beijing

    返回:
        包含天气预报信息的字典
    """
    try:
        forecast_info = service.get_forecast_info(city)
        if forecast_info:
            # 确保返回的是可序列化的JSON数据
            serializable_data = datetime_to_str(forecast_info)
            return {
                "status": "success",
                "data": serializable_data,
                "city": city
            }
        else:
            return {
                "status": "error",
                "message": f"无法获取城市 {city} 的天气预报"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"获取天气预报时出错: {str(e)}"
        }


@mcp.resource("server://info")
async def server_info():
    """服务器信息资源"""
    return {
        "name": SERVER_NAME,
        "version": "1.0.0",
        "description": "获得天气预报信息",
        "tools": ["get_weather", "get_forecast"]
    }

if __name__ == "__main__":
    # 初始化并运行服务器
    # 启动服务器（SSE模式，便于远程连接）
    mcp.run(transport="sse")
    # host = "127.0.0.1", port = 9000
