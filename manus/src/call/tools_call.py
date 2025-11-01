from typing import Literal
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

@tool
def weather_tool(weather: Literal["晴朗的", "多云的", "多雨的","下雪的"]) -> None:
    """Describe the weather"""
    pass


model = ChatOpenAI(model="gpt-4o")
model_with_tools = model.bind_tools([weather_tool])
image_url_1 = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
image_url_2 = "https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/Morning_in_China_Snow_Town.jpg/1280px-Morning_in_China_Snow_Town.jpg"

message = HumanMessage(
    content=[
        {"type": "text", "text": "用中文描述两张图片中的天气"},
        {"type": "image_url", "image_url": {"url": image_url_1}},
        {"type": "image_url", "image_url": {"url": image_url_2}},
    ],
)
response = model_with_tools.invoke([message])
print(response.tool_calls)
