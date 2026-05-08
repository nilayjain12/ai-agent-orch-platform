from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Agent
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/agents", tags=["Agents"])

class AgentCreate(BaseModel):
    name: str
    description: str
    role: str
    system_prompt: str
    model_name: Optional[str] = "llama-3.1-8b-instant"
    temperature: Optional[str] = "0.7"
    tools: Optional[List[str]] = []
    memory_enabled: Optional[bool] = True
    memory_config: Optional[dict] = {}
    channels: Optional[List[str]] = []
    schedule: Optional[str] = None
    interaction_rules: Optional[str] = None
    guardrails: Optional[str] = None

class AgentResponse(AgentCreate):
    id: int
    active: bool

    class Config:
        from_attributes = True

@router.post("/", response_model=AgentResponse)
def create_agent(agent: AgentCreate, db: Session = Depends(get_db)):
    db_agent = Agent(**agent.model_dump())
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent

@router.get("/", response_model=List[AgentResponse])
def get_agents(db: Session = Depends(get_db)):
    return db.query(Agent).filter(Agent.active == True).all()

@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(agent_id: int, db: Session = Depends(get_db)):
    db_agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return db_agent

@router.put("/{agent_id}", response_model=AgentResponse)
def update_agent(agent_id: int, agent: AgentCreate, db: Session = Depends(get_db)):
    db_agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    for key, value in agent.model_dump().items():
        setattr(db_agent, key, value)
        
    db.commit()
    db.refresh(db_agent)
    return db_agent

@router.delete("/{agent_id}")
def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    db_agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    db_agent.active = False
    db.commit()
    return {"status": "deleted"}
