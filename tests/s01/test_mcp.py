from pathlib import Path
import json

import pytest
from fastmcp import FastMCP, Context, Client
from fastmcp.client.transports import PythonStdioTransport
from langchain.mcp import MCPAdapter
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from pydantic import BaseModel
from mcp.types import InputRequiredResult, ElicitRequest, ElicitRequestFormParams
from lib_graph import AgentContext, build_agent, final_text

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.asyncio
async def test_native_adapter_real_http_discovery_call_and_resource(math_server):
    async with MCPAdapter(math_server) as adapter:
        tools = await adapter.list_tools()
        calculator = next(t for t in tools if t.name == "calculator")
        result = await calculator.ainvoke({"expression": "2+3*4"})
        assert "14" in str(result)
    async with Client(math_server) as client:
        resource = await client.read_resource("server://info")
        assert "MathTools" in str(resource)


@pytest.mark.asyncio
async def test_native_adapter_stdio_process(monkeypatch):
    monkeypatch.setenv("MCP_TRANSPORT", "stdio")
    transport = PythonStdioTransport(
        ROOT / "mcp_server_math/main.py", env={"MCP_TRANSPORT": "stdio"}, cwd=str(ROOT))
    async with MCPAdapter(Client(transport)) as adapter:
        tools = await adapter.list_tools()
        result = await next(t for t in tools if t.name == "calculator").ainvoke(
            {"expression": "6*7"})
        assert "42" in str(result)


@pytest.mark.asyncio
async def test_existing_mcp_client_manager_new_sdk(math_server):
    from mcp_client_manager.src.core.mcp_client import MCPProtocolClient
    client = MCPProtocolClient()
    try:
        await client.register_server("math", math_server)
        assert "math_calculator" in {t["function"]["name"] for t in client.get_all_tool_schemas()}
        assert "9" in await client.call_tool("math_calculator", {"expression": "4+5"})
    finally:
        await client.close_all()


@pytest.mark.asyncio
async def test_agentmcp_actual_agent_tool_loop(math_server, model_factory):
    from agentmcp.agentmcp import run_query
    model = model_factory([
        AIMessage(content="", tool_calls=[{"name": "calculator", "args": {"expression": "3*7"}, "id": "math-1"}]),
        AIMessage(content="21"),
    ])
    result = await run_query("3*7", target=math_server, model=model)
    assert result["messages"][-1].text == "21"
    assert any(isinstance(m, ToolMessage) and "21" in str(m.content) for m in result["messages"])


@pytest.mark.asyncio
async def test_mcp_elicitation_interrupts_and_resumes_without_early_effect(model_factory):
    class Destination(BaseModel):
        city: str

    server = FastMCP("elicitation-test")
    effects = []

    @server.tool
    async def choose_city(ctx: Context) -> str | InputRequiredResult:
        """Ask using the modern input-required protocol before any effect."""
        answer = (ctx.input_responses or {}).get("destination")
        if answer is None:
            return InputRequiredResult(inputRequests={
                "destination": ElicitRequest(params=ElicitRequestFormParams(
                    message="Which city?", requestedSchema=Destination.model_json_schema()))
            })
        if answer.action != "accept":
            return "declined"
        city = Destination.model_validate(answer.content).city
        effects.append(city)
        return city

    async with MCPAdapter(server) as adapter:
        tools = await adapter.list_tools()
        model = model_factory([
            AIMessage(content="", tool_calls=[{"name": "choose_city", "args": {}, "id": "city-1"}]),
            AIMessage(content="Shanghai"),
        ])
        agent = build_agent(model, tools, checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": "mcp-input"}}
        paused = await agent.ainvoke({"messages": [("user", "choose")]}, config,
                                     context=AgentContext("mcp-input"))
        request = paused["__interrupt__"][0].value
        assert request["type"] == "mcp_elicitation"
        assert effects == []
        answers = {r["key"]: {"action": "accept", "content": {"city": "Shanghai"}}
                   for r in request["requests"]}
        done = await agent.ainvoke(Command(resume={"responses": answers}), config,
                                   context=AgentContext("mcp-input"))
        assert final_text(done) == "Shanghai"
        assert effects == ["Shanghai"]


@pytest.mark.asyncio
async def test_manager_and_sdk_router_dispatch_actual_http_tool(math_server, monkeypatch):
    from openai import AsyncOpenAI
    import httpx
    from mcp_client_manager.src.core import mcp_manager
    from mcp_client_manager.src.core.mcp_router import LLMMCP
    monkeypatch.setattr(mcp_manager, "MCP_SERVERS", {"math": math_server})
    manager = mcp_manager.MCPManager()
    await manager.initialize()
    router = LLMMCP(manager, "offline")
    await router.llm_client.close()

    def respond(request):
        return httpx.Response(200, json={"id": "router-test", "object": "chat.completion", "created": 1,
            "model": "test", "choices": [{"index": 0, "message": {"role": "assistant", "content": None,
                "tool_calls": [{"id": "math-r", "type": "function", "function": {
                    "name": "math_calculator", "arguments": "{\"expression\": \"7*8\"}"}}]},
                "finish_reason": "tool_calls"}]})

    router.llm_client = AsyncOpenAI(api_key="offline", max_retries=0,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(respond)))
    try:
        assert "56" in await router.process_user_request("7*8")
    finally:
        await manager.cleanup()
        await router.llm_client.close()


@pytest.mark.asyncio
async def test_manager_keeps_nested_tool_schema(monkeypatch):
    from mcp_client_manager.src.core import mcp_client

    class Details(BaseModel):
        city: str
        nights: int

    server = FastMCP("nested-schema")

    @server.tool
    def itinerary(details: Details) -> str:
        """Summarize typed trip details."""
        return f"{details.city}:{details.nights}"

    original_client = Client
    monkeypatch.setattr(mcp_client, "Client", lambda target: original_client(server))
    manager = mcp_client.MCPProtocolClient()
    try:
        await manager.register_server("trip", "in-process-test")
        schema = manager.get_all_tool_schemas()[0]["function"]["parameters"]
        # The wire schema must retain every nested constraint, whether the SDK
        # dereferences it inline or uses $defs/$ref.
        details = schema["properties"]["details"]
        if "$ref" in details:
            details = schema["$defs"][details["$ref"].split("/")[-1]]
        assert details["properties"]["nights"]["type"] == "integer"
        assert "Shanghai:2" in await manager.call_tool("trip_itinerary", {
            "details": {"city": "Shanghai", "nights": 2}})
    finally:
        await manager.close_all()
