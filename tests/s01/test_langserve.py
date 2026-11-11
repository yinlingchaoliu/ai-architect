"""Run only in the separately locked LangServe environment."""
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import FakeListChatModel

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def client(monkeypatch):
    import langchain_openai
    monkeypatch.setattr(langchain_openai, "ChatOpenAI", lambda **kwargs: FakeListChatModel(responses=["model result"]))
    sys.path.insert(0, str(ROOT / "server"))
    from app.server import app
    with TestClient(app) as client:
        yield client


def test_registered_routes_health_and_schema(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert len(response.json()["registered_routes"]) == 4
    assert client.get("/openai/input_schema").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_openai_chain_invoke_and_stream(client):
    response = client.post("/openai/invoke", json={"input": "hello"})
    assert response.status_code == 200
    assert response.json()["output"]["content"] == "model result"
    response = client.post("/openai/stream", json={"input": "hello"})
    assert response.status_code == 200
    assert "event: data" in response.text
    chunks = [json.loads(line[6:]) for line in response.text.splitlines()
              if line.startswith("data: ") and line[6:].strip()]
    assert "".join(chunk.get("content", "") for chunk in chunks) == "model result"


def test_prompt_and_demo_compatibility(client):
    response = client.post("/openai_ext/invoke", json={"input": {"topic": "test"}})
    assert response.status_code == 200
    response = client.post("/post_demo/invoke", json={"input": json.dumps({"input": "sample", "name": "test"})})
    assert response.status_code == 200
    assert response.json()["output"]["input"] == "sample"
    response = client.get("/get_demo/invoke", params={"input": "sample", "name": "test"})
    assert response.status_code == 200
    assert response.json()["input"] == "sample"
