import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# API配置
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', '')
DEFAULT_CITY = os.getenv('DEFAULT_CITY', 'Beijing')

# OpenWeatherMap API基础URL
OPENWEATHER_BASE_URL = 'https://api.openweathermap.org/data/2.5'

# 验证必要配置
if not OPENWEATHER_API_KEY:
    raise ValueError('请在.env文件中设置OPENWEATHER_API_KEY')