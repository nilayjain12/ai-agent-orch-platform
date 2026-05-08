from fastapi.testclient import TestClient
from app.main import app
from app.db.database import get_db, Base, engine
from sqlalchemy.orm import sessionmaker
import pytest

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

def test_create_agent():
    response = client.post(
        "/api/agents/",
        json={
            "name": "Weather Agent",
            "description": "An agent that can check the weather",
            "role": "Weather Specialist",
            "system_prompt": "You are a weather specialist.",
            "tools": ["weather"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Weather Agent"
    assert "weather" in data["tools"]
    return data["id"]

def test_get_agents():
    response = client.get("/api/agents/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert any(a["name"] == "Weather Agent" for a in data)

def test_create_workflow():
    # First create an agent to use in the workflow
    agent_id = test_create_agent()
    
    response = client.post(
        "/api/workflows/",
        json={
            "name": "Weather Workflow",
            "description": "A workflow to check weather",
            "nodes": [
                {
                    "id": "agent_1",
                    "type": "agent",
                    "data": {"agent_id": agent_id}
                }
            ],
            "edges": []
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Weather Workflow"
    return data["id"]

def test_execute_workflow():
    workflow_id = test_create_workflow()
    
    response = client.post(
        f"/api/workflows/{workflow_id}/execute",
        params={"input_message": "What is the weather in London?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "started"
    assert "execution_id" in data
    return data["execution_id"]

def test_monitoring():
    execution_id = test_execute_workflow()
    
    # Check status
    response = client.get(f"/api/executions/{execution_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == execution_id
    assert data["status"] in ["running", "completed", "failed"]

    # Check recent executions
    response = client.get("/api/executions/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert any(e["id"] == execution_id for e in data)

def test_delete_workflow():
    workflow_id = test_create_workflow()
    
    response = client.delete(f"/api/workflows/{workflow_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"
    
    # Verify it's no longer in active workflows
    response = client.get("/api/workflows/")
    assert response.status_code == 200
    data = response.json()
    assert not any(w["id"] == workflow_id for w in data)

def test_clear_executions():
    response = client.delete("/api/executions/")
    assert response.status_code == 200
    assert response.json()["message"] == "All executions cleared"
    
    response = client.get("/api/executions/")
    assert response.status_code == 200
    assert len(response.json()) == 0
