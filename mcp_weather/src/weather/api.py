import requests

from ..config.settings import OPENWEATHER_API_KEY, OPENWEATHER_BASE_URL

class WeatherAPI:
    """天气API接口类，用于获取天气数据"""
    
    def __init__(self):
        self.api_key = OPENWEATHER_API_KEY
        self.base_url = OPENWEATHER_BASE_URL
        
    def get_current_weather(self, city):
        """获取指定城市的当前天气"""
        url = f"{self.base_url}/weather"
        params = {
            'q': city,
            'appid': self.api_key,
            'units': 'metric',  # 使用摄氏度
            'lang': 'zh_cn'  # 使用中文
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()  # 如果请求失败，抛出异常
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"获取天气数据失败: {e}")
            return None
            
    def get_forecast(self, city):
        """获取指定城市的天气预报（5天/3小时预报）"""
        url = f"{self.base_url}/forecast"
        params = {
            'q': city,
            'appid': self.api_key,
            'units': 'metric',
            'lang': 'zh_cn'
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"获取天气预报失败: {e}")
            return None