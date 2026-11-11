"""Deterministic models and isolated local services; no external API in this suite."""
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

import httpx
import pytest
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


class ToolModel(FakeMessagesListChatModel):
    def bind_tools(self, tools, *, tool_choice=None, **kwargs):
        return self


@pytest.fixture
def model_factory():
    return lambda responses: ToolModel(responses=responses)


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "s01-offline-test-key")
    monkeypatch.setenv("AI_ARCHITECT_LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "false")


@pytest.fixture
def math_server(tmp_path):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    env = {**os.environ, "MCP_PORT": str(port), "MCP_HOST": "127.0.0.1",
           "MCP_TRANSPORT": "http", "PYTHONPATH": str(ROOT)}
    logfile = tmp_path / "math-server.log"
    with logfile.open("w") as log:
        process = subprocess.Popen([sys.executable, "-m", "mcp_server_math.main"],
                                   cwd=ROOT, env=env, stdout=log, stderr=log)
        url = f"http://127.0.0.1:{port}/mcp"
        try:
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    pytest.fail(logfile.read_text()[-3000:])
                try:
                    if httpx.get(url, timeout=0.5).status_code in (200, 400, 405, 406):
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(0.05)
            else:
                pytest.fail("MCP HTTP server did not become ready")
            yield url
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            assert process.poll() is not None
