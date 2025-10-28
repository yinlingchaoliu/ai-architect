
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

class OpenAIServer:
    """GET请求示例类 - 使用Pydantic模型处理输入输出"""

    def __init__(self):
        self.chain = ChatOpenAI(model="gpt-4")

    def get_chain(self):
        return self.chain