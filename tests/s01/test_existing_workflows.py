import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from langchain_core.messages import AIMessage


def test_conference_graph_runs_original_roles_and_stops(monkeypatch, model_factory):
    from graph_discussion.agents import base_agent
    from graph_discussion.graph.graph import create_conference_graph
    model = model_factory([
        AIMessage(content=[{"type": "text", "text": "【讨论主题】\n1. 技术商业研究\n【所需专家】\n技术 商业 研究"}]),
        AIMessage(content="first question"),
        AIMessage(content="technical result"), AIMessage(content="business result"),
        AIMessage(content="research result"), AIMessage(content="round summary"),
        AIMessage(content="结束"),
        AIMessage(content="【技术落地方案】tech【商业落地方案】business【研究落地方案】research"),
    ])
    monkeypatch.setattr(base_agent, "ChatOpenAI", lambda **kwargs: model)
    graph = create_conference_graph()
    state = graph.invoke({
        "user_query": "sample", "current_round": 0, "max_rounds": 2,
        "requirement_analysis": "", "discussion_topics": [], "required_experts": [],
        "moderator_questions": [], "expert_discussions": [], "current_question": "",
        "round_summaries": [], "final_summary": "", "implementation_plans": {},
        "should_continue": False,
    })
    assert len(state["expert_discussions"]) == 1
    assert set(state["expert_discussions"][0]) == {"技术专家", "商业专家", "研究专家"}
    assert state["implementation_plans"] == {"技术专家": "tech", "商业专家": "business", "研究专家": "research"}
    assert state["should_continue"] is False


@pytest.mark.asyncio
async def test_manus_graph_executes_each_subtask_once():
    from manus.src.graph.workflow import create_workflow
    from manus.src.graph.nodes.plan_node import set_agent_pool as set_plan
    from manus.src.graph.nodes.execute_node import set_agent_pool as set_execute
    calls = []

    async def execute(task):
        calls.append(task["task"])
        return {"status": "success", "content": task["task"]}

    planning = SimpleNamespace(run=AsyncMock(return_value={"subtasks": [
        {"id": 1, "description": "first", "recommended_agent": "worker"},
        {"id": 2, "description": "second", "recommended_agent": "worker"},
    ]}))
    worker = SimpleNamespace(run=execute, llm_manager=object())
    pool = SimpleNamespace(get_agent=lambda name: planning if name == "planning_agent" else worker)
    set_plan(pool)
    set_execute(pool)
    try:
        graph = create_workflow().compile()
        state = await graph.ainvoke({"messages": [], "current_task": "do work", "subtasks": [],
            "current_agent": "", "tool_results": [], "execution_path": [], "is_complete": False,
            "plan": None}, config={"recursion_limit": 24})
        assert calls == ["first", "second"]
        assert len(state["tool_results"]) == 2
        assert state["is_complete"] is True
    finally:
        set_plan(None)
        set_execute(None)


