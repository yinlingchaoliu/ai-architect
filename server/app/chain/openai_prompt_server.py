from fastapi import FastAPI
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
from langserve import add_routes

def register_route(app:FastAPI,config:dict):
    """注册RAG相关路由[citation:6]"""
    server = OpenAIPromptServer()
    # 使用add_routes注册LangChain链[citation:3]
    path = config.get("path", "")
    add_routes(app,server.get_chain(),path=path)
    print("注册path: "+path)
    print(config)


class OpenAIPromptServer:
    """GET请求示例类 - 使用Pydantic模型处理输入输出"""

    def __init__(self):
        prompt = ChatPromptTemplate.from_template("告诉我一个关于 {topic} 的笑话")
        self.chain = prompt | ChatOpenAI(model="gpt-4")

    def get_chain(self):
        return self.chain