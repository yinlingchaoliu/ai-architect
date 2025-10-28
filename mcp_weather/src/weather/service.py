from .api import WeatherAPI
import datetime

class WeatherService:
    """天气服务类，用于处理和格式化天气数据"""
    
    def __init__(self):
        self.api = WeatherAPI()
        
    def get_current_weather_info(self, city):
        """获取并格式化当前天气信息"""
        data = self.api.get_current_weather(city)
        if not data:
            return None
            
        # 解析和格式化天气数据
        weather_info = {
            'city': data.get('name', ''),
            'country': data.get('sys', {}).get('country', ''),
            'temperature': data.get('main', {}).get('temp', 0),
            'feels_like': data.get('main', {}).get('feels_like', 0),
            'humidity': data.get('main', {}).get('humidity', 0),
            'pressure': data.get('main', {}).get('pressure', 0),
            'wind_speed': data.get('wind', {}).get('speed', 0),
            'weather_description': data.get('weather', [{}])[0].get('description', ''),
            'weather_icon': data.get('weather', [{}])[0].get('icon', ''),
            'sunrise': datetime.datetime.fromtimestamp(data.get('sys', {}).get('sunrise', 0)),
            'sunset': datetime.datetime.fromtimestamp(data.get('sys', {}).get('sunset', 0)),
            'update_time': datetime.datetime.fromtimestamp(data.get('dt', 0))
        }
        
        return weather_info
        
    def get_forecast_info(self, city):
        """获取并格式化天气预报信息"""
        data = self.api.get_forecast(city)
        if not data:
            return None
            
        # 按日期分组预报数据
        daily_forecast = {}
        
        for item in data.get('list', []):
            date = datetime.datetime.fromtimestamp(item.get('dt', 0)).strftime('%Y-%m-%d')
            if date not in daily_forecast:
                daily_forecast[date] = []
                
            forecast_item = {
                'time': datetime.datetime.fromtimestamp(item.get('dt', 0)),
                'temperature': item.get('main', {}).get('temp', 0),
                'humidity': item.get('main', {}).get('humidity', 0),
                'weather_description': item.get('weather', [{}])[0].get('description', ''),
                'weather_icon': item.get('weather', [{}])[0].get('icon', ''),
                'wind_speed': item.get('wind', {}).get('speed', 0)
            }
            
            daily_forecast[date].append(forecast_item)
            
        return daily_forecast