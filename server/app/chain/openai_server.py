from fastapi import FastAPI
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
from langserve import add_routes

"""
路由自动注册
"""
def register_route(app:FastAPI,config:dict):
    """注册RAG相关路由[citation:6]"""
    server = OpenAIServer()
    # 使用add_routes注册LangChain链[citation:3]
    path = config.get("path", "")
    add_routes(app,server.get_chain(),path=path)
    print("注册path: "+path)
    print(config)

class OpenAIServer:
    """GET请求示例类 - 使用Pydantic模型处理输入输出"""

    def __init__(self):
        self.chain = ChatOpenAI(model="gpt-4")

    def get_chain(self):
        return self.chain