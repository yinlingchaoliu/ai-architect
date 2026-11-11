"""A current-API entry point; the framework owns the agent's tool loop."""

from dataclasses import dataclass
from collections.abc import Callable, Sequence
from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware, ModelCallLimitMiddleware
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import BaseTool


@dataclass(frozen=True, slots=True)
class AgentContext:
    """Invocation data supplied by the caller, never inferred from a prompt."""

    request_id: str
    user_id: str = "local"


def build_agent(
    model: str | BaseChatModel,
    tools: Sequence[BaseTool | Callable[..., Any]] = (),
    *,
    system_prompt: str = "You are a helpful assistant.",
    response_format: Any = None,
    middleware: Sequence[AgentMiddleware] = (),
    checkpointer: Any = None,
    store: Any = None,
    max_model_calls: int = 8,
    name: str | None = None,
):
    """Return the compiled graph, including its native typed event API."""
    if max_model_calls < 1:
        raise ValueError("max_model_calls must be positive")
    return create_agent(
        model,
        tools=tools,
        system_prompt=system_prompt,
        context_schema=AgentContext,
        response_format=response_format,
        middleware=[
            ModelCallLimitMiddleware(run_limit=max_model_calls, exit_behavior="error"),
            *middleware,
        ],
        checkpointer=checkpointer,
        store=store,
        name=name,
    )


def final_text(state: dict[str, Any]) -> str:
    """Read final AI text without stringifying structured content blocks."""
    for message in reversed(state.get("messages", [])):
        if isinstance(message, AIMessage):
            return message.text
    raise ValueError("agent state contains no AI message")
