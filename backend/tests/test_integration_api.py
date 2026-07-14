import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.session import Base, get_db, engine as app_engine
from app.services.ai_gateway.base import CompletionResponse


@pytest.fixture(scope="module")
def test_db():
    # Use the application's DB engine (falls back to SQLite in-memory if Postgres unavailable)
    Base.metadata.create_all(bind=app_engine)

    def _get_db():
        # Create a new session from the app's SessionLocal (the module defines it)
        from app.database.session import SessionLocal

        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Override dependency
    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def client(test_db):
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert "name" in data and "version" in data


def test_agent_crud_and_chat(client, monkeypatch):
    # Create an agent
    project_id = str(uuid.uuid4())
    payload = {"project_id": project_id, "name": "test-agent", "system_prompt": "You are helpful", "model": "gpt-4o"}
    r = client.post("/api/v1/agents/", json=payload)
    assert r.status_code == 200
    agent = r.json()
    agent_id = agent["id"]

    # List agents
    r = client.get(f"/api/v1/agents/?project_id={project_id}")
    assert r.status_code == 200
    lst = r.json()
    assert any(a["id"] == agent_id for a in lst)

    # Get agent
    r = client.get(f"/api/v1/agents/{agent_id}")
    assert r.status_code == 200

    # Mock AgentRuntime.run to avoid external LLM calls
    async def fake_run(self, user_input: str):
        return {"response": "Hello from agent", "iterations": 1, "messages": 2}

    monkeypatch.setattr("app.agents.runtime.AgentRuntime.run", fake_run)

    chat_payload = {"user_id": str(uuid.uuid4()), "message": "Hi there", "use_memory": False}
    r = client.post(f"/api/v1/agents/{agent_id}/chat", json=chat_payload)
    assert r.status_code == 200
    data = r.json()
    assert "response" in data and data["response"] == "Hello from agent"


def test_gateway_models_and_chat(client, monkeypatch):
    # Mock ProviderFactory to return a fake provider
    class FakeProvider:
        def list_models(self):
            return ["fake-model"]

        async def complete(self, messages, model, temperature=0.7, max_tokens=2048, **kwargs):
            return CompletionResponse(
                content="hi",
                model=model,
                provider="fake",
                prompt_tokens=1,
                completion_tokens=1,
                total_tokens=2,
            )

        async def stream(self, *args, **kwargs):
            if False:
                yield ""

    monkeypatch.setattr("app.services.ai_gateway.gateway.ProviderFactory.get", lambda name: FakeProvider())
    monkeypatch.setattr("app.services.ai_gateway.gateway.ProviderFactory.resolve_provider", lambda model: "fake")

    # List models
    r = client.get("/api/v1/gateway/models")
    assert r.status_code == 200

    # Chat
    payload = {"messages": [{"role": "user", "content": "Hello"}], "model": "fake-model"}
    r = client.post("/api/v1/gateway/chat", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data.get("provider") in ("fake", None) or "content" in data
