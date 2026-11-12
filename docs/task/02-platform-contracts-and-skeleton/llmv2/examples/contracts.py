"""PROPOSED interface/DTO sketch only. No executable LLM implementation.

Source for design review; no credentials, network clients, or runtime side effects.
The enclosing Markdown specifies lifecycle, trust, and error semantics.
"""
from __future__ import annotations

from collections.abc import AsyncIterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncContextManager, Literal, Protocol, TypeVar

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.prompt_values import PromptValue
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)
ModelInput = str | PromptValue | Sequence[BaseMessage]


@dataclass(frozen=True, slots=True)
class CallContext:
    request_id: str
    tenant_id: str
    run_id: str | None
    budget_ref: str
    deadline_at: datetime  # UTC-aware; convert remaining time to monotonic locally
    allowed_profiles: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ModelBinding:
    profile_id: str
    profile_revision: str
    provider_id: str
    provider_revision: str
    model_id: str
    adapter_revision: str
    capability_revision: str
    defaults_digest: str


@dataclass(frozen=True, slots=True)
class Usage:
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    cache_read_tokens: int | None = None  # subset of input, not additional total
    cache_write_tokens: int | None = None
    reasoning_tokens: int | None = None  # subset of output
    source: Literal["provider", "unknown"] = "unknown"


@dataclass(frozen=True, slots=True)
class TokenEstimate:
    input_tokens: int | None
    output_tokens_bound: int | None
    estimator_revision: str
    confidence: Literal["exact_tokenizer", "conservative", "heuristic", "unknown"]


@dataclass(frozen=True, slots=True)
class GenerationOptions:
    max_output_tokens: int | None = None
    temperature: float | None = None
    stop: tuple[str, ...] | None = None
    reasoning_mode: Literal["off", "on", "provider_default"] | None = None
    reasoning_effort: str | None = None
    require_complete: bool = True
    # Runtime freezes/validates these. Frozen dataclass alone does not freeze dicts.
    tools: tuple[Mapping[str, Any], ...] = ()
    tool_choice: str | Mapping[str, Any] | None = None
    provider_options: Mapping[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class LLMResponse:
    message: AIMessage
    call_id: str
    attempt_id: str
    binding: ModelBinding
    usage: Usage
    completion_status: Literal["complete", "incomplete"]
    accounting_status: Literal["settled", "pending", "not_required"]
    estimate: TokenEstimate | None = None


class StreamSession(Protocol):
    def __aiter__(self) -> AsyncIterator[AIMessageChunk]: ...
    async def result(self) -> LLMResponse: ...
    async def aclose(self) -> None: ...


class LLMClient(Protocol):
    async def achat(
        self, input: ModelInput, *,
        context: CallContext, profile: str = "default",
        options: GenerationOptions | None = None,
    ) -> AIMessage: ...

    async def generate(
        self, input: ModelInput, *,
        context: CallContext, profile: str = "default",
        options: GenerationOptions | None = None,
    ) -> LLMResponse: ...

    def stream(
        self, input: ModelInput, *,
        context: CallContext, profile: str = "default",
        options: GenerationOptions | None = None,
    ) -> AsyncContextManager[StreamSession]: ...

    def chat_model(self, profile: str, revision: str | None = None) -> BaseChatModel: ...

    def scope(self, context: CallContext) -> AsyncContextManager[None]: ...

    async def structured(
        self, schema: type[T], input: ModelInput, *,
        context: CallContext, profile: str = "default",
        options: GenerationOptions | None = None,
        method: Literal["function_calling", "json_schema"] = "function_calling",
    ) -> tuple[T, LLMResponse]: ...


class BudgetPort(Protocol):
    async def reserve(self, *, attempt_id: str, budget_ref: str, bounds: Mapping[str, int]) -> str: ...
    async def settle(self, *, attempt_id: str, reservation_id: str, usage: Usage) -> None: ...
    async def mark_unknown(self, *, attempt_id: str, reservation_id: str, reason: str) -> None: ...


class QuotaLease(Protocol):
    async def mark_dispatched(self) -> None: ...
    async def release(self, *, outcome: str) -> None: ...


class QuotaBackend(Protocol):
    # Atomic eligibility over RPM/TPM/concurrency. Queuing belongs to governor.
    async def try_admit(self, *, quota_group: str, tenant_id: str, token_bound: int) -> QuotaLease | None: ...


class AdapterHandle(Protocol):
    # Handle is pinned; underlying model is private and never returned by facade.
    def capabilities(self, binding: ModelBinding) -> Mapping[str, Any]: ...
    def build_native_model(self, *, connection_lease: Any) -> BaseChatModel: ...
    def normalize_usage(self, message: AIMessage) -> Usage: ...
    def normalize_error(self, error: Exception, *, phase: str) -> Exception: ...


class AdapterFactory(Protocol):
    def descriptor(self) -> Mapping[str, Any]: ...
    async def create(self, *, provider_revision: Mapping[str, Any]) -> AdapterHandle: ...


class RegistrationHandle(Protocol):
    async def retire(self, *, drain_deadline_at: datetime) -> None: ...


class AdapterRegistry(Protocol):
    async def register(self, factory: AdapterFactory) -> RegistrationHandle: ...
