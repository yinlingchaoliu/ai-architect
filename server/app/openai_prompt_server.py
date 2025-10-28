from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, Runnable
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

class OpenAIPromptServer:
    """GET请求示例类 - 使用Pydantic模型处理输入输出"""

    def __init__(self):
        prompt = ChatPromptTemplate.from_template("告诉我一个关于 {topic} 的笑话")
        self.chain = prompt | ChatOpenAI(model="gpt-4")

    def get_chain(self):
        return self.chain