"""Runnable current-API example; importing it does not contact a model."""
import os
from uuid import uuid4

from langchain.tools import ToolRuntime, tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from .runtime import AgentContext, build_agent, final_text


@tool
def search(query: str, runtime: ToolRuntime[AgentContext]) -> dict:
    """Return explicitly labelled demonstration weather data for a query."""
    return {
        "query": query,
        "request_id": runtime.context.request_id,
        "source": "demo-only; not a real weather provider",
        "temperature_celsius": 30 if "上海" in query or "shanghai" in query.lower() else 35,
    }


def create_demo_agent(model=None):
    model = model if model is not None else ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "deepseek-flash"), temperature=0,
        extra_body={"thinking": {"type": "disabled"}} if os.getenv("OPENAI_MODEL", "deepseek-flash").startswith("deepseek-") else {},
        use_responses_api=False
    )
    return build_agent(
        model, [search],
        system_prompt="Use the tool when needed. Clearly label its data as demonstration data.",
        checkpointer=InMemorySaver(), name="weather-demo",
    )


def main():
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv(".env.local"))
    load_dotenv()
    agent = create_demo_agent()
    request_id = str(uuid4())
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "上海的示例天气是多少？"}]},
        config={"configurable": {"thread_id": request_id}},
        context=AgentContext(request_id=request_id),
    )
    print(final_text(result))


if __name__ == "__main__":
    main()
