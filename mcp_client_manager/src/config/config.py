# config.py
"""MCP服务器配置 - 完全解耦"""
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

openai_base_url = os.getenv('OPENAI_BASE_URL')
openai_api_key = os.getenv('OPENAI_API_KEY')

MCP_SERVERS = {
    "weather_tools": "http://127.0.0.1:8000/sse",
    "math_tools": "http://127.0.0.1:8001/sse",
}

LLM_CONFIG = {
    "api_key": openai_api_key,  # 设置为您的OpenAI API密钥
    "model": "gpt-3.5-turbo"
}