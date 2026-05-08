from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.database import get_db, SessionLocal
from app.db.models import Workflow, Execution, Agent, LogEntry
from app.core.runtime import compile_workflow
from langchain_core.messages import HumanMessage
import json
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/workflows", tags=["Workflows"])

class WorkflowCreate(BaseModel):
    name: str
    description: str
    nodes: list = []
    edges: list = []

class WorkflowResponse(WorkflowCreate):
    id: int
    active: bool

    class Config:
        from_attributes = True

@router.post("/", response_model=WorkflowResponse)
def create_workflow(workflow: WorkflowCreate, db: Session = Depends(get_db)):
    db_workflow = Workflow(**workflow.model_dump())
    db.add(db_workflow)
    db.commit()
    db.refresh(db_workflow)
    return db_workflow

@router.get("/", response_model=List[WorkflowResponse])
def get_workflows(db: Session = Depends(get_db)):
    return db.query(Workflow).filter(Workflow.active == True).all()

def run_workflow_bg(workflow_id: int, execution_id: int, input_message: str):
    db = SessionLocal()
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        execution = db.query(Execution).filter(Execution.id == execution_id).first()
        
        # Get all agents required by this workflow
        agent_ids = [n["data"]["agent_id"] for n in workflow.nodes if n.get("type") == "agent"]
        agents = db.query(Agent).filter(Agent.id.in_(agent_ids)).all()
        
        graph = compile_workflow(workflow, agents)
        
        # Initial state
        initial_state = {
            "messages": [HumanMessage(content=input_message)],
            "sender": "user",
            "context": {}
        }
        
        # Stream graph execution
        full_state = initial_state
        for chunk in graph.stream(initial_state, stream_mode="updates"):
            for node_id, update in chunk.items():
                # Update full state history
                if "messages" in update:
                    full_state["messages"] = list(full_state["messages"]) + list(update["messages"])
                if "sender" in update:
                    full_state["sender"] = update["sender"]
                if "context" in update:
                    full_state["context"].update(update["context"])

                # Determine friendly name for node
                friendly_name = node_id
                if node_id == "tools":
                    friendly_name = "Tools"
                else:
                    node_data = next((n for n in workflow.nodes if n["id"] == node_id), None)
                    if node_data and node_data.get("type") == "agent":
                        agent_id = node_data["data"].get("agent_id")
                        agent = next((a for a in agents if a.id == agent_id), None)
                        if agent:
                            friendly_name = agent.name

                # Log ALL new messages in this chunk, avoiding duplicates
                if "messages" in update and update["messages"]:
                    for msg in update["messages"]:
                        msg_content = msg.content if hasattr(msg, "content") else str(msg)
                        # Handle empty content (e.g. tool calls)
                        if not msg_content and hasattr(msg, "tool_calls") and msg.tool_calls:
                            msg_content = f"Calling tools: {', '.join([tc['name'] for tc in msg.tool_calls])}"
                        
                        if msg_content:
                            # Simple check to avoid logging the exact same content twice for this node
                            # We check the last few logs for this execution
                            prefix = f"[{friendly_name}]"
                            full_msg = f"{prefix} {msg_content[:1000]}..." if len(msg_content) > 1000 else f"{prefix} {msg_content}"
                            
                            exists = db.query(LogEntry).filter(
                                LogEntry.execution_id == execution_id,
                                LogEntry.message == full_msg
                            ).first()
                            
                            if not exists:
                                log = LogEntry(
                                    execution_id=execution_id,
                                    level="info",
                                    message=full_msg
                                )
                                db.add(log)
                                db.commit()

        # Save result
        execution.status = "completed"
        final_msg = ""
        
        # Extract the last meaningful content (skipping pure tool calls)
        for msg in reversed(full_state["messages"]):
            content = msg.content if hasattr(msg, "content") else str(msg)
            is_tool_call = hasattr(msg, "tool_calls") and msg.tool_calls
            if content.strip() and not (is_tool_call and len(content.strip()) < 5):
                final_msg = content
                break
                
        if not final_msg and full_state["messages"]:
            last_msg = full_state["messages"][-1]
            final_msg = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
        
        execution.result = {"output": final_msg}
        db.commit()
    except Exception as e:
        execution = db.query(Execution).filter(Execution.id == execution_id).first()
        if execution:
            execution.status = "failed"
            execution.result = {"error": str(e)}
            db.commit()
    finally:
        db.close()

@router.post("/{workflow_id}/execute")
async def execute_workflow(workflow_id: int, background_tasks: BackgroundTasks, input_message: str = "Hello", db: Session = Depends(get_db)):
    db_workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not db_workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Create execution record
    execution = Execution(workflow_id=workflow_id, status="running")
    db.add(execution)
    db.commit()
    db.refresh(execution)
    
    background_tasks.add_task(run_workflow_bg, workflow_id, execution.id, input_message)
    
    return {"status": "started", "execution_id": execution.id}

@router.delete("/{workflow_id}")
def delete_workflow(workflow_id: int, db: Session = Depends(get_db)):
    db_workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not db_workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    db_workflow.active = False
    db.commit()
    return {"status": "deleted"}
