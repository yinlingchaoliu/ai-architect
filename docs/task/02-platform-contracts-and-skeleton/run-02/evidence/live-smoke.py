"""Bounded user-authorized DeepSeek verification through lib_llm/lib_request.

Only lib_llm loads private configuration. Receipts contain no prompts, replies,
keys, raw provider exceptions, headers, or complete environment values.
"""
import asyncio
from dataclasses import asdict
from datetime import datetime, timezone
import json
import hashlib
from pathlib import Path
from urllib.parse import urlparse

from pydantic import BaseModel
from lib_llm import LLMRuntime, load_settings
from lib_request import OpenAIAssistantClient

OUT = Path(__file__).with_name('live-model.json')


class Smoke(BaseModel):
    marker: str


async def main():
    settings = load_settings()
    profile = next(p for p in settings.profiles if p.name == 'default')
    receipt = {'started_at': datetime.now(timezone.utc).isoformat(),
               'provider_host': urlparse(profile.provider.base_url).hostname,
               'model': profile.model, 'checks': [], 'usage': [], 'max_attempts': 1,
               'output_cap_per_request': 64, 'configuration_owner': 'lib_llm'}
    # Scope is the user-specified model and official host, never another configured provider.
    if profile.model != 'deepseek-flash' or receipt['provider_host'] != 'api.deepseek.com':
        receipt['status'] = 'not_run_configuration_outside_scope'
        OUT.write_text(json.dumps(receipt, indent=2) + '\n')
        print(json.dumps({k:v for k,v in receipt.items() if k!='usage'}))
        return
    profile = profile.model_copy(update={'max_output_tokens': 64})
    settings = settings.model_copy(update={'profiles': (profile,), 'max_attempts': 1, 'total_timeout': 30})
    try:
        async with LLMRuntime(settings) as runtime:
            # Invoke the actual legacy facade through its sync bridge on a worker thread;
            # transport still belongs to the runtime's single main event loop.
            client = OpenAIAssistantClient(runtime=runtime)
            body = json.loads(await asyncio.to_thread(client.request, 'Reply with exactly S02_OK.'))
            receipt['checks'].append({'name': 'lib_request_to_lib_llm_text', 'passed': body['choices'][0]['message']['content'].strip() == 'S02_OK'})
            receipt['usage'].append(body.get('usage'))
            async with runtime.stream('Reply with exactly STREAM_OK.') as stream:
                text = ''.join([c.text async for c in stream])
                result = await stream.result()
            receipt['checks'].append({'name': 'lib_llm_stream', 'passed': text.strip() == 'STREAM_OK'})
            receipt['usage'].append(asdict(result.usage))
            parsed, structured_response = await runtime.structured(Smoke, 'Return marker=STRUCTURED_OK using the required schema.')
            receipt['checks'].append({'name': 'managed_structured', 'passed': parsed.marker == 'STRUCTURED_OK'})
            receipt['runtime_connection_pools'] = runtime.snapshot()['connection_pools']
            receipt['attempt_outcomes'] = [e['status'] for e in runtime.events if e['event'] == 'attempt.finished']
            receipt['usage'] = [e['usage'] for e in runtime.events if e['event'] == 'attempt.finished' and 'usage' in e]
            receipt['status'] = 'passed' if all(c['passed'] for c in receipt['checks']) else 'failed_expectation'
        receipt['runtime_closed'] = runtime._closed
    except Exception as error:
        receipt['status'] = 'failed'
        receipt['error_type'] = type(error).__name__
        receipt['error_code'] = getattr(error, 'code', None)
        receipt['http_status'] = getattr(error, 'status', None)
    receipt['finished_at'] = datetime.now(timezone.utc).isoformat()
    root = Path(__file__).resolve().parents[5]
    receipt['candidate_sources'] = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for directory in [root/'lib_llm/src', root/'lib_request/src']
        for p in directory.rglob('*.py')}
    OUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='usage'}, ensure_ascii=False))


if __name__ == '__main__':
    asyncio.run(main())
