"""Bounded live validation using only explicit project model configuration.

No keys, full URLs, prompts or raw provider errors are written to the receipt.
Run separately from the deterministic suite.
"""
import asyncio
from datetime import datetime, timezone
from pathlib import Path
import json
import os
from urllib.parse import urlparse

from dotenv import dotenv_values
from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain.agents.structured_output import ToolStrategy
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/task/01-langchain-upgrade/run-01/evidence/live-model.json"


class SmokeReport(BaseModel):
    marker: str


async def main():
    values = {**{k: v for k, v in dotenv_values(ROOT / ".env").items() if v}, **{k: v for k, v in dotenv_values(ROOT / ".env.local").items() if v}, **os.environ}
    key = values.get("OPENAI_API_KEY")
    base = values.get("OPENAI_BASE_URL")
    model_name = values.get("OPENAI_MODEL") or values.get("OPENAI_MODEL_NAME") or "deepseek-flash"
    result = {"date": "2026-11-12", "started_at": datetime.now(timezone.utc).isoformat(),
              "configuration_source": "project .env.local / explicit environment",
              "provider_host": urlparse(base).hostname if base else "api.openai.com",
              "model": model_name, "transport": "chat_completions", "max_retries": 0, "thinking": "disabled" if model_name.startswith("deepseek-") else None,
              "checks": [], "usage": []}
    if not key:
        result["status"] = "not_run_missing_project_key"
        OUT.write_text(json.dumps(result, indent=2) + "\n")
        return
    model = ChatOpenAI(model=model_name, api_key=key, base_url=base, temperature=0,
                       timeout=30, max_retries=0, max_tokens=128, use_responses_api=False,
                       extra_body={"thinking": {"type": "disabled"}} if model_name.startswith("deepseek-") else {})
    try:
        response = await model.ainvoke("Reply with exactly S01_OK.")
        result["checks"].append({"name": "text", "passed": "S01_OK" in response.text})
        result["usage"].append(response.usage_metadata)
        text = ""
        async for chunk in model.astream("Reply with exactly STREAM_OK."):
            text += chunk.text
        result["checks"].append({"name": "stream", "passed": "STREAM_OK" in text})
        agent = create_agent(model, response_format=ToolStrategy(SmokeReport, handle_errors=False),
                             middleware=[ModelCallLimitMiddleware(run_limit=2, exit_behavior="error")])
        structured = await agent.ainvoke({"messages": [("user", "Return marker=STRUCTURED_OK using the schema.")]})
        result["checks"].append({"name": "create_agent_structured_tool_strategy",
                                  "passed": structured["structured_response"].marker == "STRUCTURED_OK"})
        result["usage"].extend(m.usage_metadata for m in structured["messages"]
                               if getattr(m, "usage_metadata", None))
        result["status"] = "passed" if all(c["passed"] for c in result["checks"]) else "failed_expectation"
    except Exception as error:
        result["status"] = "failed_external_provider"
        result["error_type"] = type(error).__name__
        result["http_status"] = getattr(error, "status_code", None)
    finally:
        await model.root_async_client.close()
        model.root_client.close()
        result["finished_at"] = datetime.now(timezone.utc).isoformat()
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ["usage"]}, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
