"""LangChain create_agent + built-in MCPAdapter, using Streamable HTTP."""
import asyncio
import os
from uuid import uuid4

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain.mcp import MCPAdapter
from langchain_openai import ChatOpenAI


async def run_query(query: str, *, target=None, model=None, response_format=None):
    """Discover and execute inside the adapter context; propagate failures."""
    target = target if target is not None else os.getenv(
        "MCP_WEATHER_URL", "http://127.0.0.1:8000/mcp"
    )
    model = model if model is not None else ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "deepseek-flash"), temperature=0,
        extra_body={"thinking": {"type": "disabled"}} if os.getenv("OPENAI_MODEL", "deepseek-flash").startswith("deepseek-") else {},
        use_responses_api=False
    )
    async with MCPAdapter(target) as adapter:
        tools = await adapter.list_tools()
        agent = create_agent(
            model, tools,
            system_prompt="Use tools when needed and report their results accurately.",
            middleware=[ModelCallLimitMiddleware(run_limit=8, exit_behavior="error")],
            response_format=response_format,
            name="mcp-assistant",
        )
        return await agent.ainvoke(
            {"messages": [{"role": "user", "content": query}]},
            config={"run_name": f"mcp-query-{uuid4()}"},
        )


async def main():
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv(".env.local"))
    load_dotenv()
    result = await run_query("今天北京的天气怎么样？")
    print(result["messages"][-1].text)


if __name__ == "__main__":
    asyncio.run(main())