@pytest.mark.asyncio
async def test_raw_sdk_v3_manus_tool_calls_and_usage():
    from openai import AsyncOpenAI
    from manus.src.llm.manager import LLMManager
    captured = []

    def respond(request):
        captured.append(json.loads(request.content))
        return httpx.Response(200, json={
            "id": "chatcmpl-test", "object": "chat.completion", "created": 1, "model": "test-model",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": None,
                "tool_calls": [{"id": "tool-1", "type": "function", "function": {
                    "name": "calculate", "arguments": "{\"x\": 2}"}}]}, "finish_reason": "tool_calls"}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5}})

    manager = LLMManager({"models": {"provider": "openai", "model_name": "deepseek-flash", "api_key": "offline"}})
    await manager.clients["default"].close()
    client = AsyncOpenAI(api_key="offline", max_retries=0,
                         http_client=httpx.AsyncClient(transport=httpx.MockTransport(respond)))
    manager.clients["default"] = client
    try:
        result = await manager.generate([{"role": "user", "content": "test"}], tools=[{
            "type": "function", "function": {"name": "calculate", "parameters": {"type": "object"}}}])
        assert result.tool_calls[0]["function"]["name"] == "calculate"
        assert result.usage.total_tokens == 5
        assert manager.total_usage["default"].total_tokens == 5
        assert captured[0]["tools"][0]["function"]["name"] == "calculate"
        assert captured[0]["model"] == "deepseek-flash"
        assert captured[0]["thinking"] == {"type": "disabled"}
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_travel_coordinator_existing_iteration_contract(monkeypatch):
    from agent_muti.src.core.agent_system import EnhancedDynamicAgentSystem
    from agent_muti.src.models.agent_models import AgentResponse, AgentType
    system = EnhancedDynamicAgentSystem("offline")
    worker_name = next(iter(system.coordinator.agent_registry))
    worker = system.coordinator.agent_registry[worker_name]
    monkeypatch.setattr(worker, "process_request", AsyncMock(return_value=AgentResponse(
        agent_type=AgentType.CUSTOM, content="verified intermediate", data={"source": "stub"}, confidence=1.0)))

    async def decide(messages, **kwargs):
        phase = system.coordinator.step
        if phase == "think":
            return json.dumps({"should_complete": False, "missing_info": ["sample"], "acquired_info": {}})
        if phase == "plan":
            return json.dumps({"required_agents": [worker_name], "expected_outputs": {worker_name: "sample"}})
        if phase == "next":
            return json.dumps({"should_terminate": True})
        return "final travel summary"

    monkeypatch.setattr(system.coordinator, "_call_llm", decide)
    await system.initialize_system()
    try:
        response = await system.process_query("sample trip")
        assert response.content == "final travel summary"
        assert response.metadata["iterations"] == 1
        assert response.data["iteration_result"]["final_result"]["agent_responses"][worker_name].content == "verified intermediate"
    finally:
        await system.shutdown_system()
        await system.coordinator.llm_client.close()
        for agent in system.coordinator.agent_registry.values():
            await agent.llm_client.close()


def test_discussion_sync_sdk_v3_serializes_history_and_clears_it():
    from openai import OpenAI
    from agent_muti_discussion.src.agents.analyzer_agent import AnalyzerAgent
    seen = []

    def respond(request):
        seen.append(json.loads(request.content))
        return httpx.Response(200, json={"id": "sync-test", "object": "chat.completion",
            "created": 1, "model": "test-model", "choices": [{"index": 0,
                "message": {"role": "assistant", "content": "analysis result"}, "finish_reason": "stop"}]})

    agent = AnalyzerAgent()
    agent.llm.close()
    agent.llm = OpenAI(api_key="offline", max_retries=0,
                       http_client=httpx.Client(transport=httpx.MockTransport(respond)))
    try:
        assert agent.generate_response("sample") == "analysis result"
        assert seen[0]["messages"][-1]["role"] == "user"
        assert agent.get_history()[-1] == {"role": "assistant", "content": "analysis result"}
        agent.clear_history()
        assert len(agent.get_history()) == 1
        assert agent.get_history()[0]["role"] == "system"
    finally:
        agent.llm.close()


def test_manus_explicit_model_environment_overrides_file_without_mutating_it(monkeypatch, tmp_path):
    from manus.src.utils.config import ConfigManager
    path = tmp_path / "config.toml"
    source = '[llm.models]\nprovider="openai"\nmodel_name="old-model"\napi_key="placeholder"\nbase_url="https://old.invalid"\n'
    path.write_text(source)
    monkeypatch.setenv("OPENAI_MODEL", "deepseek-flash")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.deepseek.com")
    config = ConfigManager(str(path))
    effective = config.get_llm_config()["models"]
    assert effective["model_name"] == "deepseek-flash"
    assert effective["base_url"] == "https://api.deepseek.com"
    assert effective["api_key"] == "s01-offline-test-key"
    assert path.read_text() == source
    assert config.config["llm"]["models"]["model_name"] == "old-model"
