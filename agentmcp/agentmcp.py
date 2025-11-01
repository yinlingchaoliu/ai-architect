# 首先安装必要的依赖包：
# pip install langchain langchain-community langchain-mcp-adapters langchain-openai python-dotenv

import asyncio
import os

from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()  # 加载环境变量，例如 OPENAI_API_KEY


async def main():

    client = MultiServerMCPClient({
        "weather": {
            "url": "http://localhost:8000/sse",  # 你的SSE URL
            "transport": "sse",
        }
    })

    tools = await client.get_tools()
    print("✅ 从MCP服务器获取到的工具:")
    for tool in tools:
        print(f"   - {tool.name}: {tool.description}")

    # 4. 设置LLM和Agent
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    # Agent提示词模板，指导其如何使用工具
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个有用的助手，可以调用工具来获取信息。请根据用户需求使用合适的工具。"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    # 创建能理解工具调用的Agent
    agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # 5. 使用Agent执行任务（示例：查询天气）
    print("\n🤖 Agent开始处理用户请求...")
    try:
        result = await agent_executor.ainvoke({
            "input": "今天北京的天气怎么样？"  # 请确保MCP服务提供天气查询工具
        })
        print(f"\n📝 最终回答: {result['output']}")
    except Exception as e:
        print(f"❌ 执行过程中出现错误: {e}")


# 运行示例
if __name__ == "__main__":
    asyncio.run(main())