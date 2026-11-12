"""Offline mechanism observations only; no network, provider credentials or speed claims."""
import asyncio
import json
import os
from pathlib import Path
import threading
from contextvars import ContextVar
from importlib.metadata import version, distribution
import hashlib

os.environ['LANGSMITH_TRACING'] = 'false'
os.environ['LANGCHAIN_TRACING_V2'] = 'false'

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, AIMessageChunk
from langchain_core.outputs import ChatResult, ChatGeneration, ChatGenerationChunk
from langchain_core.callbacks import AsyncCallbackHandler
from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware
from langchain.agents.structured_output import ToolStrategy
from pydantic import BaseModel

OUT = Path(__file__).with_name('langchain-mechanism-results.json')
seen = []
scope = ContextVar("offline_attempt_scope", default=None)


class SyncOnly(BaseChatModel):
    @property
    def _llm_type(self):
        return 'offline-sync-only'

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        seen.append(('sync_generate', threading.get_ident()))
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content='ok'))])

    def _stream(self, messages, stop=None, run_manager=None, **kwargs):
        seen.append(('sync_stream', threading.get_ident()))
        yield ChatGenerationChunk(message=AIMessageChunk(content='ok'))


class NativeAsync(SyncOnly):
    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        seen.append(('native_generate', threading.get_ident()))
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content='ok'))])

    async def _astream(self, messages, stop=None, run_manager=None, **kwargs):
        seen.append(('native_stream', threading.get_ident()))
        yield ChatGenerationChunk(message=AIMessageChunk(content='ok'))


class Report(BaseModel):
    value: int


class ToolFake(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


async def main():
    loop_thread = threading.get_ident()
    await SyncOnly().ainvoke('probe')
    async for _ in SyncOnly().astream('probe'):
        pass
    await NativeAsync().ainvoke('probe')
    async for _ in NativeAsync().astream('probe'):
        pass
    checks = {name: thread == loop_thread for name, thread in seen}
    assert checks == {'sync_generate': False, 'sync_stream': False,
                      'native_generate': True, 'native_stream': True}

    # LangChain chunks carry additive usage. Two cumulative snapshots are invalid
    # as additive chunks; this intentionally demonstrates the wrong mapping.
    a = AIMessageChunk(content='', usage_metadata={'input_tokens': 10, 'output_tokens': 1, 'total_tokens': 11})
    b = AIMessageChunk(content='', usage_metadata={'input_tokens': 12, 'output_tokens': 2, 'total_tokens': 14})
    merged = (a + b).usage_metadata
    assert merged['input_tokens'] == 22
    assert merged['total_tokens'] == 25

    events, usage_seen, scopes_seen = [], [], []

    class Capture(AsyncCallbackHandler):
        async def on_llm_end(self, response, **kwargs):
            message = response.generations[0][0].message
            events.append('provider_llm_end')
            scopes_seen.append(scope.get())
            usage_seen.append(message.usage_metadata)

    class Outer(AgentMiddleware):
        async def awrap_model_call(self, request, handler):
            events.append('outer_before')
            try:
                return await handler(request)
            except Exception as error:
                events.append('outer_error:' + type(error).__name__)
                raise

    class Inner(AgentMiddleware):
        async def awrap_model_call(self, request, handler):
            events.append('inner_before')
            token = scope.set('attempt-probe')
            try:
                return await handler(request)
            except Exception as error:
                events.append('inner_error:' + type(error).__name__)
                raise
            finally:
                scope.reset(token)

    model = ToolFake(responses=[AIMessage(content='', tool_calls=[{
        'name': 'Report', 'args': {'value': 'not-an-integer'}, 'id': 'probe-call'
    }], usage_metadata={'input_tokens': 3, 'output_tokens': 2, 'total_tokens': 5})])
    agent = create_agent(model, middleware=[Outer(), Inner()],
                         response_format=ToolStrategy(Report, handle_errors=False))
    error_type = None
    try:
        await agent.ainvoke({'messages': [('user', 'probe')]}, config={'callbacks': [Capture()]})
    except Exception as error:
        error_type = type(error).__name__
    assert error_type == 'StructuredOutputValidationError', error_type
    assert events[:3] == ['outer_before', 'inner_before', 'provider_llm_end'], events
    assert usage_seen[0]['total_tokens'] == 5
    assert scopes_seen == ['attempt-probe']
    assert scope.get() is None

    source_files = [('langchain-core', 'langchain_core/language_models/chat_models.py'),
                    ('langchain-core', 'langchain_core/messages/ai.py'),
                    ('langchain-core', 'langchain_core/runnables/base.py'),
                    ('langchain', 'langchain/agents/factory.py'),
                    ('langchain', 'langchain/agents/middleware/types.py'),
                    ('langchain-openai', 'langchain_openai/chat_models/base.py')]
    fingerprints = []
    for package, relative in source_files:
        path = Path(distribution(package).locate_file(relative))
        fingerprints.append({'package': package, 'path': str(path),
                             'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    result = {
        'date': '2026-11-12', 'status': 'passed', 'scope': 'offline mechanism observations, not performance or provider validation',
        'versions': {name: version(name) for name in ['langchain', 'langchain-core', 'langchain-openai', 'langgraph']},
        'async_method_same_as_event_loop_thread': checks,
        'cumulative_chunk_mis_mapping': {'snapshots': [11, 14], 'framework_additive_total': merged['total_tokens'],
                                       'correct_final_snapshot_total': 14},
        'middleware_and_usage': {'events': events, 'error': error_type, 'provider_usage_observed_before_schema_error': usage_seen,
                                 'async_callback_attempt_scope': scopes_seen, 'scope_reset_after_error': scope.get() is None},
        'source_fingerprints': fingerprints, 'network_calls': 0,
        'not_run': ['TypeScript reference tests', 'live provider', 'load test', 'billing ledger test']
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['source_fingerprints']}, ensure_ascii=False))


if __name__ == '__main__':
    asyncio.run(main())
