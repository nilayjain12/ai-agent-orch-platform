"""
Extended API tests — covers 404 paths, CRUD edge cases, WebSocket, and run_workflow_bg error handling.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app, manager
from app.db.database import get_db, Base, engine
from sqlalchemy.orm import sessionmaker

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# ── Root ─────────────────────────────────────────────────────

def test_root_health():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["message"] == "AI Agent Orchestration Platform API"


# ── Agent 404s ───────────────────────────────────────────────

def test_get_agent_not_found():
    assert client.get("/api/agents/99999").status_code == 404


def test_update_agent_not_found():
    payload = {"name": "X", "description": "X", "role": "X", "system_prompt": "X"}
    assert client.put("/api/agents/99999", json=payload).status_code == 404


def test_delete_agent_not_found():
    assert client.delete("/api/agents/99999").status_code == 404


# ── Agent full lifecycle ─────────────────────────────────────

def test_agent_get_update_delete():
    # Create
    res = client.post("/api/agents/", json={
        "name": "Lifecycle Agent", "description": "D", "role": "R", "system_prompt": "P"
    })
    assert res.status_code == 200
    agent_id = res.json()["id"]

    # Get by ID
    res = client.get(f"/api/agents/{agent_id}")
    assert res.status_code == 200
    assert res.json()["name"] == "Lifecycle Agent"

    # Update
    res = client.put(f"/api/agents/{agent_id}", json={
        "name": "Updated Agent", "description": "D2", "role": "R2", "system_prompt": "P2"
    })
    assert res.status_code == 200
    assert res.json()["name"] == "Updated Agent"

    # Delete (soft)
    res = client.delete(f"/api/agents/{agent_id}")
    assert res.status_code == 200
    assert res.json()["status"] == "deleted"


# ── Workflow 404s ────────────────────────────────────────────

def test_execute_workflow_not_found():
    assert client.post("/api/workflows/99999/execute", params={"input_message": "hi"}).status_code == 404


def test_delete_workflow_not_found():
    assert client.delete("/api/workflows/99999").status_code == 404


# ── Monitoring 404 ───────────────────────────────────────────

def test_execution_not_found():
    assert client.get("/api/executions/99999").status_code == 404


# ── WebSocket ────────────────────────────────────────────────

def test_websocket_connect_disconnect():
    with client.websocket_connect("/ws/logs") as ws:
        assert len(manager.active_connections) >= 1
        ws.send_text("ping")
    # After context exit, connection is closed
    assert len(manager.active_connections) == 0


# ── run_workflow_bg error path ───────────────────────────────

def test_run_workflow_bg_invalid_ids():
    """Calling with non-existent IDs should not raise — it catches exceptions internally."""
    from app.api.workflows import run_workflow_bg
    # Should not raise
    run_workflow_bg(99999, 99999, "test")
