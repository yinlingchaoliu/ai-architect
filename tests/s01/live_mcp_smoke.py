"""Bounded real provider -> create_agent -> local HTTP MCP verification."""
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from urllib.parse import urlparse

import httpx
from dotenv import dotenv_values
from langchain_core.messages import ToolMessage
from langchain_openai import ChatOpenAI

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from agentmcp.agentmcp import run_query

OUT = ROOT / "docs/task/01-langchain-upgrade/run-01/evidence/live-mcp-model.json"


async def main():
    values = {**{k: v for k, v in dotenv_values(ROOT / ".env").items() if v},
              **{k: v for k, v in dotenv_values(ROOT / ".env.local").items() if v}, **os.environ}
    model_name = values.get("OPENAI_MODEL", "deepseek-flash")
    base = values.get("OPENAI_BASE_URL")
    receipt = {"started_at": datetime.now(timezone.utc).isoformat(), "model": model_name,
               "provider_host": urlparse(base).hostname if base else "api.openai.com",
               "transport": "chat_completions -> local Streamable HTTP MCP", "usage": []}
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    process = subprocess.Popen([sys.executable, "-m", "mcp_server_math.main"], cwd=ROOT,
        env={**os.environ, "MCP_HOST": "127.0.0.1", "MCP_PORT": str(port), "MCP_TRANSPORT": "http"},
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    model = ChatOpenAI(model=model_name, api_key=values["OPENAI_API_KEY"], base_url=base,
        max_tokens=128, max_retries=0, timeout=30, temperature=0, use_responses_api=False,
        extra_body={"thinking": {"type": "disabled"}} if model_name.startswith("deepseek-") else {})
    try:
        url = f"http://127.0.0.1:{port}/mcp"
        async with httpx.AsyncClient() as client:
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError("local_mcp_exited")
                try:
                    if (await client.get(url, timeout=0.3)).status_code in (200, 400, 405, 406):
                        break
                except httpx.HTTPError:
                    pass
                await asyncio.sleep(0.1)
            else:
                raise TimeoutError("local_mcp_startup")
        result = await asyncio.wait_for(run_query(
            "必须调用 calculator 工具计算 (17+25)*2，并据工具结果简短回答。", target=url, model=model), 60)
        tools = [m for m in result["messages"] if isinstance(m, ToolMessage)]
        receipt["tool_result_verified"] = any(m.name == "calculator" and "84" in str(m.content) for m in tools)
        receipt["final_answer_verified"] = "84" in result["messages"][-1].text
        receipt["usage"] = [m.usage_metadata for m in result["messages"] if getattr(m, "usage_metadata", None)]
        receipt["status"] = "passed" if receipt["tool_result_verified"] and receipt["final_answer_verified"] else "failed_expectation"
    except Exception as error:
        receipt.update(status="failed", error_type=type(error).__name__, http_status=getattr(error, "status_code", None))
    finally:
        await model.root_async_client.close()
        model.root_client.close()
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        receipt["local_server_stopped"] = process.poll() is not None
        receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
        OUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in receipt.items() if k != "usage"}, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
