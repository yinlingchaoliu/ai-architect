import pytest
from pydantic import BaseModel
from langchain.agents.middleware import dynamic_prompt
from langchain.agents.structured_output import ToolStrategy
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command, interrupt
from lib_graph import AgentContext, build_agent, final_text


class Report(BaseModel):
    total: int


def call(name, args, call_id="call-1"):
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": call_id}])


def test_tool_loop_context_middleware_and_structured_output(model_factory):
    observations = []

    @tool
    def add(a: int, b: int, runtime: ToolRuntime[AgentContext]) -> int:
        """Add two numbers for this invocation."""
        observations.append((runtime.context.request_id, a, b))
        return a + b

    prompts = []

    @dynamic_prompt
    def request_prompt(request):
        prompts.append(request.runtime.context.request_id)
        return f"request={request.runtime.context.request_id}"

    model = model_factory([call("add", {"a": 2, "b": 3}),
                           call("Report", {"total": 5}, "report-1")])
    agent = build_agent(model, [add], middleware=[request_prompt],
                        response_format=ToolStrategy(Report, handle_errors=False))
    result = agent.invoke({"messages": [{"role": "user", "content": "2+3"}]},
                          context=AgentContext("request-a"))
    assert result["structured_response"] == Report(total=5)
    assert observations == [("request-a", 2, 3)]
    assert prompts == ["request-a", "request-a"]
    assert any(isinstance(m, ToolMessage) and m.tool_call_id == "call-1"
               for m in result["messages"])


def test_invalid_structured_output_is_not_reported_as_success(model_factory):
    agent = build_agent(model_factory([call("Report", {"total": "invalid"})]),
                        response_format=ToolStrategy(Report, handle_errors=False))
    with pytest.raises(Exception, match="(Report|validation|structured)"):
        agent.invoke({"messages": [("user", "report")]}, context=AgentContext("invalid"))


def test_framework_model_call_limit_stops_unbounded_tool_loop(model_factory):
    @tool
    def again() -> str:
        """Return another intermediate result."""
        return "continue"

    agent = build_agent(model_factory([call("again", {})]), [again], max_model_calls=2)
    with pytest.raises(Exception, match="(?i)(model call|model_call|limit)"):
        agent.invoke({"messages": [("user", "loop")]}, context=AgentContext("limited"))


def test_standard_content_blocks_preserve_text():
    message = AIMessage(content=[{"type": "text", "text": "one"},
                                 {"type": "text", "text": "two"}])
    assert final_text({"messages": [message]}) == "onetwo"
    assert all(block["type"] == "text" for block in message.content_blocks)
    with pytest.raises(ValueError):
        final_text({"messages": []})


def test_v3_event_projection_has_text_state_and_final_usage(model_factory):
    message = AIMessage(content="streamed answer", usage_metadata={
        "input_tokens": 2, "output_tokens": 3, "total_tokens": 5})
    agent = build_agent(model_factory([message]))
    stream = agent.stream_events({"messages": [("user", "hello")]}, version="v3",
                                 context=AgentContext("stream"))
    texts = [str(m.text) for m in stream.messages]
    assert "streamed answer" in "".join(texts)
    assert final_text(stream.output) == "streamed answer"
    assert stream.output["messages"][-1].usage_metadata["total_tokens"] == 5


@pytest.mark.asyncio
async def test_async_v3_stream(model_factory):
    agent = build_agent(model_factory([AIMessage(content="async answer")]))
    stream = await agent.astream_events({"messages": [("user", "hello")]}, version="v3",
                                        context=AgentContext("async-stream"))
    texts = []
    async for message in stream.messages:
        async for text in message.text:
            texts.append(text)
    assert "async answer" in "".join(texts)
    assert final_text(await stream.output()) == "async answer"


def test_interrupt_resume_keeps_checkpoint_and_defers_side_effect(model_factory):
    effects = []

    @tool
    def wait_for_input() -> str:
        """Wait for input before recording an effect."""
        answer = interrupt({"question": "supply a value"})
        effects.append(answer)
        return str(answer)

    agent = build_agent(model_factory([call("wait_for_input", {}), AIMessage(content="done")]),
                        [wait_for_input], checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "resume-test"}}
    first = agent.invoke({"messages": [("user", "wait")]}, config,
                         context=AgentContext("paused"))
    assert first["__interrupt__"]
    assert effects == []
    second = agent.invoke(Command(resume="answer"), config,
                          context=AgentContext("paused"))
    assert final_text(second) == "done"
    assert effects == ["answer"]
